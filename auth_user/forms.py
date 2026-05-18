from django import forms
from django.contrib.auth.password_validation import validate_password
from auth_user.models import User
from pharmacies.models import Pharmacy


# ──────────────────────────────────────────────────────────────────
# Formulaire patient
# ──────────────────────────────────────────────────────────────────

class PatientRegisterForm(forms.Form):
    first_name = forms.CharField(max_length=150, label="Prénom")
    last_name  = forms.CharField(max_length=150, label="Nom")
    email      = forms.EmailField(label="Email")
    phone      = forms.CharField(max_length=30, label="Téléphone")
    password1  = forms.CharField(widget=forms.PasswordInput, label="Mot de passe")
    password2  = forms.CharField(widget=forms.PasswordInput, label="Confirmer le mot de passe")

    def clean_email(self):
        email = self.cleaned_data["email"]
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("Un compte avec cet email existe déjà.")
        return email

    def clean_phone(self):
        phone = self.cleaned_data["phone"]
        if User.objects.filter(phone=phone).exists():
            raise forms.ValidationError("Ce numéro de téléphone est déjà utilisé.")
        return phone

    def clean_password1(self):
        password = self.cleaned_data.get("password1")
        validate_password(password)
        return password

    def clean(self):
        cleaned = super().clean()
        p1 = cleaned.get("password1")
        p2 = cleaned.get("password2")
        if p1 and p2 and p1 != p2:
            self.add_error("password2", "Les mots de passe ne correspondent pas.")
        return cleaned

    def save(self):
        data = self.cleaned_data
        username = data["email"].split("@")[0]
        base, i = username, 1
        while User.objects.filter(username=username).exists():
            username = f"{base}{i}"
            i += 1

        user = User.objects.create_user(
            username   = username,
            email      = data["email"],
            password   = data["password1"],
            first_name = data["first_name"],
            last_name  = data["last_name"],
            phone      = data["phone"],
            role       = "PATIENT",
        )
        return user


# ──────────────────────────────────────────────────────────────────
# Formulaire pharmacien + pharmacie (atomique)
# ──────────────────────────────────────────────────────────────────

class PharmacistRegisterForm(forms.Form):

    # ── Compte utilisateur ──
    first_name = forms.CharField(max_length=150, label="Prénom du responsable")
    last_name  = forms.CharField(max_length=150, label="Nom du responsable")
    email      = forms.EmailField(label="Email professionnel")
    phone      = forms.CharField(max_length=30, label="Téléphone personnel")
    password1  = forms.CharField(widget=forms.PasswordInput, label="Mot de passe")
    password2  = forms.CharField(widget=forms.PasswordInput, label="Confirmer le mot de passe")

    # ── Informations pharmacie ──
    pharmacy_name    = forms.CharField(max_length=255, label="Nom de la pharmacie")
    pharmacy_address = forms.CharField(widget=forms.Textarea(attrs={"rows": 2}), label="Adresse complète")
    pharmacy_city    = forms.CharField(max_length=100, label="Ville")
    pharmacy_country = forms.CharField(max_length=100, initial="Gabon", label="Pays")
    pharmacy_phone   = forms.CharField(max_length=30, label="Téléphone de la pharmacie")
    pharmacy_email   = forms.EmailField(required=False, label="Email de la pharmacie (optionnel)")
    pharmacy_lat     = forms.FloatField(label="Latitude", widget=forms.HiddenInput)
    pharmacy_lng     = forms.FloatField(label="Longitude", widget=forms.HiddenInput)
    opening_time     = forms.TimeField(
        label="Heure d'ouverture",
        widget=forms.TimeInput(attrs={"type": "time"}),
        required=False,
    )
    closing_time     = forms.TimeField(
        label="Heure de fermeture",
        widget=forms.TimeInput(attrs={"type": "time"}),
        required=False,
    )
    is_open_24h      = forms.BooleanField(required=False, label="Ouvert 24h/24")
    description      = forms.CharField(
        widget=forms.Textarea(attrs={"rows": 3}),
        required=False,
        label="Description de la pharmacie",
    )
    logo             = forms.ImageField(required=False, label="Logo de la pharmacie")
    benefits         = [
        "Fiche pharmacie géolocalisée",
        "Gestion de stock en temps réel",
        "Réception de réservations",
        "Paiement Airtel Money & Mobicash",
        "Tableau de bord & statistiques",
    ]

    def clean_email(self):
        email = self.cleaned_data["email"]
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("Un compte avec cet email existe déjà.")
        return email

    def clean_phone(self):
        phone = self.cleaned_data["phone"]
        if User.objects.filter(phone=phone).exists():
            raise forms.ValidationError("Ce numéro est déjà utilisé.")
        return phone

    def clean_password1(self):
        password = self.cleaned_data.get("password1")
        validate_password(password)
        return password

    def clean(self):
        cleaned = super().clean()
        p1 = cleaned.get("password1")
        p2 = cleaned.get("password2")
        if p1 and p2 and p1 != p2:
            self.add_error("password2", "Les mots de passe ne correspondent pas.")

        is_24h  = cleaned.get("is_open_24h")
        opening = cleaned.get("opening_time")
        closing = cleaned.get("closing_time")
        if not is_24h:
            if not opening:
                self.add_error("opening_time", "Indiquez l'heure d'ouverture.")
            if not closing:
                self.add_error("closing_time", "Indiquez l'heure de fermeture.")
        return cleaned

    def save(self):
        from django.db import transaction
        data = self.cleaned_data

        with transaction.atomic():
            # 1 — Créer le compte pharmacien
            username = data["email"].split("@")[0]
            base, i = username, 1
            while User.objects.filter(username=username).exists():
                username = f"{base}{i}"
                i += 1

            user = User.objects.create_user(
                username   = username,
                email      = data["email"],
                password   = data["password1"],
                first_name = data["first_name"],
                last_name  = data["last_name"],
                phone      = data["phone"],
                role       = "PHARMACIST",
            )

            # 2 — Créer la pharmacie liée
            pharmacy_kwargs = dict(
                owner       = user,
                name        = data["pharmacy_name"],
                description = data.get("description", ""),
                address     = data["pharmacy_address"],
                city        = data["pharmacy_city"],
                country     = data.get("pharmacy_country") or "Gabon",
                phone       = data["pharmacy_phone"],
                email       = data.get("pharmacy_email", ""),
                latitude    = data["pharmacy_lat"],
                longitude   = data["pharmacy_lng"],
                is_open_24h = bool(data.get("is_open_24h")),
                is_verified = False,
            )
            if data.get("is_open_24h"):
                from datetime import time
                pharmacy_kwargs["opening_time"] = time(0, 0)
                pharmacy_kwargs["closing_time"] = time(23, 59)
            else:
                pharmacy_kwargs["opening_time"] = data["opening_time"]
                pharmacy_kwargs["closing_time"] = data["closing_time"]

            pharmacy = Pharmacy(**pharmacy_kwargs)
            if data.get("logo"):
                pharmacy.logo = data["logo"]
            pharmacy.save()

        return user, pharmacy