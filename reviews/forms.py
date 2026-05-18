from django import forms
from django.core.exceptions import ValidationError
from .models import PharmacyReview


class PharmacyReviewForm(forms.ModelForm):

    class Meta:
        model = PharmacyReview
        fields = ["patient", "pharmacy", "rating", "comment"]

        widgets = {
            "patient": forms.Select(attrs={"class": "form-select"}),
            "pharmacy": forms.Select(attrs={"class": "form-select"}),
            "rating": forms.NumberInput(attrs={
                "class": "form-control",
                "min": 1,
                "max": 5,
            }),
            "comment": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 4,
                "placeholder": "Laissez un commentaire (optionnel)..."
            }),
        }

    def clean_rating(self):
        rating = self.cleaned_data.get("rating")
        if rating is not None and not (1 <= rating <= 5):
            raise ValidationError("La note doit être comprise entre 1 et 5.")
        return rating