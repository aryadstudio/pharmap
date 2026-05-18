from django.db import models
import uuid
# Create your models here.
class Prescription(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    STATUS_CHOICES = (
        ("PENDING", "Pending"),
        ("APPROVED", "Approved"),
        ("REJECTED", "Rejected"),
    )

    patient = models.ForeignKey(
        "auth_user.User",
        on_delete=models.CASCADE,
        related_name="prescriptions"
    )

    order = models.ForeignKey(
        "orders.Order",
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    image = models.FileField(
        upload_to="prescriptions/"
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="PENDING"
    )

    reviewed_by = models.ForeignKey(
        "auth_user.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reviewed_prescriptions"
    )

    reviewed_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)