from django import forms
from .models import Pharmacy, Prescription, PharmacyReview
import re

class PharmacyForm(forms.ModelForm):
    """Formulaire pour créer ou modifier une pharmacie."""
    class Meta:
        model = Pharmacy
        fields = [
            'name', 'description', 'logo', 'address', 'city', 'country',
            'phone', 'email', 'opening_time', 'closing_time', 'is_open_24h'
        ]
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control', 
                'placeholder': 'Ex: Pharmacie du Centre'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control', 
                'rows': 4, 
                'placeholder': 'Description de votre établissement...'
            }),
            'logo': forms.FileInput(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={
                'class': 'form-control', 
                'rows': 2,
                'placeholder': 'Adresse complète'
            }),
            'city': forms.TextInput(attrs={'class': 'form-control'}),
            'country': forms.TextInput(attrs={'class': 'form-control', 'value': 'Gabon'}),
            'phone': forms.TextInput(attrs={
                'class': 'form-control', 
                'placeholder': '+241 06 00 00 00'
            }),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'opening_time': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'closing_time': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'is_open_24h': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def clean_phone(self):
        phone = self.cleaned_data.get('phone')
        # Nettoyage simple : retire espaces et tirets
        clean_phone = re.sub(r'\s|-', '', phone)
        if not re.match(r'^\+?\d{8,15}$', clean_phone):
            raise forms.ValidationError("Numéro de téléphone invalide. Format attendu : +241...")
        return clean_phone

class PrescriptionForm(forms.ModelForm):
    """Formulaire pour uploader une ordonnance."""
    class Meta:
        model = Prescription
        fields = ['image']
        widgets = {
            'image': forms.FileInput(attrs={
                'class': 'form-control', 
                'accept': 'image/*,.pdf'
            })
        }

class PharmacyReviewForm(forms.ModelForm):
    """Formulaire pour laisser un avis."""
    class Meta:
        model = PharmacyReview
        fields = ['rating', 'comment']
        widgets = {
            'rating': forms.NumberInput(attrs={
                'min': 1, 
                'max': 5, 
                'class': 'form-control',
                'step': 1
            }),
            'comment': forms.Textarea(attrs={
                'class': 'form-control', 
                'rows': 3, 
                'placeholder': 'Partagez votre expérience...'
            })
        }

    def clean_rating(self):
        rating = self.cleaned_data.get('rating')
        if rating < 1 or rating > 5:
            raise forms.ValidationError("La note doit être comprise entre 1 et 5.")
        return rating