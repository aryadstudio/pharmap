from django import forms
from .models import Payment

class PaymentForm(forms.ModelForm):
    """
    Formulaire de paiement adaptatif.
    - Cache les champs inutiles selon la méthode (ex: transaction_id pour CASH).
    - Valide le montant.
    """

    class Meta:
        model = Payment
        fields = ("method", "amount", "transaction_id")
        widgets = {
            "method": forms.Select(attrs={
                "class": "form-select",
                "id": "paymentMethodSelect", # ID pour le JS si besoin
                "style": "font-weight: 600;"
            }),
            "amount": forms.NumberInput(attrs={
                "class": "form-control",
                "placeholder": "Montant en FCFA",
                "readonly": True, # Souvent le montant vient de la commande, donc non modifiable
                "step": "100"
            }),
            "transaction_id": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Référence de transaction (automatique pour CB/Mobile)",
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Si l'instance existe déjà (édition admin), on ajuste les attributs
        if self.instance and self.instance.pk:
            if self.instance.method == "CASH":
                self.fields['transaction_id'].required = False
                self.fields['transaction_id'].widget.attrs['placeholder'] = "Non applicable pour le paiement cash"
            
            # Rend le montant en lecture seule s'il est déjà défini par la commande
            if self.instance.amount:
                self.fields['amount'].widget.attrs['readonly'] = True

    def clean_amount(self):
        amount = self.cleaned_data.get("amount")
        if amount is not None and amount <= 0:
            raise forms.ValidationError("Le montant doit être supérieur à 0.")
        return amount

    def clean_transaction_id(self):
        transaction_id = self.cleaned_data.get("transaction_id")
        method = self.cleaned_data.get("method")

        # Pour le cash, la transaction ID n'est pas requise lors de la création
        if method == "CASH" and not transaction_id:
            return ""
        
        # Pour les autres méthodes, on pourrait vouloir vérifier le format si nécessaire
        return transaction_id