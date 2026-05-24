import uuid
from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    ROLE_CHOICES = (
        ("PATIENT", "Patient"),
        ("PHARMACIST", "Pharmacien"),
        ("ADMIN", "Administrateur"),
    )

    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default="PATIENT")
    phone = models.CharField(max_length=30, unique=True)
    profile_picture = models.ImageField(upload_to="users/profiles/", null=True, blank=True)
    is_verified = models.BooleanField(default=False)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"

    @property
    def is_patient(self):
        return self.role == "PATIENT"

    @property
    def is_pharmacist(self):
        return self.role == "PHARMACIST"

    @property
    def is_admin(self):
        return self.role == "ADMIN"