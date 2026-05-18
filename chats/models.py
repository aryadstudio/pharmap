from django.db import models
import uuid
# Create your models here.
class Conversation(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    patient = models.ForeignKey(
        "auth_user.User",
        on_delete=models.CASCADE,
        related_name="patient_conversations"
    )

    pharmacy = models.ForeignKey(
        "pharmacies.Pharmacy",
        on_delete=models.CASCADE,
        related_name="conversations"
    )

    created_at = models.DateTimeField(auto_now_add=True)


class Message(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    conversation = models.ForeignKey(
        Conversation,
        on_delete=models.CASCADE,
        related_name="messages"
    )

    sender = models.ForeignKey(
        "auth_user.User",
        on_delete=models.CASCADE
    )

    content = models.TextField()

    is_read = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

class FavoriteMedication(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    patient = models.ForeignKey(
        "auth_user.User",
        on_delete=models.CASCADE,
        related_name="favorites"
    )

    medication = models.ForeignKey(
        "medications.Medication",
        on_delete=models.CASCADE
    )

    created_at = models.DateTimeField(auto_now_add=True)