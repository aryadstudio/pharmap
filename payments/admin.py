from django.contrib import admin
from .models import Payment


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):

    list_display = (
        "id",
        "order",
        "method",
        "amount",
        "status",
        "transaction_id",
        "paid_at",
        "created_at",
    )

    list_filter = (
        "method",
        "status",
        "paid_at",
        "created_at",
    )

    search_fields = (
        "transaction_id",
        "order__id",
        "order__user__username",
        "order__user__email",
    )

    readonly_fields = (
        "id",
        "created_at",
    )

    ordering = ("-created_at",)

    fieldsets = (
        ("Informations du paiement", {
            "fields": (
                "id",
                "order",
                "method",
                "amount",
                "status",
            )
        }),

        ("Transaction", {
            "fields": (
                "transaction_id",
                "paid_at",
            )
        }),

        ("Dates", {
            "fields": (
                "created_at",
            )
        }),
    )