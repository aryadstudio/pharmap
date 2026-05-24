from django.contrib import admin
from django.utils.html import format_html
from .models import Payment

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ("get_short_id", "order_link", "method_badge", "amount_display", "status_badge", "paid_at", "created_at")
    list_filter = ("method", "status", "paid_at", "created_at")
    search_fields = ("transaction_id", "order__id", "order__patient__username", "order__patient__email")
    readonly_fields = ("id", "created_at", "updated_at", "metadata_display")
    ordering = ("-created_at",)
    date_hierarchy = "created_at"

    fieldsets = (
        ("Informations principales", {
            "fields": ("id", "order", "method", "amount", "status"),
            "description": "Détails généraux de la transaction."
        }),
        ("Détails de la transaction", {
            "fields": ("transaction_id", "paid_at", "cash_verified_by"),
            "description": "Références externes et validation."
        }),
        ("Données techniques", {
            "fields": ("metadata_display", "created_at", "updated_at"),
            "classes": ("collapse",),
            "description": "Données brutes API et horodatages."
        }),
    )

    # --- Custom Display Methods ---

    def get_short_id(self, obj):
        return str(obj.id)[:8] + "..."
    get_short_id.short_description = "ID"

    def order_link(self, obj):
        if obj.order:
            return format_html('<a href="/admin/orders/order/{}/change/">#{}</a>', obj.order.id, str(obj.order.id)[:6])
        return "-"
    order_link.short_description = "Commande"

    def method_badge(self, obj):
        colors = {
            "AIRTEL": "#E90505", "MOOV": "#004B93", 
            "CARD": "#635BFF", "CASH": "#27AE60"
        }
        color = colors.get(obj.method, "#777")
        return format_html(
            '<span style="background:{}; color:white; padding:4px 8px; border-radius:4px; font-size:11px; font-weight:bold;">{}</span>',
            color, obj.get_method_display()
        )
    method_badge.short_description = "Méthode"

    def amount_display(self, obj):
        return f"{obj.amount:,.0f} FCFA"
    amount_display.short_description = "Montant"

    def status_badge(self, obj):
        colors = {
            "PENDING": "#F39C12", "PROCESSING": "#3498DB",
            "SUCCESS": "#27AE60", "FAILED": "#C0392B", 
            "CANCELLED": "#7F8C8D", "REFUNDED": "#8E44AD"
        }
        color = colors.get(obj.status, "#95a5a6")
        return format_html(
            '<span style="background:{}; color:white; padding:4px 8px; border-radius:4px; font-size:11px; font-weight:bold;">{}</span>',
            color, obj.get_status_display()
        )
    status_badge.short_description = "Statut"

    def metadata_display(self, obj):
        if obj.metadata:
            import json
            return format_html('<pre style="max-height:200px; overflow:auto; background:#f4f4f4; padding:10px; border-radius:4px;">{}</pre>', json.dumps(obj.metadata, indent=2, ensure_ascii=False))
        return "Aucune donnée technique."
    metadata_display.short_description = "Métadonnées (JSON)"