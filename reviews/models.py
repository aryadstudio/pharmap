from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator


class PharmacyReview(models.Model):

    patient = models.ForeignKey(
        "auth_user.User",
        on_delete=models.CASCADE,
        related_name="reviews"
    )

    pharmacy = models.ForeignKey(
        "pharmacies.Pharmacy",
        on_delete=models.CASCADE,
        related_name="reviews"
    )

    rating = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )

    comment = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("patient", "pharmacy")  # un avis par patient par pharmacie
        ordering = ("-created_at",)

    def __str__(self):
        return f"{self.patient} → {self.pharmacy} ({self.rating}★)"