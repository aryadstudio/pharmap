import json
from django.shortcuts import render
from django.core.serializers.json import DjangoJSONEncoder
from pharmacies.models import Pharmacy
from medications.models import Medication
from django.db.models import Count


def home(request):
    featured_pharmacies = Pharmacy.objects.filter(
        is_verified=True
    ).order_by('-average_rating')[:3]

    popular_medications = Medication.objects.annotate(
        stock_count=Count('pharmacy_stocks')
    ).filter(
        pharmacy_stocks__is_available=True
    ).distinct().order_by('-stock_count')[:6]

    total_pharmacies  = Pharmacy.objects.filter(is_verified=True).count()
    nearby_pharmacies = Pharmacy.objects.filter(is_verified=True).order_by('-created_at')[:3]

    cards_tab = [
        ("linear-gradient(135deg,var(--navy-pale),var(--navy-tint))",
         "Pharmacie Centrale", "Boulevard Triomphal, Libreville", 4.8),
        ("linear-gradient(135deg,var(--green-pale),var(--green-tint))",
         "Pharmacie de la Paix", "Quartier Montagne Sainte, Libreville", 4.6),
        ("linear-gradient(135deg,var(--gold-pale),#F5E8C0)",
         "Pharmacie du Carrefour", "Owendo – face marché", 4.5),
    ]

    # ── Marqueurs carte hero ──────────────────────────────────────
    _FALLBACK_MARKERS = [
        {"lat": 0.3924, "lng": 9.4536, "name": "Pharmacie Centrale",   "color": "#0C1F3F"},
        {"lat": 0.4012, "lng": 9.4612, "name": "Pharmacie de la Paix", "color": "#1A7A5E"},
        {"lat": 0.3845, "lng": 9.4445, "name": "Pharmacie du Port",    "color": "#B8841C"},
    ]

    map_markers = []
    for p in nearby_pharmacies:
        try:
            map_markers.append({
                "lat":   float(p.latitude),
                "lng":   float(p.longitude),
                "name":  p.name,
                "color": "#0C1F3F",
            })
        except (AttributeError, TypeError, ValueError):
            pass

    if not map_markers:
        map_markers = _FALLBACK_MARKERS

    # Centre par défaut : Libreville
    map_center = [0.3924, 9.4536]

    context = {
        'featured_pharmacies':  featured_pharmacies,
        'popular_medications':  popular_medications,
        'nearby_pharmacies':    nearby_pharmacies,
        'total_pharmacies':     total_pharmacies or 120,
        'cards_tab':            cards_tab,
        # ↓ tout en JSON — pas de liste Python brute dans les templates
        'map_center_json':      json.dumps(map_center, cls=DjangoJSONEncoder),
        'map_zoom':             13,
        'map_markers_json':     json.dumps(map_markers, cls=DjangoJSONEncoder),
    }
    return render(request, 'core/home.html', context)


def how_it_works(request):
    context = {
        'total_pharmacies':  Pharmacy.objects.filter(is_verified=True).count() or 120,
        'total_medications': Medication.objects.count() or 3500,
    }
    return render(request, 'core/how_it_works.html', context)