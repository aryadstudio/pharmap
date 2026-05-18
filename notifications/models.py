from django.db import models
import uuid
# Create your models here.
class Notification(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    TYPE_CHOICES = (
        ("ORDER", "Order"),
        ("STOCK", "Stock"),
        ("PAYMENT", "Payment"),
        ("SYSTEM", "System"),
    )

    user = models.ForeignKey(
        "auth_user.User",
        on_delete=models.CASCADE,
        related_name="notifications"
    )

    title = models.CharField(max_length=255)

    message = models.TextField()

    notification_type = models.CharField(
        max_length=30,
        choices=TYPE_CHOICES
    )

    is_read = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)