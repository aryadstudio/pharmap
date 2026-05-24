from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum, Count
from django.db import transaction

from auth_user.models import User
from orders.models import Order
from pharmacies.models import PharmacyReview, Prescription

from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from client.models import Cart, CartItem

# ──────────────────────────────────────────────────────────────────
# Helpers internes
# ──────────────────────────────────────────────────────────────────

def _get_profile_stats(user):
    """Calcule les statistiques pour le profil utilisateur."""
    if user.role != "PATIENT":
        return {}
        
    orders = Order.objects.filter(patient=user)
    return {
        "total_orders":      orders.count(),
        "pending_orders":    orders.filter(status="PENDING").count(),
        "delivered_orders":  orders.filter(status="DELIVERED").count(),
        "cancelled_orders":  orders.filter(status="CANCELLED").count(),
        "total_reviews":     PharmacyReview.objects.filter(patient=user).count(),
        "total_prescriptions": Prescription.objects.filter(patient=user).count(),
        "total_spent":       orders.filter(status="DELIVERED").aggregate(
                                s=Sum("total_amount"))["s"] or 0,
    }

def _get_profile_context(user):
    """Construit le contexte commun à tous les onglets du profil patient."""
    if user.role != "PATIENT":
        return {}

    orders = Order.objects.filter(patient=user)
    return {
        "stats": _get_profile_stats(user),
        "recent_orders": orders.prefetch_related("items__medication").order_by("-created_at")[:5],
        "recent_reviews": PharmacyReview.objects.filter(patient=user).select_related("pharmacy").order_by("-created_at")[:3],
        "prescriptions": Prescription.objects.filter(patient=user).order_by("-created_at")[:5],
    }

# ──────────────────────────────────────────────────────────────────
# Profil patient
# ──────────────────────────────────────────────────────────────────

@login_required
def profile(request):
    """Page principale du profil patient (Vue d'ensemble)."""
    user = request.user
    
    # Redirection si ce n'est pas un patient (optionnel, selon votre logique métier)
    if user.role != "PATIENT":
        messages.info(request, "Cette page est réservée aux patients.")
        # Vous pourriez rediriger vers un dashboard pharmacien ici si nécessaire
        # return redirect('pharmacist:dashboard')

    context = _get_profile_context(user)
    context.update({
        "user": user,
        "active_tab": request.GET.get("tab", "overview"),
    })
    
    return render(request, "client/profile_patient.html", context)


@login_required
def profile_edit(request):
    """Modifier les infos personnelles."""
    user = request.user
    errors = {}
    post_data = request.POST if request.method == "POST" else None

    if request.method == "POST":
        first_name = request.POST.get("first_name", "").strip()
        last_name  = request.POST.get("last_name", "").strip()
        phone      = request.POST.get("phone", "").strip()
        email      = request.POST.get("email", "").strip()

        # Validations
        if not first_name:
            errors["first_name"] = "Le prénom est requis."
        if not last_name:
            errors["last_name"] = "Le nom est requis."
        if not phone:
            errors["phone"] = "Le téléphone est requis."
        
        if email and email != user.email:
            if User.objects.filter(email=email).exclude(pk=user.pk).exists():
                errors["email"] = "Cet email est déjà utilisé."
        
        if phone and phone != user.phone:
            if User.objects.filter(phone=phone).exclude(pk=user.pk).exists():
                errors["phone"] = "Ce numéro est déjà utilisé."

        if not errors:
            with transaction.atomic():
                user.first_name = first_name
                user.last_name  = last_name
                user.phone      = phone
                if email:
                    user.email = email

                # Photo de profil
                if "profile_picture" in request.FILES:
                    user.profile_picture = request.FILES["profile_picture"]

                user.save()
            
            messages.success(request, "Profil mis à jour avec succès.")
            return redirect("auth_user:profile")
        else:
            messages.error(request, "Veuillez corriger les erreurs ci-dessous.")

    return render(request, "client/profile_edit.html", {
        "user": user, 
        "errors": errors,
        "post_data": post_data,
    })


@login_required
def profile_change_password(request):
    """Changer le mot de passe."""
    if request.method == "POST":
        current  = request.POST.get("current_password", "")
        new_pw   = request.POST.get("new_password", "")
        confirm  = request.POST.get("confirm_password", "")
        errors   = {}

        if not request.user.check_password(current):
            errors["current_password"] = "Mot de passe actuel incorrect."
        
        if len(new_pw) < 8:
            errors["new_password"] = "Le mot de passe doit contenir au moins 8 caractères."
        elif new_pw != confirm:
            errors["confirm_password"] = "Les mots de passe ne correspondent pas."

        if errors:
            # On recharge le contexte complet pour afficher les erreurs dans le bon onglet
            context = _get_profile_context(request.user)
            context.update({
                "user": request.user,
                "active_tab": "security",
                "pw_errors": errors,
            })
            return render(request, "client/profile_patient.html", context)

        with transaction.atomic():
            request.user.set_password(new_pw)
            request.user.save()
            update_session_auth_hash(request, request.user)
            
        messages.success(request, "Mot de passe modifié avec succès.")
        return redirect("auth_user:profile")

    return redirect("auth_user:profile")


@login_required
def profile_orders(request):
    """Liste complète des commandes du patient (peut être une vue dédiée ou un filtre dans profile)."""
    if request.user.role != "PATIENT":
        return redirect("auth_user:profile")
        
    status_filter = request.GET.get("status", "")
    orders = Order.objects.filter(patient=request.user).select_related("pharmacy").order_by("-created_at")
    
    if status_filter:
        orders = orders.filter(status=status_filter)

    context = _get_profile_context(request.user)
    context.update({
        "user":          request.user,
        "orders":        orders,
        "active_tab":    "orders",
        "status_filter": status_filter,
        "status_choices": Order.STATUS_CHOICES,
    })
    
    # Si vous avez un template dédié 'client/profile_orders.html', changez le nom ci-dessous
    # Sinon, cela réutilise le template principal avec l'onglet actif
    return render(request, "client/profile_patient.html", context)


@login_required
def profile_prescriptions(request):
    """Liste des ordonnances du patient."""
    if request.user.role != "PATIENT":
        return redirect("auth_user:profile")
        
    prescriptions = Prescription.objects.filter(patient=request.user).order_by("-created_at")
    
    context = _get_profile_context(request.user)
    context.update({
        "user": request.user,
        "prescriptions_list": prescriptions,
        "active_tab": "prescriptions",
    })
    
    return render(request, "client/profile_patient.html", context)


# ──────────────────────────────────────────────────────────────────
# PANIER
# ──────────────────────────────────────────────────────────────────
@login_required
def cart_view(request):
    """Affiche le panier du patient."""
    try:
        cart = Cart.objects.get(patient=request.user)
        items = cart.items.select_related('medication', 'pharmacy').order_by('-added_at')
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
    medication_id = request.POST.get('medication_id')
    pharmacy_id = request.POST.get('pharmacy_id')
    quantity = int(request.POST.get('quantity', 1))
    
    if not medication_id or not pharmacy_id:
        return JsonResponse({'success': False, 'error': 'Données invalides'}, status=400)
    
    from medications.models import Medication, PharmacyMedication
    from pharmacies.models import Pharmacy
    
    try:
        medication = Medication.objects.get(id=medication_id)
        pharmacy = Pharmacy.objects.get(id=pharmacy_id)
        stock = PharmacyMedication.objects.get(
            medication=medication,
            pharmacy=pharmacy,
            quantity__gt=0,
            is_available=True
        )
    except (Medication.DoesNotExist, Pharmacy.DoesNotExist, PharmacyMedication.DoesNotExist):
        return JsonResponse({'success': False, 'error': 'Produit non disponible'}, status=404)
    
    # Récupérer ou créer le panier
    cart, _ = Cart.objects.get_or_create(patient=request.user)
    
    # Vérifier si l'article existe déjà
    existing_item = CartItem.objects.filter(
        cart=cart,
        medication=medication,
        pharmacy=pharmacy
    ).first()
    
    if existing_item:
        # Mettre à jour la quantité
        new_quantity = existing_item.quantity + quantity
        # Vérifier le stock max
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
        # Créer nouvel article
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


@require_http_methods(["POST"])
@login_required
@transaction.atomic
def cart_update(request, item_id):
    """Met à jour la quantité d'un article (AJAX)."""
    try:
        item = CartItem.objects.get(id=item_id, cart__patient=request.user)
    except CartItem.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Article non trouvé'}, status=404)
    
    action = request.POST.get('action', 'update')
    
    if action == 'remove':
        item.delete()
        return JsonResponse({
            'success': True,
            'action': 'removed',
            'item_count': item.cart.get_item_count(),
            'total_amount': str(item.cart.get_total_amount()),
        })
    
    # Update quantity
    try:
        quantity = int(request.POST.get('quantity', item.quantity))
        if quantity < 1:
            raise ValueError()
    except ValueError:
        return JsonResponse({'success': False, 'error': 'Quantité invalide'}, status=400)
    
    # Vérifier le stock
    from medications.models import PharmacyMedication
    stock = PharmacyMedication.objects.filter(
        medication=item.medication,
        pharmacy=item.pharmacy,
        quantity__gt=0,
        is_available=True
    ).first()
    
    if not stock:
        return JsonResponse({'success': False, 'error': 'Produit plus disponible'}, status=400)
    
    if quantity > stock.quantity:
        return JsonResponse({
            'success': False, 
            'error': f'Stock insuffisant. Maximum {stock.quantity} disponible.'
        }, status=400)
    
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
    """Vide le panier."""
    try:
        cart = Cart.objects.get(patient=request.user)
        cart.clear()
        return JsonResponse({'success': True, 'message': 'Panier vidé'})
    except Cart.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Panier non trouvé'}, status=404)