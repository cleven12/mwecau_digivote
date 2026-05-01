from django import forms
from .models import User


class PasswordResetRequestForm(forms.Form):
    registration_number = forms.CharField(
        max_length=50,
        label="Registration Number",
        widget=forms.TextInput(attrs={
            'placeholder': 'e.g. T/DEG/2024/001',
            'autocomplete': 'username',
        }),
    )

    def get_user(self):
        """Return the User matching the registration number, or None."""
        reg_num = self.cleaned_data.get('registration_number', '').strip()
        try:
            return User.objects.get(registration_number=reg_num)
        except User.DoesNotExist:
            return None
