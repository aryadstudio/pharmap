import uuid
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from auth_user.models import User
# Import différé pour éviter les conflits circulaires si Order n'est pas encore chargé
# ou utilisez une string de référence comme fait ci-dessous pour Order

class Pharmacy(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    owner = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="pharmacy"
    )
    
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    logo = models.ImageField(upload_to="pharmacies/logos/", null=True, blank=True)
    
    address = models.TextField()
    city = models.CharField(max_length=100)
    country = models.CharField(max_length=100, default="Gabon")
    
    latitude = models.FloatField()
    longitude = models.FloatField()
    
    phone = models.CharField(max_length=30)
    email = models.EmailField(blank=True)
    
    opening_time = models.TimeField()
    closing_time = models.TimeField()
    is_open_24h = models.BooleanField(default=False)
    
    is_verified = models.BooleanField(default=False)
    average_rating = models.FloatField(default=0)
    total_reviews = models.IntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Pharmacie"
        verbose_name_plural = "Pharmacies"
        ordering = ["-is_verified", "-average_rating"]


class Prescription(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    STATUS_CHOICES = (
        ("PENDING", "En attente"),
        ("APPROVED", "Approuvée"),
        ("REJECTED", "Rejetée"),
    )

    patient = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="prescriptions"
    )

    # Utilisation d'une chaîne de caractères pour éviter l'import circulaire avec orders
    order = models.ForeignKey(
        "orders.Order",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="prescription"
    )

    image = models.FileField(upload_to="prescriptions/")

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="PENDING"
    )

    reviewed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reviewed_prescriptions"
    )

    reviewed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Ordonnance de {self.patient} ({self.status})"

    class Meta:
        ordering = ["-created_at"]


class PharmacyReview(models.Model):
    patient = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="reviews"
    )

    pharmacy = models.ForeignKey(
        Pharmacy,
        on_delete=models.CASCADE,
        related_name="reviews"
    )

    rating = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )

    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.patient} → {self.pharmacy} ({self.rating}★)"

    class Meta:
        unique_together = ("patient", "pharmacy")  # Un avis par patient par pharmacie
        ordering = ("-created_at",)
        verbose_name = "Avis"
        verbose_name_plural = "Avis"