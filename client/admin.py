from django.contrib import admin
from .models import Cart, CartItem


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ('id', 'patient', 'get_total_amount', 'get_item_count', 'created_at', 'updated_at')
    search_fields = ('patient__username', 'patient__email')
    readonly_fields = ('created_at', 'updated_at')
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('patient')


@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ('id', 'cart', 'medication', 'pharmacy', 'quantity', 'unit_price', 'subtotal', 'added_at')
    list_filter = ('pharmacy', 'added_at')
    search_fields = ('cart__patient__username', 'medication__name')
    readonly_fields = ('subtotal', 'added_at', 'updated_at')
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('cart', 'medication', 'pharmacy')