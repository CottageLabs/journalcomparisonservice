from django import forms
from phonenumber_field.formfields import PhoneNumberField
from phonenumber_field.widgets import PhoneNumberPrefixWidget

from accounts.models import PSTFUser


class UserUpdateForm(forms.ModelForm):
    phone = PhoneNumberField(widget=PhoneNumberPrefixWidget())

    class Meta:
        model = PSTFUser
        fields = ['phone']


class ChangeUserForm(UserUpdateForm):
    email = forms.EmailField(widget=forms.EmailInput(),
                             error_messages={'unique': 'A user with this email address already exists.'})
    name = forms.CharField(widget=forms.TextInput())

    def clean_email(self):
        return self.cleaned_data['email'].lower()

    class Meta:
        model = PSTFUser
        fields = ['email', 'name', 'phone']


class UserForm(forms.Form):
    email = forms.EmailField(widget=forms.EmailInput())
