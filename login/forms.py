from django import forms


class LoginForm(forms.Form):
    email = forms.EmailField(
        widget=forms.EmailInput(
        ))


class OTPForm(forms.Form):
    otp = forms.CharField(
        widget=forms.TextInput(
            attrs={
                'placeholder': 'OTP',
                'size': '10',
                'inputmode': 'numeric'
            }
        ))

