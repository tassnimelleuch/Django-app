"""Forms for contact and phone number management in the accounts app."""
from django import forms
from .models import Contact, PhoneNumber


class ContactForm(forms.ModelForm):
    """Form for creating and editing contacts."""
    class Meta:
        """Form metadata for ContactForm."""
        model = Contact
        fields = ['first_name', 'last_name', 'email', 'linkedin']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'linkedin': forms.URLInput(attrs={'class': 'form-control'}),
        }


class PhoneNumberForm(forms.ModelForm):
    """Form for creating and editing phone numbers."""
    class Meta:
        """Form metadata for PhoneNumberForm."""
        model = PhoneNumber
        fields = ['phone_type', 'number']
        widgets = {
            'phone_type': forms.Select(attrs={'class': 'form-control'}),
            'number': forms.TextInput(attrs={'class': 'form-control'}),
        }
