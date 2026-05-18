from django.db import models
from django.core.validators import MinValueValidator
import uuid

class Order(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    STATUS_CHOICES = (
        ("PENDING",    "En attente"),
        ("CONFIRMED",  "Confirmée"),
        ("READY",      "Prête"),
        ("DELIVERED",  "Livrée"),
        ("CANCELLED",  "Annulée"),
    )

    patient = models.ForeignKey(
        "auth_user.User",
        on_delete=models.CASCADE,
        related_name="orders"
    )

    pharmacy = models.ForeignKey(
        "pharmacies.Pharmacy",
        on_delete=models.CASCADE,
        related_name="orders"
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="PENDING"
    )

    total_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )

    note = models.TextField(blank=True, help_text="Note du patient pour la pharmacie")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-created_at",)

    def __str__(self):
        return f"Commande #{self.pk} — {self.patient} → {self.pharmacy}"

    def is_cancellable(self):
        return self.status in ("PENDING", "CONFIRMED")


class OrderItem(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name="items"
    )

    medication = models.ForeignKey(
        "medications.Medication",
        on_delete=models.CASCADE
    )

    quantity = models.PositiveIntegerField(validators=[MinValueValidator(1)])

    unit_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )

    subtotal = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )

    class Meta:
        unique_together = ("order", "medication")

    def __str__(self):
        return f"{self.quantity}× {self.medication} (commande #{self.order_id})"

    def save(self, *args, **kwargs):
        self.subtotal = self.unit_price * self.quantity
        super().save(*args, **kwargs)