from django.db import models
import uuid

class MedicationCategory(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=150)
    slug = models.SlugField(unique=True)

    def __str__(self):
        return self.name
    
class Medication(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    category = models.ForeignKey(
        MedicationCategory,
        on_delete=models.SET_NULL,
        null=True,
        related_name="medications"
    )

    name = models.CharField(max_length=255)

    description = models.TextField(blank=True)

    manufacturer = models.CharField(max_length=255, blank=True)

    requires_prescription = models.BooleanField(default=False)

    is_rare = models.BooleanField(default=False)

    image = models.ImageField(
        upload_to="medications/",
        null=True,
        blank=True
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name
    
class PharmacyMedication(models.Model):
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

    quantity = models.PositiveIntegerField(default=0)

    price = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    is_available = models.BooleanField(default=True)

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("pharmacy", "medication")

class StockHistory(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    pharmacy_medication = models.ForeignKey(
        PharmacyMedication,
        on_delete=models.CASCADE,
        related_name="history"
    )

    previous_quantity = models.IntegerField()

    new_quantity = models.IntegerField()

    reason = models.CharField(max_length=255, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

