from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import Profile, Order,  PaymentNumber, ReqMoneyBack, PaymentWindow


class UserRegisterForm(UserCreationForm):
    email = forms.EmailField()

    class Meta:
        model = User
        fields = [
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
            "image",
        ]

#    def __init__(self, *args, **kwargs):
#        super(ProfileUpdateForm, self).__init__(*args, **kwargs)
#        for i in PaymentWindow.objects.all():
#            self.fields[i.name] = forms.IntegerField()


class PaymentNumForm(forms.ModelForm):
    class Meta:
        model = PaymentNumber
        fields = [
            "num"
        ]
        labels ={"num":False}


class AmountWithdrawForm(forms.ModelForm):
    payment_method = forms.ChoiceField(required=True, widget=forms.RadioSelect)

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("inst", None)
        super(AmountWithdrawForm, self).__init__(*args, **kwargs)
        self.fields["payment_method"].choices = ((i.pk,i.name) for i in self.user.profile.payment_options.all()
                                                 if self.user.profile.paymentnumber_set.get(payment_window=i).num)

    class Meta:
        model = ReqMoneyBack
        fields = [
            "amount"
        ]


class AmountDepositForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = [
            "amount"
        ]
