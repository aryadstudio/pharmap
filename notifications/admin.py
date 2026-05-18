# admin.py

from django.contrib import admin
from .models import Notification


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):

    list_display = (
        "id",
        "user",
        "title",
        "notification_type",
        "is_read",
        "created_at",
    )

    list_filter = (
        "notification_type",
        "is_read",
        "created_at",
    )

    search_fields = (
        "title",
        "message",
        "user__username",
        "user__email",
        "user__phone",
    )

    readonly_fields = (
        "id",
        "created_at",
    )

    ordering = ("-created_at",)

    fieldsets = (
        ("Informations notification", {
            "fields": (
                "id",
                "user",
                "notification_type",
            )
        }),

        ("Contenu", {
            "fields": (
                "title",
                "message",
            )
        }),

        ("Statut", {
            "fields": (
                "is_read",
            )
        }),

        ("Dates", {
            "fields": (
                "created_at",
            )
        }),
    )