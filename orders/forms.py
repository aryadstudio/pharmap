from django import forms
from .models import Order, OrderItem

class OrderForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ["pharmacy", "note"]
        widgets = {
            "pharmacy": forms.Select(attrs={"class": "form-select", "disabled": True}), # Souvent pré-sélectionné
            "note": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 3,
                "placeholder": "Instructions particulières pour la pharmacie (optionnel)…"
            }),
        }

class OrderItemForm(forms.ModelForm):
    class Meta:
        model = OrderItem
        fields = ["medication", "quantity"]
        widgets = {
            "medication": forms.Select(attrs={"class": "form-select"}),
            "quantity": forms.NumberInput(attrs={
                "class": "form-control",
                "min": 1,
                "placeholder": "Qté"
            }),
        }

# Formset pour gérer plusieurs médicaments dans une seule commande
OrderItemFormSet = forms.inlineformset_factory(
    Order,
    OrderItem,
    form=OrderItemForm,
    fields=["medication", "quantity"],
    extra=1,          # Nombre de lignes vides supplémentaires
    min_num=1,        # Au moins une ligne requise
    validate_min=True,
    can_delete=True,  # Permet de supprimer une ligne ajoutée par erreur
)

class OrderStatusForm(forms.ModelForm):
    """Formulaire léger pour changer uniquement le statut (usage pharmacien)."""
    class Meta:
        model = Order
        fields = ["status"]
        widgets = {
            "status": forms.Select(attrs={"class": "form-select"})
        }