from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):

    list_display = (
        "id",
        "username",
        "email",
        "first_name",
        "last_name",
        "role",
        "phone",
        "is_verified",
        "is_staff",
        "is_active",
        "created_at",
    )

    list_filter = (
        "role",
        "is_verified",
        "is_staff",
        "is_superuser",
        "is_active",
        "created_at",
    )

    search_fields = (
        "username",
        "email",
        "first_name",
        "last_name",
        "phone",
    )

    ordering = ("-created_at",)

    readonly_fields = (
        "created_at",
        "updated_at",
        "last_login",
        "date_joined",
    )

    fieldsets = (
        ("Informations de connexion", {
            "fields": (
                "username",
                "password",
                "email",
            )
        }),

        ("Informations personnelles", {
            "fields": (
                "first_name",
                "last_name",
                "phone",
                "profile_picture",
            )
        }),

        ("Rôle & vérification", {
            "fields": (
                "role",
                "is_verified",
            )
        }),

        ("Localisation", {
            "fields": (
                "latitude",
                "longitude",
            )
        }),

        ("Permissions", {
            "fields": (
                "is_active",
                "is_staff",
                "is_superuser",
                "groups",
                "user_permissions",
            )
        }),

        ("Dates importantes", {
            "fields": (
                "last_login",
                "date_joined",
                "created_at",
                "updated_at",
            )
        }),
    )

    add_fieldsets = (
        (
            "Créer un utilisateur",
            {
                "classes": ("wide",),
                "fields": (
                    "username",
                    "email",
                    "first_name",
                    "last_name",
                    "phone",
                    "role",
                    "password1",
                    "password2",
                    "is_staff",
                    "is_active",
                ),
            },
        ),
    )