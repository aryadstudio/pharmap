from django.shortcuts import render, get_object_or_404,redirect
from django.http import JsonResponse
from django.db.models import FloatField, ExpressionWrapper, Min, Q, F
from django.db.models.functions import ACos, Cos, Sin, Radians, Greatest, Least
import math
import json
from django.core.serializers.json import DjangoJSONEncoder
from django.urls import reverse
from urllib.parse import quote

from pharmacies.models import Pharmacy
from medications.models import (
    Medication,
    PharmacyMedication as Stock,
    MedicationCategory as Category,
)
from django.contrib import messages
from reviews.models import PharmacyReview


EARTH_RADIUS_KM = 6371

DEFAULT_CATEGORIES = [
    ('antibiotiques',       'Antibiotiques'),
    ('antalgiques',         'Antalgiques'),
    ('antipaludeens',       'Antipaludéens'),
    ('anti-inflammatoires', 'Anti-inflammatoires'),
    ('cardiologie',         'Cardiologie'),
    ('diabete',             'Diabète'),
    ('gastro',              'Gastro-intestinal'),
    ('dermatologie',        'Dermatologie'),
]


# ──────────────────────────────────────────────────────────────────
# Helpers géographiques
# ──────────────────────────────────────────────────────────────────

def _haversine_expr(lat, lng):
    """
    Distance Haversine (km) calculée en SQL.
    On borne la valeur dans [-1, 1] avec Least/Greatest
    pour éviter que ACos explose sur des coordonnées très proches.
    """
    inner = (
        Cos(Radians(lat)) * Cos(Radians(F('latitude')))
        * Cos(Radians(F('longitude')) - Radians(lng))
        + Sin(Radians(lat)) * Sin(Radians(F('latitude')))
    )
    return ExpressionWrapper(
        EARTH_RADIUS_KM * ACos(
            Least(1.0, Greatest(-1.0, inner))
        ),
        output_field=FloatField()
    )


def _bounding_box(lat, lng, radius_km):
    """Bounding box pour pré-filtrer avant Haversine."""
    delta_lat = radius_km / EARTH_RADIUS_KM * (180 / math.pi)
    delta_lng = delta_lat / math.cos(math.radians(lat))
    return (
        lat - delta_lat, lat + delta_lat,
        lng - delta_lng, lng + delta_lng,
    )


def _parse_location(request):
    """Extrait et valide lat/lng depuis les paramètres GET."""
    try:
        lat = float(request.GET.get('lat', ''))
        lng = float(request.GET.get('lng', ''))
        if not (-90 <= lat <= 90) or not (-180 <= lng <= 180):
            return None, None
        return lat, lng
    except (ValueError, TypeError):
        return None, None


# ──────────────────────────────────────────────────────────────────
# Helpers de sérialisation
# ──────────────────────────────────────────────────────────────────

def _pha_to_dict(p, user_lat=None):
    """Sérialise une pharmacie en dict JSON-safe."""
    try:
        lat = float(p.latitude) if p.latitude else None
        lng = float(p.longitude) if p.longitude else None
    except (TypeError, ValueError):
        lat = lng = None

    try:
        distance = (
            round(float(p.distance), 2)
            if (user_lat is not None and hasattr(p, 'distance') and p.distance is not None)
            else None
        )
    except (TypeError, ValueError):
        distance = None

    try:
        min_price = round(float(p.min_price), 2) if p.min_price else None
    except (TypeError, ValueError):
        min_price = None

    try:
        rating = round(float(p.average_rating), 1) if p.average_rating else 0.0
    except (TypeError, ValueError):
        rating = 0.0

    return {
        'id':          p.id,
        'name':        p.name or '',
        'address':     p.address or '',
        'city':        p.city or '',
        'phone':       p.phone or '',
        'lat':         lat,
        'lng':         lng,
        'distance':    distance,
        'min_price':   min_price,
        'is_open_24h': bool(p.is_open_24h),
        'is_verified': bool(p.is_verified),
        'rating':      rating,
        'url':         reverse('pharmacies:pharmacy_detail', args=[p.id]),
    }


def _med_to_dict(m):
    """Sérialise un médicament en dict JSON-safe."""
    return {
        'id':       m.id,
        'name':     m.name or '',
        'category': m.category.name if m.category else '',
        'rx':       bool(m.requires_prescription),
        'url':      reverse('pharmacies:search') + '?q=' + quote(m.name or ''),
    }


# ──────────────────────────────────────────────────────────────────
# pharmacy_list
# ──────────────────────────────────────────────────────────────────

def pharmacy_list(request):
    pharmacies = Pharmacy.objects.filter(is_verified=True).order_by('-average_rating')
    city = request.GET.get('city', '')
    if city:
        pharmacies = pharmacies.filter(city__icontains=city)

    map_markers = []
    for p in pharmacies:
        try:
            map_markers.append({
                'lat':   float(p.latitude),
                'lng':   float(p.longitude),
                'name':  p.name,
                'color': '#0C1F3F' if p.is_verified else '#718096',
            })
        except (AttributeError, TypeError, ValueError):
            pass

    context = {
        'pharmacies':       pharmacies,
        'cities':           Pharmacy.objects.values_list('city', flat=True).distinct(),
        'selected_city':    city,
        'total_pharmacies': Pharmacy.objects.count(),
        'map_center_json':  json.dumps([0.3924, 9.4536], cls=DjangoJSONEncoder),
        'map_zoom':         12,
        'map_markers_json': json.dumps(map_markers, cls=DjangoJSONEncoder),
    }
    return render(request, 'pharmacies/pharmacy_list.html', context)


# ──────────────────────────────────────────────────────────────────
# pharmacy_search  (HTML + AJAX)
# ──────────────────────────────────────────────────────────────────

def pharmacy_search(request):
    query    = request.GET.get('q', '').strip()
    category = request.GET.get('category', '').strip()
    radius   = max(1, min(int(request.GET.get('radius', 5) or 5), 100))
    is_ajax  = request.headers.get('X-Requested-With') == 'XMLHttpRequest'

    user_lat, user_lng = _parse_location(request)

    # ── Médicaments correspondants ────────────────────────────────
    medications = Medication.objects.select_related('category').all()
    if query:
        medications = medications.filter(
            Q(name__icontains=query)
            | Q(description__icontains=query)
            | Q(category__name__icontains=query)
        )
    if category:
        medications = medications.filter(category__slug=category)

    # Évaluer le queryset maintenant pour éviter la référence circulaire
    medication_ids = list(medications.values_list('id', flat=True))

    # ── Pharmacies ────────────────────────────────────────────────
    if query or category:
        if not medication_ids:
            pharmacies = Pharmacy.objects.none()
        else:
            pharmacies = Pharmacy.objects.filter(
                stocks__medication_id__in=medication_ids,
                stocks__quantity__gt=0,
                stocks__is_available=True,
            ).distinct()
    else:
        pharmacies = Pharmacy.objects.filter(is_verified=True)

    # ── Filtre géographique ───────────────────────────────────────
    if user_lat is not None:
        min_lat, max_lat, min_lng, max_lng = _bounding_box(user_lat, user_lng, radius)
        pharmacies = (
            pharmacies
            .filter(
                latitude__gte=min_lat,  latitude__lte=max_lat,
                longitude__gte=min_lng, longitude__lte=max_lng,
            )
            .annotate(distance=_haversine_expr(user_lat, user_lng))
            .filter(distance__lte=radius)
            .order_by('distance')
        )
    else:
        pharmacies = pharmacies.order_by('-average_rating')

    # ── Prix minimum par pharmacie ────────────────────────────────
    if medication_ids:
        pharmacies = pharmacies.annotate(
            min_price=Min(
                'stocks__price',
                filter=Q(
                    stocks__medication_id__in=medication_ids,
                    stocks__quantity__gt=0,
                    stocks__is_available=True,
                )
            )
        )
    else:
        pharmacies = pharmacies.annotate(
            min_price=Min(
                'stocks__price',
                filter=Q(
                    stocks__quantity__gt=0,
                    stocks__is_available=True,
                )
            )
        )

    # ── Réponse JSON (AJAX) ───────────────────────────────────────
    if is_ajax:
        total    = pharmacies.count()
        pha_list = list(pharmacies[:20])
        meds_list = list(medications[:6])

        return JsonResponse({
            'pharmacies':  [_pha_to_dict(p, user_lat) for p in pha_list],
            'medications': [_med_to_dict(m) for m in meds_list],
            'total':       total,
        })

    # ── Rendu HTML ────────────────────────────────────────────────
    pha_list  = list(pharmacies[:20])
    meds_list = list(medications[:6])
    all_categories = Category.objects.all()

    context = {
        'query':              query,
        'category':           category,
        'categories':         all_categories,
        'default_categories': DEFAULT_CATEGORIES,
        'medications':        meds_list,
        'pharmacies':         pha_list,
        'user_lat':           user_lat if user_lat is not None else '',
        'user_lng':           user_lng if user_lng is not None else '',
        'radius':             radius,
        'has_location':       user_lat is not None,
        # JSON sérialisé proprement côté Python — zéro risque de JSON invalide
        'pharmacies_json':    json.dumps(
            [_pha_to_dict(p, user_lat) for p in pha_list],
            cls=DjangoJSONEncoder
        ),
        'medications_json':   json.dumps(
            [_med_to_dict(m) for m in meds_list],
            cls=DjangoJSONEncoder
        ),
    }
    return render(request, 'pharmacies/pharmacy_search.html', context)


# ──────────────────────────────────────────────────────────────────
# autocomplete
# ──────────────────────────────────────────────────────────────────

def autocomplete(request):
    """Suggestions live (AJAX)."""
    q = request.GET.get('q', '').strip()
    if len(q) < 2:
        return JsonResponse({'results': []})

    meds = (
        Medication.objects
        .filter(Q(name__icontains=q) | Q(category__name__icontains=q))
        .select_related('category')
        .values(
            'id',
            'name',
            'category__name',
            'category__slug',
            'requires_prescription',
        )[:8]
    )

    return JsonResponse({'results': list(meds)})


# ──────────────────────────────────────────────────────────────────
# pharmacy_detail
# ──────────────────────────────────────────────────────────────────

def pharmacy_detail(request, pharmacy_id):
    pharmacy = get_object_or_404(Pharmacy, id=pharmacy_id)
    stocks = (
        Stock.objects
        .filter(pharmacy=pharmacy, quantity__gt=0, is_available=True)
        .select_related('medication', 'medication__category')
        .order_by('medication__name')
    )
    reviews = (
        PharmacyReview.objects
        .filter(pharmacy=pharmacy)
        .order_by('-created_at')[:5]
    )

    map_markers = []
    try:
        map_markers = [{
            'lat':   float(pharmacy.latitude),
            'lng':   float(pharmacy.longitude),
            'name':  pharmacy.name,
            'color': '#0C1F3F' if pharmacy.is_verified else '#718096',
        }]
    except (AttributeError, TypeError, ValueError):
        pass

    context = {
        'pharmacy': pharmacy,
        'stocks':   stocks,
        'reviews':  reviews,
        'sibars':   [(5, 80), (4, 12), (3, 5), (2, 2), (1, 1)],
        'sibar2':   [(5, 75), (4, 15), (3, 6), (2, 3), (1, 1)],
        'map_center_json': json.dumps(
            [float(pharmacy.latitude), float(pharmacy.longitude)]
            if pharmacy.latitude and pharmacy.longitude
            else [0.3924, 9.4536],
            cls=DjangoJSONEncoder
        ),
        'map_zoom':         15,
        'map_markers_json': json.dumps(map_markers, cls=DjangoJSONEncoder),
    }
    return render(request, 'pharmacies/pharmacy_detail.html', context)


# ──────────────────────────────────────────────────────────────────
# pharmacy_reviews
# ──────────────────────────────────────────────────────────────────
def pharmacy_reviews(request, pharmacy_id):
    pharmacy = get_object_or_404(Pharmacy, id=pharmacy_id)
    reviews  = PharmacyReview.objects.filter(pharmacy=pharmacy).select_related("patient").order_by("-created_at")

    # Distribution des notes 1→5
    total = reviews.count()
    distribution = []
    for star in range(5, 0, -1):
        count = reviews.filter(rating=star).count()
        pct   = round((count / total) * 100) if total > 0 else 0
        distribution.append({"star": star, "count": count, "pct": pct})

    # Avis existant du user connecté
    user_review = None
    if request.user.is_authenticated:
        user_review = reviews.filter(patient=request.user).first()

    # Soumission du formulaire
    if request.method == "POST":
        if not request.user.is_authenticated:
            return redirect("auth_user:login")

        if user_review:
            messages.warning(request, "Vous avez déjà laissé un avis pour cette pharmacie.")
            return redirect("pharmacies:pharmacy_reviews", pharmacy_id=pharmacy_id)

        rating  = request.POST.get("rating", 0)
        comment = request.POST.get("comment", "").strip()

        try:
            rating = int(rating)
            if not (1 <= rating <= 5):
                raise ValueError
        except ValueError:
            messages.error(request, "Veuillez sélectionner une note entre 1 et 5.")
            return redirect("pharmacies:pharmacy_reviews", pharmacy_id=pharmacy_id)

        PharmacyReview.objects.create(
            patient=request.user,
            pharmacy=pharmacy,
            rating=rating,
            comment=comment,
        )

        # Recalcul de la note moyenne sur la pharmacie
        all_reviews = PharmacyReview.objects.filter(pharmacy=pharmacy)
        pharmacy.total_reviews  = all_reviews.count()
        pharmacy.average_rating = round(sum(r.rating for r in all_reviews) / pharmacy.total_reviews, 2)
        pharmacy.save(update_fields=["average_rating", "total_reviews"])

        messages.success(request, "Votre avis a bien été publié, merci !")
        return redirect("pharmacies:pharmacy_reviews", pharmacy_id=pharmacy_id)

    context = {
        "pharmacy":     pharmacy,
        "reviews":      reviews,
        "distribution": distribution,
        "user_review":  user_review,
        "total":        total,
    }
    return render(request, "pharmacies/pharmacy_reviews.html", context)