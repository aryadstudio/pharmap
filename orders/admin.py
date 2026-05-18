from django.contrib import admin
from django.utils.html import format_html
from .models import Order, OrderItem


class OrderItemInline(admin.TabularInline):
    model       = OrderItem
    extra       = 0
    readonly_fields = ("subtotal",)
    fields      = ("medication", "quantity", "unit_price", "subtotal")
    min_num     = 1
    can_delete  = True


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):

    list_display = (
        "id",
        "patient",
        "pharmacy",
        "status_badge",
        "total_amount",
        "item_count",
        "created_at",
    )

    list_filter  = ("status", "pharmacy", "created_at")

    search_fields = (
        "patient__username",
        "patient__email",
        "pharmacy__name",
    )

    readonly_fields  = ("total_amount", "created_at", "updated_at")
    ordering         = ("-created_at",)
    date_hierarchy   = "created_at"
    save_on_top      = True
    list_per_page    = 25
    inlines          = [OrderItemInline]

    fieldsets = (
        ("Commande", {
            "fields": ("patient", "pharmacy", "status", "note")
        }),
        ("Montants & Dates", {
            "fields": ("total_amount", "created_at", "updated_at"),
            "classes": ("collapse",),
        }),
    )

    def status_badge(self, obj):
        colors = {
            "PENDING":   "#f0ad4e",
            "CONFIRMED": "#5bc0de",
            "READY":     "#6EDCBC",
            "DELIVERED": "#5cb85c",
            "CANCELLED": "#d9534f",
        }
        color = colors.get(obj.status, "#aaa")
        return format_html(
            '<span style="background:{};color:white;padding:3px 10px;'
            'border-radius:999px;font-size:0.75rem;font-weight:700;">{}</span>',
            color, obj.get_status_display()
        )
    status_badge.short_description = "Statut"

    def item_count(self, obj):
        return obj.items.count()
    item_count.short_description = "Articles"


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):

    list_display  = ("order", "medication", "quantity", "unit_price", "subtotal")
    list_filter   = ("medication__category",)
    search_fields = ("order__id", "medication__name")
    readonly_fields = ("subtotal",)
    list_per_page = 50