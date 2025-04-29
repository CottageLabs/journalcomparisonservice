import pycountry
from django.utils.translation import gettext as _
from django import forms
from accounts import models
from phonenumber_field.formfields import PhoneNumberField
from phonenumber_field.widgets import PhoneNumberPrefixWidget


class InsSelfRegisterForm(forms.Form):
    organisation_name = forms.CharField(widget=forms.TextInput(
        attrs={
            "placeholder": _("Organisation Name"),
            'size': '50'
        }
    ), required=True)

    email = forms.EmailField(widget=forms.EmailInput(
        attrs={"placeholder": _("Email"),
               "class": "form-control"}))

    phone = PhoneNumberField(widget=PhoneNumberPrefixWidget())


class EndUserAccount(forms.ModelForm):

    countries = [(c.alpha_3, c.name) for c in list(pycountry.countries)]
    countries.sort(key=lambda e: e[1])

    country = forms.ChoiceField(choices=[('', '---------')] + countries)

    postal_address2 = forms.CharField(required=False)
    postal_address3 = forms.CharField(required=False)

    organisation_type = forms.ChoiceField(
        choices=models.OrganisationType.choices,
        widget=forms.RadioSelect())

    class Meta:
        model = models.EndUserAccount
        fields = '__all__'
        exclude = ['verified', 'created']


class EndUserAccountReadonly(EndUserAccount):
    def __init__(self, *args, **kwargs):
        super(EndUserAccountReadonly, self).__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].widget.attrs['disabled'] = True

    class Meta:
        model = models.PublisherAccount
        fields = '__all__'