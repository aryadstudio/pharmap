from django import forms
from django.contrib.auth.forms import UserChangeForm, PasswordChangeForm
from auth_user.models import User


class PatientProfileForm(UserChangeForm):
    """
    Formulaire de modification de profil pour les patients.
    N'affiche pas le champ 'password' car géré séparément.
    """
    # Champs personnalisés à afficher (optionnel, pour réorganiser l'ordre)
    first_name = forms.CharField(
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Prénom'
        })
    )
    last_name = forms.CharField(
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Nom'
        })
    )
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Adresse email'
        })
    )
    phone = forms.CharField(
        max_length=15,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Numéro de téléphone (ex: 699000000)'
        })
    )
    address = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'placeholder': 'Adresse postale complète',
            'rows': 3
        })
    )
    
    # Si vous avez un champ avatar/image dans votre modèle User
    # Décommentez la ligne ci-dessous si le champ existe
    # avatar = forms.ImageField(required=False, widget=forms.FileInput(attrs={'class': 'form-control'}))

    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email', 'phone', 'address')
        # Si vous avez un champ avatar, ajoutez-le ici : ('...', 'avatar')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # On retire le mot de passe du formulaire de profil classique
        if 'password' in self.fields:
            del self.fields['password']
        
        # Personnalisation supplémentaire des widgets si nécessaire
        # Exemple : ajouter des classes CSS bootstrap ou personnalisées
        for field_name, field in self.fields.items():
            if 'class' not in field.widget.attrs:
                field.widget.attrs['class'] = 'form-control'


class PatientPasswordChangeForm(PasswordChangeForm):
    """
    Formulaire de changement de mot de passe sécurisé.
    Hérite de PasswordChangeForm de Django qui gère déjà :
    1. La vérification de l'ancien mot de passe.
    2. Les validations de complexité du nouveau mot de passe.
    """
    
    old_password = forms.CharField(
        label="Mot de passe actuel",
        strip=False,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Entrez votre mot de passe actuel',
            'autocomplete': 'current-password'
        })
    )
    
    new_password1 = forms.CharField(
        label="Nouveau mot de passe",
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Nouveau mot de passe',
            'autocomplete': 'new-password'
        }),
        strip=False,
        help_text="Au moins 8 caractères. Évitez les mots de passe trop courants."
    )
    
    new_password2 = forms.CharField(
        label="Confirmation du nouveau mot de passe",
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Confirmez le nouveau mot de passe',
            'autocomplete': 'new-password'
        }),
        strip=False,
        help_text="Re-saisissez le nouveau mot de passe pour vérification."
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Ajustement des labels et aides si nécessaire pour correspondre à votre design
        self.fields['old_password'].label = "Mot de passe actuel"
        self.fields['new_password1'].label = "Nouveau mot de passe"
        self.fields['new_password2'].label = "Confirmer le nouveau mot de passe"