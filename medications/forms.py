from django import forms
from .models import (
    MedicationCategory,
    Medication,
    PharmacyMedication,
    StockHistory
)


class MedicationCategoryForm(forms.ModelForm):

    class Meta:
        model = MedicationCategory
        fields = ["name", "slug"]

        widgets = {
            "name": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Nom de la catégorie"
            }),
            "slug": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "slug-unique"
            }),
        }


class MedicationForm(forms.ModelForm):

    class Meta:
        model = Medication
        fields = [
            "category",
            "name",
            "description",
            "manufacturer",
            "requires_prescription",
            "is_rare",
            "image"
        ]

        widgets = {
            "category": forms.Select(attrs={"class": "form-select"}),
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "description": forms.Textarea(attrs={"class": "form-control", "rows": 4}),
            "manufacturer": forms.TextInput(attrs={"class": "form-control"}),
            "requires_prescription": forms.CheckboxInput(),
            "is_rare": forms.CheckboxInput(),
        }


class PharmacyMedicationForm(forms.ModelForm):

    class Meta:
        model = PharmacyMedication
        fields = ["pharmacy", "medication", "quantity", "price", "is_available"]

        widgets = {
            "pharmacy": forms.Select(attrs={"class": "form-select"}),
            "medication": forms.Select(attrs={"class": "form-select"}),
            "quantity": forms.NumberInput(attrs={"class": "form-control"}),
            "price": forms.NumberInput(attrs={"class": "form-control"}),
            "is_available": forms.CheckboxInput(),
        }


class StockHistoryForm(forms.ModelForm):

    class Meta:
        model = StockHistory
        fields = ["pharmacy_medication", "previous_quantity", "new_quantity", "reason"]

        widgets = {
            "pharmacy_medication": forms.Select(attrs={"class": "form-select"}),
            "previous_quantity": forms.NumberInput(attrs={"class": "form-control"}),
            "new_quantity": forms.NumberInput(attrs={"class": "form-control"}),
            "reason": forms.TextInput(attrs={"class": "form-control"}),
        }