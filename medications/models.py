from django.db import models
import uuid

class MedicationCategory(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=150)
    slug = models.SlugField(unique=True)

    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name_plural = "Catégories de médicaments"


class Medication(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    category = models.ForeignKey(
        MedicationCategory,
        on_delete=models.SET_NULL,
        null=True,
        related_name="medications",
        verbose_name="Catégorie"
    )

    name = models.CharField(max_length=255, verbose_name="Nom du médicament")
    description = models.TextField(blank=True, verbose_name="Description")
    manufacturer = models.CharField(max_length=255, blank=True, verbose_name="Laboratoire")
    
    requires_prescription = models.BooleanField(default=False, verbose_name="Ordonnance requise")
    is_rare = models.BooleanField(default=False, verbose_name="Médicament rare")

    image = models.ImageField(
        upload_to="medications/",
        null=True,
        blank=True,
        verbose_name="Image"
    )

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Date de création")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = "Médicaments"
        ordering = ['name']


class PharmacyMedication(models.Model):
    """Lien entre une pharmacie et un médicament (Stock)"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    pharmacy = models.ForeignKey(
        "pharmacies.Pharmacy",
        on_delete=models.CASCADE,
        related_name="stocks"
    )

    medication = models.ForeignKey(
        Medication,
        on_delete=models.CASCADE,
        related_name="pharmacy_stocks"
    )

    quantity = models.PositiveIntegerField(default=0, verbose_name="Quantité")
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Prix (FCFA)"
    )

    is_available = models.BooleanField(default=True, verbose_name="Disponible")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Dernière mise à jour")

    class Meta:
        unique_together = ("pharmacy", "medication")
        verbose_name = "Stock Pharmacie"
        verbose_name_plural = "Stocks Pharmacies"

    def __str__(self):
        return f"{self.medication.name} - {self.pharmacy.name}"


class StockHistory(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    pharmacy_medication = models.ForeignKey(
        PharmacyMedication,
        on_delete=models.CASCADE,
        related_name="history"
    )

    previous_quantity = models.IntegerField(verbose_name="Quantité précédente")
    new_quantity = models.IntegerField(verbose_name="Nouvelle quantité")
    reason = models.CharField(max_length=255, blank=True, verbose_name="Raison")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Date")

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Historique de stock"

    def __str__(self):
        return f"{self.pharmacy_medication.medication.name} ({self.previous_quantity} -> {self.new_quantity})"