from django.shortcuts import render, redirect
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum

from auth_user.models import User
from orders.models import Order
from reviews.models import PharmacyReview
from prescriptions.models import Prescription

# ──────────────────────────────────────────────────────────────────
# Profil patient
# ──────────────────────────────────────────────────────────────────

@login_required
def profile(request):
    """Page principale du profil patient."""
    user = request.user

    # Stats rapides
    orders      = Order.objects.filter(patient=user).select_related("pharmacy")
    reviews     = PharmacyReview.objects.filter(patient=user).select_related("pharmacy")
    prescriptions = Prescription.objects.filter(patient=user).order_by("-created_at")

    stats = {
        "total_orders":       orders.count(),
        "pending_orders":     orders.filter(status="PENDING").count(),
        "delivered_orders":   orders.filter(status="DELIVERED").count(),
        "cancelled_orders":   orders.filter(status="CANCELLED").count(),
        "total_reviews":      reviews.count(),
        "total_prescriptions": prescriptions.count(),
        "total_spent":        orders.filter(status="DELIVERED").aggregate(
                                  s=Sum("total_amount"))["s"] or 0,
    }

    # Commandes récentes (5 dernières)
    recent_orders = orders.prefetch_related("items__medication")[:5]

    # Avis récents
    recent_reviews = reviews[:3]

    context = {
        "user":          user,
        "stats":         stats,
        "recent_orders": recent_orders,
        "recent_reviews": recent_reviews,
        "prescriptions": prescriptions[:5],
        "active_tab":    request.GET.get("tab", "overview"),
    }
    return render(request, "client/profile_patient.html", context)


@login_required
def profile_edit(request):
    """Modifier les infos personnelles."""
    user = request.user

    if request.method == "POST":
        first_name = request.POST.get("first_name", "").strip()
        last_name  = request.POST.get("last_name", "").strip()
        phone      = request.POST.get("phone", "").strip()
        email      = request.POST.get("email", "").strip()

        errors = {}

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

        if errors:
            return render(request, "client/profile_edit.html", {
                "user": user, "errors": errors,
                "post": request.POST,
            })

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

    return render(request, "client/profile_edit.html", {"user": user, "errors": {}})


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
        if new_pw != confirm:
            errors["confirm_password"] = "Les mots de passe ne correspondent pas."

        if errors:
            return render(request, "client/profile_patient.html", {
                "user":       request.user,
                "active_tab": "security",
                "pw_errors":  errors,
                **_profile_context(request.user),
            })

        request.user.set_password(new_pw)
        request.user.save()
        update_session_auth_hash(request, request.user)
        messages.success(request, "Mot de passe modifié avec succès.")
        return redirect("auth_user:profile")

    return redirect("auth_user:profile")


# ──────────────────────────────────────────────────────────────────
# Commandes (onglet)
# ──────────────────────────────────────────────────────────────────

@login_required
def profile_orders(request):
    """Liste complète des commandes du patient."""
    status_filter = request.GET.get("status", "")
    orders = Order.objects.filter(patient=request.user).select_related("pharmacy")
    if status_filter:
        orders = orders.filter(status=status_filter)

    context = {
        "user":          request.user,
        "orders":        orders,
        "active_tab":    "orders",
        "status_filter": status_filter,
        "status_choices": Order.STATUS_CHOICES,
        **_profile_context(request.user),
    }
    return render(request, "client/profile_patient.html", context)


# ──────────────────────────────────────────────────────────────────
# Helpers internes
# ──────────────────────────────────────────────────────────────────

def _profile_context(user):
    """Construit le contexte commun à tous les onglets du profil."""
    orders = Order.objects.filter(patient=user)
    return {
        "stats": {
            "total_orders":     orders.count(),
            "pending_orders":   orders.filter(status="PENDING").count(),
            "delivered_orders": orders.filter(status="DELIVERED").count(),
            "cancelled_orders": orders.filter(status="CANCELLED").count(),
            "total_reviews":    PharmacyReview.objects.filter(patient=user).count(),
            "total_prescriptions": Prescription.objects.filter(patient=user).count(),
            "total_spent":      orders.filter(status="DELIVERED").aggregate(
                                    s=Sum("total_amount"))["s"] or 0,
        },
        "recent_orders":  orders.prefetch_related("items__medication")[:5],
        "recent_reviews": PharmacyReview.objects.filter(patient=user).select_related("pharmacy")[:3],
        "prescriptions":  Prescription.objects.filter(patient=user).order_by("-created_at")[:5],
    }