from django import forms
from .models import Pharmacy


class PharmacyForm(forms.ModelForm):
    class Meta:
        model = Pharmacy
        fields = [
            "owner",
            "name",
            "description",
            "logo",
            "address",
            "city",
            "country",
            "latitude",
            "longitude",
            "phone",
            "email",
            "opening_time",
            "closing_time",
            "is_open_24h",
            "is_verified",
        ]

        widgets = {
            "description": forms.Textarea(attrs={"rows": 4}),
            "address": forms.Textarea(attrs={"rows": 3}),
            "opening_time": forms.TimeInput(format="%H:%M", attrs={"type": "time"}),
            "closing_time": forms.TimeInput(format="%H:%M", attrs={"type": "time"}),
        }