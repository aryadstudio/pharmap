from django.contrib import admin
from .models import (
    MedicationCategory,
    Medication,
    PharmacyMedication,
    StockHistory
)
from .forms import (
    MedicationCategoryForm,
    MedicationForm,
    PharmacyMedicationForm,
    StockHistoryForm
)


@admin.register(MedicationCategory)
class MedicationCategoryAdmin(admin.ModelAdmin):
    form = MedicationCategoryForm

    list_display = ("name", "slug", "medication_count")
    search_fields = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}
    ordering = ("name",)

    def medication_count(self, obj):
        return obj.medications.count()
    medication_count.short_description = "Médicaments"


@admin.register(Medication)
class MedicationAdmin(admin.ModelAdmin):
    form = MedicationForm

    list_display = (
        "name",
        "category",
        "manufacturer",
        "requires_prescription",
        "is_rare",
        "created_at",
    )

    list_filter = (
        "category",
        "requires_prescription",
        "is_rare",
        "created_at",
    )

    search_fields = ("name", "manufacturer", "category__name")

    list_editable = ("requires_prescription", "is_rare")

    readonly_fields = ("created_at",)

    ordering = ("-created_at",)

    date_hierarchy = "created_at"

    save_on_top = True

    fieldsets = (
        ("Informations générales", {
            "fields": (
                "category",
                "name",
                "description",
                "image",
            )
        }),
        ("Fabricant & Statut", {
            "fields": (
                "manufacturer",
                "requires_prescription",
                "is_rare",
            )
        }),
        ("Métadonnées", {
            "fields": ("created_at",),
            "classes": ("collapse",),
        }),
    )

    list_per_page = 25


class StockHistoryInline(admin.TabularInline):
    model = StockHistory
    form = StockHistoryForm
    extra = 0
    readonly_fields = ("created_at",)
    fields = ("previous_quantity", "new_quantity", "reason", "created_at")
    ordering = ("-created_at",)
    can_delete = False


@admin.register(PharmacyMedication)
class PharmacyMedicationAdmin(admin.ModelAdmin):
    form = PharmacyMedicationForm

    list_display = (
        "pharmacy",
        "medication",
        "quantity",
        "price",
        "is_available",
        "updated_at",
    )

    list_filter = (
        "is_available",
        "pharmacy",
        "medication__category",
    )

    search_fields = (
        "medication__name",
        "pharmacy__name",
        "medication__manufacturer",
    )

    list_editable = ("quantity", "price", "is_available")

    readonly_fields = ("updated_at",)

    ordering = ("pharmacy", "medication")

    save_on_top = True

    inlines = [StockHistoryInline]

    fieldsets = (
        ("Stock", {
            "fields": (
                "pharmacy",
                "medication",
                "quantity",
                "price",
                "is_available",
            )
        }),
        ("Métadonnées", {
            "fields": ("updated_at",),
            "classes": ("collapse",),
        }),
    )

    list_per_page = 25


@admin.register(StockHistory)
class StockHistoryAdmin(admin.ModelAdmin):
    form = StockHistoryForm

    list_display = (
        "pharmacy_medication",
        "previous_quantity",
        "new_quantity",
        "delta",
        "reason",
        "created_at",
    )

    list_filter = (
        "created_at",
        "pharmacy_medication__pharmacy",
        "pharmacy_medication__medication__category",
    )

    search_fields = (
        "pharmacy_medication__medication__name",
        "pharmacy_medication__pharmacy__name",
        "reason",
    )

    readonly_fields = ("created_at", "delta")

    ordering = ("-created_at",)

    date_hierarchy = "created_at"

    list_per_page = 50

    fieldsets = (
        ("Mouvement de stock", {
            "fields": (
                "pharmacy_medication",
                "previous_quantity",
                "new_quantity",
                "delta",
                "reason",
            )
        }),
        ("Métadonnées", {
            "fields": ("created_at",),
            "classes": ("collapse",),
        }),
    )

    def delta(self, obj):
        diff = obj.new_quantity - obj.previous_quantity
        sign = "+" if diff >= 0 else ""
        return f"{sign}{diff}"
    delta.short_description = "Variation"