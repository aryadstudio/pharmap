from django import forms
from .models import Payment


class PaymentForm(forms.ModelForm):

    class Meta:
        model = Payment
        fields = (
            "method",
            "amount",
            "transaction_id",
        )

        widgets = {
            "method": forms.Select(attrs={
                "class": "form-select"
            }),

            "amount": forms.NumberInput(attrs={
                "class": "form-control",
                "placeholder": "Montant"
            }),

            "transaction_id": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "ID de transaction"
            }),
        }

    def clean_amount(self):
        amount = self.cleaned_data.get("amount")

        if amount <= 0:
            raise forms.ValidationError(
                "Le montant doit être supérieur à 0."
            )

        return amount