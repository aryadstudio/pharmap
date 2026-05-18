from django.db import models
from auth_user.models import User
from medications.models import Medication
from django.db import models
from auth_user.models import User
import uuid

class Pharmacy(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    owner = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="pharmacy"
    )
    name         = models.CharField(max_length=255)
    description  = models.TextField(blank=True)
    logo         = models.ImageField(upload_to="pharmacies/logos/", null=True, blank=True)
    address      = models.TextField()
    city         = models.CharField(max_length=100)
    country      = models.CharField(max_length=100, default="Gabon")
    latitude     = models.FloatField()
    longitude    = models.FloatField()
    phone        = models.CharField(max_length=30)
    email        = models.EmailField(blank=True)
    opening_time = models.TimeField()
    closing_time = models.TimeField()
    is_open_24h  = models.BooleanField(default=False)
    is_verified  = models.BooleanField(default=False)
    average_rating = models.FloatField(default=0)
    total_reviews  = models.IntegerField(default=0)
    created_at   = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name
