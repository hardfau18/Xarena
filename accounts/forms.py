from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import Profile, Order

class UserRegisterForm(UserCreationForm):
    email = forms.EmailField()

    class Meta:
        model = User
        fields =[
            "username",
            "email",
            "password1",
            "password2"
        ]


class UserUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = [
            "username"
        ]


class ProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = [
            "account_number",
            "image"
        ]


class AmountTransfer(forms.ModelForm):
    class Meta:
        model = Order
        fields = [
            "amount"
        ]

