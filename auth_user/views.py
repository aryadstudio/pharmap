from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib import messages
from django.contrib.auth.decorators import login_required

from .forms import PatientRegisterForm, PharmacistRegisterForm
from auth_user.models import User


# ──────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────

def _get_user_by_email(email):
    """Retourne l'utilisateur à partir de son email, ou None."""
    try:
        return User.objects.get(email=email)
    except User.DoesNotExist:
        return None


# ──────────────────────────────────────────────────────────────────
# Inscription patient
# ──────────────────────────────────────────────────────────────────

def register_patient(request):
    form = PatientRegisterForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save()
        login(request, user)
        messages.success(request, "Bienvenue sur PharMap !")
        return redirect("home")
    return render(request, "client/register_patient.html", {"form": form})


# ──────────────────────────────────────────────────────────────────
# Inscription pharmacien
# ──────────────────────────────────────────────────────────────────

def register_pharmacist(request):
    form = PharmacistRegisterForm(request.POST or None, request.FILES or None)
    if request.method == "POST" and form.is_valid():
        user, pharmacy = form.save()
        login(request, user)
        messages.success(
            request,
            f"Pharmacie « {pharmacy.name} » créée. "
            "Elle sera visible après validation par notre équipe (24h)."
        )
        return redirect("pharmacist:dashboard")
    return render(request, "pharmacies/register_pharmacist.html", {"form": form})


# ──────────────────────────────────────────────────────────────────
# Connexion patient
# ──────────────────────────────────────────────────────────────────

def login_patient(request):
    """
    Page de connexion pour les patients.
    Redirige vers la recherche après connexion.
    Refuse les pharmaciens (ils ont leur propre login).
    """
    if request.user.is_authenticated:
        return redirect("home")

    if request.method == "POST":
        email    = request.POST.get("email", "").strip()
        password = request.POST.get("password", "")

        user_obj = _get_user_by_email(email)
        if user_obj is None:
            messages.error(request, "Aucun compte trouvé avec cet email.")
            return render(request, "client/login_patient.html")

        # Un pharmacien ne doit pas passer par le login patient
        if user_obj.role == "PHARMACIST":
            messages.error(
                request,
                "Vous êtes pharmacien. Connectez-vous via l'espace professionnel."
            )
            return redirect("auth_user:login_pharmacist")

        user = authenticate(request, username=user_obj.username, password=password)
        if user is not None:
            login(request, user)
            next_url = request.GET.get("next", "home")
            return redirect(next_url)
        else:
            messages.error(request, "Mot de passe incorrect.")

    return render(request, "client/login_patient.html")


# ──────────────────────────────────────────────────────────────────
# Connexion pharmacien
# ──────────────────────────────────────────────────────────────────

def login_pharmacist(request):
    """
    Page de connexion pour les pharmaciens.
    Redirige vers le dashboard après connexion.
    Refuse les patients.
    """
    if request.user.is_authenticated:
        if request.user.role == "PHARMACIST":
            return redirect("pharmacist:dashboard")
        return redirect("home")

    if request.method == "POST":
        email    = request.POST.get("email", "").strip()
        password = request.POST.get("password", "")

        user_obj = _get_user_by_email(email)
        if user_obj is None:
            messages.error(request, "Aucun compte pharmacien trouvé avec cet email.")
            return render(request, "pharmacies/login_pharmacist.html")

        # Un patient ne doit pas accéder au dashboard pharmacien
        if user_obj.role not in ("PHARMACIST", "ADMIN"):
            messages.error(
                request,
                "Ce compte n'est pas un compte pharmacien."
            )
            return render(request, "pharmacies/login_pharmacist.html")

        user = authenticate(request, username=user_obj.username, password=password)
        if user is not None:
            login(request, user)
            return redirect("pharmacist:dashboard")
        else:
            messages.error(request, "Mot de passe incorrect.")

    return render(request, "pharmacies/login_pharmacist.html")


# ──────────────────────────────────────────────────────────────────
# Déconnexion (commune)
# ──────────────────────────────────────────────────────────────────

def logout_view(request):
    was_pharmacist = request.user.is_authenticated and request.user.role == "PHARMACIST"
    logout(request)
    if was_pharmacist:
        return redirect("auth_user:login_pharmacist")
    return redirect("home")


# ──────────────────────────────────────────────────────────────────
# Profil patient
# ──────────────────────────────────────────────────────────────────

@login_required
def profile_view(request):
    return render(request, "auth_user/profile.html")