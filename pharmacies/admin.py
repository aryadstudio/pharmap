from django.contrib import admin
from .models import Pharmacy
from .forms import PharmacyForm


@admin.register(Pharmacy)
class PharmacyAdmin(admin.ModelAdmin):
    form = PharmacyForm

    list_display = (
        "name",
        "owner",
        "city",
        "country",
        "phone",
        "email",
        "is_verified",
        "is_open_24h",
        "average_rating",
        "total_reviews",
        "created_at",
    )

    list_filter = (
        "is_verified",
        "is_open_24h",
        "city",
        "country",
        "created_at",
    )

    search_fields = (
        "name",
        "city",
        "country",
        "phone",
        "email",
        "owner__username",
        "owner__email",
    )

    ordering = ("-created_at",)

    readonly_fields = ("average_rating", "total_reviews", "created_at")

    fieldsets = (
        ("Informations générales", {
            "fields": (
                "owner",
                "name",
                "description",
                "logo",
            )
        }),
        ("Localisation", {
            "fields": (
                "address",
                "city",
                "country",
                "latitude",
                "longitude",
            )
        }),
        ("Contact", {
            "fields": (
                "phone",
                "email",
            )
        }),
        ("Horaires", {
            "fields": (
                "opening_time",
                "closing_time",
                "is_open_24h",
            )
        }),
        ("Statut & Statistiques", {
            "fields": (
                "is_verified",
                "average_rating",
                "total_reviews",
                "created_at",
            )
        }),
    )

    list_editable = ("is_verified",)

    list_per_page = 25

    date_hierarchy = "created_at"

    save_on_top = True