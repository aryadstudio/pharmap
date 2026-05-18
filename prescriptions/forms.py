# forms.py

from django import forms
from .models import Prescription


class PrescriptionForm(forms.ModelForm):

    class Meta:
        model = Prescription
        fields = (
            "patient",
            "order",
            "image",
            "status",
            "reviewed_by",
            "reviewed_at",
        )

        widgets = {
            "patient": forms.Select(attrs={
                "class": "form-select"
            }),

            "order": forms.Select(attrs={
                "class": "form-select"
            }),

            "image": forms.ClearableFileInput(attrs={
                "class": "form-control"
            }),

            "status": forms.Select(attrs={
                "class": "form-select"
            }),

            "reviewed_by": forms.Select(attrs={
                "class": "form-select"
            }),

            "reviewed_at": forms.DateTimeInput(attrs={
                "type": "datetime-local",
                "class": "form-control"
            }),
        }

    def clean_image(self):
        image = self.cleaned_data.get("image")

        if image:
            allowed_extensions = [".jpg", ".jpeg", ".png", ".pdf"]

            import os
            ext = os.path.splitext(image.name)[1].lower()

            if ext not in allowed_extensions:
                raise forms.ValidationError(
                    "Formats autorisés : JPG, JPEG, PNG, PDF."
                )

            if image.size > 5 * 1024 * 1024:
                raise forms.ValidationError(
                    "La taille maximale autorisée est de 5 MB."
                )

        return image