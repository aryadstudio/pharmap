from django.contrib import admin
from django.utils.html import format_html
from .models import PharmacyReview
from .forms import PharmacyReviewForm


@admin.register(PharmacyReview)
class PharmacyReviewAdmin(admin.ModelAdmin):
    form = PharmacyReviewForm

    list_display = (
        "patient",
        "pharmacy",
        "stars",
        "short_comment",
        "created_at",
    )

    list_filter = (
        "rating",
        "pharmacy",
        "created_at",
    )

    search_fields = (
        "patient__username",
        "patient__email",
        "pharmacy__name",
        "comment",
    )

    readonly_fields = ("created_at", "stars")

    ordering = ("-created_at",)

    date_hierarchy = "created_at"

    save_on_top = True

    list_per_page = 25

    fieldsets = (
        ("Avis", {
            "fields": (
                "patient",
                "pharmacy",
                "rating",
                "stars",
                "comment",
            )
        }),
        ("Métadonnées", {
            "fields": ("created_at",),
            "classes": ("collapse",),
        }),
    )

    def stars(self, obj):
        filled = "★" * obj.rating
        empty  = "☆" * (5 - obj.rating)
        color  = "#f5a623" if obj.rating >= 4 else "#e74c3c" if obj.rating <= 2 else "#f0ad4e"
        return format_html(
            '<span style="color: {}; font-size: 1.2em;">{}{}</span>',
            color, filled, empty
        )
    stars.short_description = "Note"

    def short_comment(self, obj):
        if not obj.comment:
            return format_html('<span style="color: #aaa;">—</span>')
        truncated = obj.comment[:60] + "…" if len(obj.comment) > 60 else obj.comment
        return truncated
    short_comment.short_description = "Commentaire"