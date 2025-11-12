from django import forms
from django.contrib.auth.forms import AuthenticationForm
from .models import TwoWheelerEntry, FourWheelerEntry

class LoginForm(AuthenticationForm):
    username = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter username',
            'required': True
        })
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter password',
            'required': True
        })
    )

class TwoWheelerEntryForm(forms.ModelForm):
    class Meta:
        model = TwoWheelerEntry
        fields = ['vehicle_no', 'phone_number']  # Include phone_number
        
        widgets = {
            'vehicle_no': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter vehicle number',
                'required': True
            }),
            'phone_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter phone number (optional)',
                'required': False
            }),
        }

class FourWheelerEntryForm(forms.ModelForm):
    class Meta:
        model = FourWheelerEntry
        fields = ['vehicle_no', 'phone_number']  # Include phone_number
        
        widgets = {
            'vehicle_no': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter vehicle number',
                'required': True
            }),
            'phone_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter phone number (optional)',
                'required': False
            }),
        }