from django.contrib import admin
from django.utils.html import format_html
from .models import Pharmacy, Prescription, PharmacyReview

@admin.register(Pharmacy)
class PharmacyAdmin(admin.ModelAdmin):
    list_display = ('name', 'city', 'owner_link', 'is_verified', 'average_rating', 'total_reviews', 'created_at')
    list_filter = ('is_verified', 'city', 'is_open_24h', 'created_at')
    search_fields = ('name', 'owner__username', 'owner__email', 'city', 'phone')
    readonly_fields = ('average_rating', 'total_reviews', 'created_at')
    
    fieldsets = (
        ("Informations générales", {
            "fields": ("owner", "name", "description", "logo")
        }),
        ("Localisation & Contact", {
            "fields": ("address", "city", "country", "latitude", "longitude", "phone", "email")
        }),
        ("Horaires & Statut", {
            "fields": ("opening_time", "closing_time", "is_open_24h", "is_verified")
        }),
        ("Statistiques (Automatique)", {
            "fields": ("average_rating", "total_reviews", "created_at"),
            "classes": ("collapse",)
        }),
    )

    def owner_link(self, obj):
        if obj.owner:
            url = f"/admin/auth_user/user/{obj.owner.id}/change/"
            return format_html('<a href="{}">{}</a>', url, obj.owner.username)
        return "-"
    owner_link.short_description = "Propriétaire"

@admin.register(Prescription)
class PrescriptionAdmin(admin.ModelAdmin):
    list_display = ('id_short', 'patient_link', 'status_badge', 'order_link', 'reviewed_by_link', 'created_at')
    list_filter = ('status', 'created_at', 'reviewed_at')
    search_fields = ('patient__username', 'id', 'order__id')
    readonly_fields = ('created_at', 'reviewed_at', 'id')
    ordering = ('-created_at',)

    actions = ['approve_prescriptions', 'reject_prescriptions']

    def id_short(self, obj):
        return str(obj.id)[:8] + "..."
    id_short.short_description = "ID"

    def status_badge(self, obj):
        colors = {
            'PENDING': '#f39c12',
            'APPROVED': '#27ae60',
            'REJECTED': '#c0392b',
        }
        color = colors.get(obj.status, '#7f8c8d')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; border-radius: 3px; font-size: 11px;">{}</span>',
            color, obj.get_status_display()
        )
    status_badge.short_description = "Statut"

    def patient_link(self, obj):
        if obj.patient:
            url = f"/admin/auth_user/user/{obj.patient.id}/change/"
            return format_html('<a href="{}">{}</a>', url, obj.patient.username)
        return "-"
    patient_link.short_description = "Patient"

    def order_link(self, obj):
        if obj.order:
            url = f"/admin/orders/order/{obj.order.id}/change/"
            return format_html('<a href="{}">Commande #{}</a>', url, str(obj.order.id)[:8])
        return "-"
    order_link.short_description = "Commande"

    def reviewed_by_link(self, obj):
        if obj.reviewed_by:
            url = f"/admin/auth_user/user/{obj.reviewed_by.id}/change/"
            return format_html('<a href="{}">{}</a>', url, obj.reviewed_by.username)
        return "-"
    reviewed_by_link.short_description = "Validé par"

    def approve_prescriptions(self, request, queryset):
        updated = queryset.update(status='APPROVED')
        self.message_user(request, f"{updated} ordonnances approuvées avec succès.")
    approve_prescriptions.short_description = "Approuver les sélections"

    def reject_prescriptions(self, request, queryset):
        updated = queryset.update(status='REJECTED')
        self.message_user(request, f"{updated} ordonnances rejetées.")
    reject_prescriptions.short_description = "Rejeter les sélections"

@admin.register(PharmacyReview)
class PharmacyReviewAdmin(admin.ModelAdmin):
    list_display = ('patient_link', 'pharmacy_link', 'rating_stars', 'comment_preview', 'created_at')
    list_filter = ('rating', 'created_at')
    search_fields = ('patient__username', 'pharmacy__name', 'comment')
    readonly_fields = ('created_at',)
    ordering = ('-created_at',)

    def patient_link(self, obj):
        if obj.patient:
            url = f"/admin/auth_user/user/{obj.patient.id}/change/"
            return format_html('<a href="{}">{}</a>', url, obj.patient.username)
        return "-"
    patient_link.short_description = "Patient"

    def pharmacy_link(self, obj):
        if obj.pharmacy:
            url = f"/admin/pharmacies/pharmacy/{obj.pharmacy.id}/change/"
            return format_html('<a href="{}">{}</a>', url, obj.pharmacy.name)
        return "-"
    pharmacy_link.short_description = "Pharmacie"

    def rating_stars(self, obj):
        return "★" * obj.rating + "☆" * (5 - obj.rating)
    rating_stars.short_description = "Note"

    def comment_preview(self, obj):
        if obj.comment:
            return (obj.comment[:50] + "...") if len(obj.comment) > 50 else obj.comment
        return "-"
    comment_preview.short_description = "Commentaire"