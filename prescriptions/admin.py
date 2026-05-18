# admin.py

from django.contrib import admin
from .models import Prescription


@admin.register(Prescription)
class PrescriptionAdmin(admin.ModelAdmin):

    list_display = (
        "id",
        "patient",
        "order",
        "status",
        "reviewed_by",
        "reviewed_at",
        "created_at",
    )

    list_filter = (
        "status",
        "reviewed_at",
        "created_at",
    )

    search_fields = (
        "patient__username",
        "patient__email",
        "patient__phone",
        "reviewed_by__username",
        "reviewed_by__email",
    )

    readonly_fields = (
        "id",
        "created_at",
    )

    ordering = ("-created_at",)

    fieldsets = (
        ("Informations ordonnance", {
            "fields": (
                "id",
                "patient",
                "order",
                "image",
            )
        }),

        ("Validation", {
            "fields": (
                "status",
                "reviewed_by",
                "reviewed_at",
            )
        }),

        ("Dates", {
            "fields": (
                "created_at",
            )
        }),
    )