# forms.py

from django import forms
from .models import Notification


class NotificationForm(forms.ModelForm):

    class Meta:
        model = Notification
        fields = (
            "user",
            "title",
            "message",
            "notification_type",
            "is_read",
        )

        widgets = {
            "user": forms.Select(attrs={
                "class": "form-select"
            }),

            "title": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Titre de la notification"
            }),

            "message": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 4,
                "placeholder": "Message de la notification"
            }),

            "notification_type": forms.Select(attrs={
                "class": "form-select"
            }),

            "is_read": forms.CheckboxInput(attrs={
                "class": "form-check-input"
            }),
        }

    def clean_title(self):
        title = self.cleaned_data.get("title")

        if len(title) < 3:
            raise forms.ValidationError(
                "Le titre est trop court."
            )

        return title

    def clean_message(self):
        message = self.cleaned_data.get("message")

        if len(message) < 5:
            raise forms.ValidationError(
                "Le message est trop court."
            )

        return message