import json
from django.shortcuts import render
from django.core.serializers.json import DjangoJSONEncoder
from django.db.models import Count, Q

from pharmacies.models import Pharmacy
from medications.models import Medication


def home(request):
    # 1. Pharmacies en vedette (Top 3 par note)
    featured_pharmacies = Pharmacy.objects.filter(
        is_verified=True
    ).order_by('-average_rating')[:3]

    # 2. Médicaments populaires (Ceux qui ont le plus de stocks disponibles)
    popular_medications = Medication.objects.annotate(
        stock_count=Count('pharmacy_stocks')
    ).filter(
        pharmacy_stocks__is_available=True,
        pharmacy_stocks__quantity__gt=0
    ).distinct().order_by('-stock_count')[:6]

    # 3. Statistiques globales
    total_pharmacies = Pharmacy.objects.filter(is_verified=True).count()
    
    # 4. Pharmacies récentes (pour la carte et la liste "à proximité" démo)
    nearby_pharmacies = Pharmacy.objects.filter(
        is_verified=True
    ).order_by('-created_at')[:3]

    # Données de fallback pour la démo si la DB est vide
    cards_tab = [
        ("linear-gradient(135deg,var(--navy-pale),var(--navy-tint))",
         "Pharmacie Centrale", "Boulevard Triomphal, Libreville", 4.8),
        ("linear-gradient(135deg,var(--green-pale),var(--green-tint))",
         "Pharmacie de la Paix", "Quartier Montagne Sainte, Libreville", 4.6),
        ("linear-gradient(135deg,var(--gold-pale),#F5E8C0)",
         "Pharmacie du Carrefour", "Owendo – face marché", 4.5),
    ]

    # ── Préparation des marqueurs pour la carte Hero ──────────────
    _FALLBACK_MARKERS = [
        {"lat": 0.3924, "lng": 9.4536, "name": "Pharmacie Centrale",   "color": "#0C1F3F"},
        {"lat": 0.4012, "lng": 9.4612, "name": "Pharmacie de la Paix", "color": "#1A7A5E"},
        {"lat": 0.3845, "lng": 9.4445, "name": "Pharmacie du Port",    "color": "#B8841C"},
    ]

    map_markers = []
    for p in nearby_pharmacies:
        try:
            # On s'assure que les coordonnées sont valides avant d'ajouter
            if p.latitude and p.longitude:
                map_markers.append({
                    "lat":   float(p.latitude),
                    "lng":   float(p.longitude),
                    "name":  p.name,
                    "color": "#0C1F3F" if p.is_verified else "#718096",
                })
        except (AttributeError, TypeError, ValueError):
            continue

    # Si aucune pharmacie réelle n'a de coordonnées, on utilise la démo
    if not map_markers:
        map_markers = _FALLBACK_MARKERS

    # Centre par défaut : Libreville
    map_center = [0.3924, 9.4536]
    
    # Si on a des pharmacies, on centre sur la première (optionnel)
    if nearby_pharmacies.exists() and nearby_pharmacies.first().latitude:
        map_center = [nearby_pharmacies.first().latitude, nearby_pharmacies.first().longitude]

    context = {
        'featured_pharmacies':  featured_pharmacies,
        'popular_medications':  popular_medications,
        'nearby_pharmacies':    nearby_pharmacies,
        'total_pharmacies':     total_pharmacies if total_pharmacies > 0 else 120,
        'cards_tab':            cards_tab,
        
        # Sérialisation JSON sûre pour Leaflet
        'map_center_json':      json.dumps(map_center, cls=DjangoJSONEncoder),
        'map_zoom':             13,
        'map_markers_json':     json.dumps(map_markers, cls=DjangoJSONEncoder),
    }
    
    return render(request, 'core/home.html', context)


def how_it_works(request):
    """Page expliquant le fonctionnement de PharMap."""
    context = {
        'total_pharmacies':  Pharmacy.objects.filter(is_verified=True).count() or 120,
        'total_medications': Medication.objects.count() or 3500,
    }
    return render(request, 'core/how_it_works.html', context)