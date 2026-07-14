from django import forms
from django.contrib.auth.models import User
from accounts.models import UserProfile

class UserUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control form-control-premium', 'placeholder': 'First Name'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control form-control-premium', 'placeholder': 'Last Name'}),
            'email': forms.EmailInput(attrs={'class': 'form-control form-control-premium', 'placeholder': 'Email Address'}),
        }


class ProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['phone_number', 'profile_photo', 'mistral_api_key']
        widgets = {
            'phone_number': forms.TextInput(attrs={'class': 'form-control form-control-premium', 'placeholder': 'Phone Number'}),
            'profile_photo': forms.FileInput(attrs={'class': 'form-control form-control-premium'}),
            'mistral_api_key': forms.TextInput(attrs={
                'class': 'form-control form-control-premium',
                'placeholder': 'Enter Mistral API Key (stored securely)',
                'type': 'password'
            }),
        }
