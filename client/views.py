import uuid
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import update_session_auth_hash
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.db import transaction, models
from django.db.models import Q, Sum, Avg, Count

# Imports de vos modèles
from client.forms import PatientProfileForm, PatientPasswordChangeForm
from auth_user.models import User
from pharmacies.models import Pharmacy
from medications.models import Medication,PharmacyMedication
from .models import Cart, CartItem

# Import conditionnel pour Order (évite les erreurs si le module n'existe pas encore)
try:
    from orders.models import Order
    ORDER_MODEL_EXISTS = True
except ImportError:
    ORDER_MODEL_EXISTS = False


# ──────────────────────────────────────────────────────────────────
# VUES PROFIL
# ──────────────────────────────────────────────────────────────────

@login_required
def profile(request):
    if request.user.role != 'PATIENT':
        return redirect('auth_user:login')
    
    orders = []
    if ORDER_MODEL_EXISTS:
        orders = Order.objects.filter(patient=request.user).order_by('-created_at')
    
    context = {
        "user": request.user,
        "orders": orders,
    }
    return render(request, "client/profile.html", context)


@login_required
def profile_edit(request):
    if request.user.role != 'PATIENT':
        return redirect('auth_user:login')

    if request.method == 'POST':
        form = PatientProfileForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Profil mis à jour avec succès.")
            return redirect('patient:profile')
    else:
        form = PatientProfileForm(instance=request.user)

    return render(request, "client/profile_edit.html", {"form": form})


@login_required
def profile_change_password(request):
    if request.user.role != 'PATIENT':
        return redirect('auth_user:login')

    if request.method == 'POST':
        form = PatientPasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            messages.success(request, "Mot de passe changé avec succès.")
            return redirect('patient:profile')
    else:
        form = PatientPasswordChangeForm(request.user)

    return render(request, "client/profile_password.html", {"form": form})


@login_required
def profile_orders(request):
    if not ORDER_MODEL_EXISTS:
        messages.warning(request, "Le système de commande n'est pas encore activé.")
        return redirect('patient:profile')
        
    orders = Order.objects.filter(patient=request.user).order_by('-created_at')
    return render(request, "client/profile_orders.html", {"orders": orders})


# ──────────────────────────────────────────────────────────────────
# VUES PANIER (Gestion Multi-Pharmacies)
# ──────────────────────────────────────────────────────────────────

@login_required
def cart_view(request):
    """
    Affiche le panier du patient.
    Gère nativement les articles de différentes pharmacies.
    Le template se chargera de les regrouper visuellement.
    """
    if request.user.role != 'PATIENT':
        messages.error(request, "Seuls les patients peuvent avoir un panier.")
        return redirect('home')

    try:
        cart = Cart.objects.get(patient=request.user)
        # Optimisation : on récupère les médicaments et les pharmacies liés en une seule requête
        items = cart.items.select_related('medication', 'pharmacy').order_by('pharmacy__name', '-added_at')
    except Cart.DoesNotExist:
        cart = None
        items = []

    context = {
        "cart": cart,
        "items": items,
        "total_amount": cart.get_total_amount() if cart else 0,
        "item_count": cart.get_item_count() if cart else 0,
    }
    return render(request, "client/cart.html", context)


@require_http_methods(["POST"])
@login_required
@transaction.atomic
def cart_add(request):
    """Ajoute un article au panier (AJAX)."""
    try:
        medication_id = request.POST.get('medication_id')
        pharmacy_id = request.POST.get('pharmacy_id')
        quantity = int(request.POST.get('quantity', 1))

        if not medication_id or not pharmacy_id:
            return JsonResponse({'success': False, 'error': 'Données invalides'}, status=400)

        medication = Medication.objects.get(id=medication_id)
        pharmacy = Pharmacy.objects.get(id=pharmacy_id)
        
        # Vérifier le stock et le prix
        stock = PharmacyMedication.objects.get(
            medication=medication,
            pharmacy=pharmacy,
            quantity__gt=0,
            is_available=True
        )

        # Récupérer ou créer le panier (un seul panier par patient, peu importe la pharmacie)
        cart, _ = Cart.objects.get_or_create(patient=request.user)

        # Vérifier si l'article existe déjà DANS CETTE PHARMACIE
        existing_item = CartItem.objects.filter(
            cart=cart,
            medication=medication,
            pharmacy=pharmacy
        ).first()

        if existing_item:
            new_quantity = existing_item.quantity + quantity
            if new_quantity > stock.quantity:
                return JsonResponse({
                    'success': False, 
                    'error': f'Stock insuffisant. Maximum {stock.quantity} disponible.'
                }, status=400)
            
            existing_item.quantity = new_quantity
            existing_item.unit_price = stock.price
            existing_item.save()
            item = existing_item
            action = 'updated'
        else:
            if quantity > stock.quantity:
                return JsonResponse({
                    'success': False, 
                    'error': f'Stock insuffisant. Maximum {stock.quantity} disponible.'
                }, status=400)
            
            item = CartItem.objects.create(
                cart=cart,
                medication=medication,
                pharmacy=pharmacy,
                quantity=quantity,
                unit_price=stock.price
            )
            action = 'created'

        return JsonResponse({
            'success': True,
            'action': action,
            'item_count': cart.get_item_count(),
            'total_amount': str(cart.get_total_amount()),
            'item': {
                'id': str(item.id),
                'medication_name': item.medication.name,
                'pharmacy_name': item.pharmacy.name,
                'quantity': item.quantity,
                'unit_price': str(item.unit_price),
                'subtotal': str(item.subtotal),
            }
        })

    except Medication.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Médicament introuvable'}, status=404)
    except Pharmacy.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Pharmacie introuvable'}, status=404)
    except PharmacyMedication.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Produit non disponible en stock'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@require_http_methods(["POST"])
@login_required
@transaction.atomic
def cart_update(request, item_id):
    """Met à jour la quantité d'un article ou le supprime (AJAX)."""
    try:
        # On vérifie que l'article appartient bien au panier du patient connecté
        item = CartItem.objects.get(id=item_id, cart__patient=request.user)
    except CartItem.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Article non trouvé'}, status=404)

    action_type = request.POST.get('action', 'update')

    if action_type == 'remove':
        cart = item.cart
        item.delete()
        return JsonResponse({
            'success': True,
            'action': 'removed',
            'item_count': cart.get_item_count(),
            'total_amount': str(cart.get_total_amount()),
        })

    # Mise à jour de quantité
    try:
        quantity = int(request.POST.get('quantity', item.quantity))
        if quantity < 1:
            raise ValueError("Quantité invalide")
    except ValueError:
        return JsonResponse({'success': False, 'error': 'Quantité invalide'}, status=400)

    # Vérifier le stock actuel dans la pharmacie concernée
    try:
        stock = PharmacyMedication.objects.get(
            medication=item.medication,
            pharmacy=item.pharmacy,
            is_available=True
        )
        if quantity > stock.quantity:
            return JsonResponse({
                'success': False, 
                'error': f'Stock insuffisant. Maximum {stock.quantity} disponible.'
            }, status=400)
    except PharmacyMedication.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Produit plus disponible'}, status=400)

    item.quantity = quantity
    item.save()

    return JsonResponse({
        'success': True,
        'action': 'updated',
        'item_count': item.cart.get_item_count(),
        'total_amount': str(item.cart.get_total_amount()),
        'item': {
            'id': str(item.id),
            'quantity': item.quantity,
            'subtotal': str(item.subtotal),
        }
    })


@require_http_methods(["POST"])
@login_required
@transaction.atomic
def cart_clear(request):
    """Vide le panier entièrement."""
    try:
        cart = Cart.objects.get(patient=request.user)
        cart.clear()
        return JsonResponse({'success': True, 'message': 'Panier vidé'})
    except Cart.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Panier non trouvé'}, status=404)