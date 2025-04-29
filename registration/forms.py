import pycountry
from django.utils.translation import gettext as _
from django import forms
from phonenumber_field.formfields import PhoneNumberField
from phonenumber_field.widgets import PhoneNumberPrefixWidget

from accounts import models
from accounts.models import ServicesModel, TradeBodiesModel
from pstf import constants
from pstf.utils import validate_issn


class SelfRegisterForm(forms.Form):
    publisher_name = forms.CharField(widget=forms.TextInput(
        attrs={
            "placeholder": _("Publisher Name"),
            'size': '10'
        }
    ), required=True)
    email = forms.EmailField(widget=forms.EmailInput(
        attrs={"placeholder": _("Email"),
               "class": "form-control"}))

    phone = PhoneNumberField(widget=PhoneNumberPrefixWidget())


class ModelMultipleChoiceRegistrationField(forms.ModelMultipleChoiceField):
    def label_from_instance(self, obj):
        return obj.name


class RegistrationCheckbox(forms.CheckboxSelectMultiple):
    def create_option(self, name, value, label, selected, index, subindex=None, attrs=None):
        option = super().create_option(name, value, label, selected, index, subindex, attrs)
        if value:
            option['attrs']['data-abbreviation'] = value.instance.abbreviation
        return option


class PublisherAccount(forms.ModelForm):

    def clean_issn(self):
        issn = self.cleaned_data['issn']

        if not validate_issn(issn):
            self.add_error('issn', constants.ISSN_FORM_ERROR)

        return issn

    def clean_services(self):
        services = self.cleaned_data['services']
        selected_services = [s.abbreviation for s in services]

        if 'INASP' in selected_services and 'inasp_journals' not in self.data:
            self.add_error('inasp_journals', constants.INASP_FORM_ERROR)

        if 'Other' in selected_services and 'services_other' in self.data\
                and str(self.data['services_other']).strip() == '':
            self.add_error('services', constants.NO_OTHER_SERVICE)

        return services

    def clean_trade_bodies(self):
        trade_bodies = self.cleaned_data['trade_bodies']
        selected_trade_bodies = [s.abbreviation for s in trade_bodies]

        if 'member_of_publisher_trade_body' in self.cleaned_data and\
                self.cleaned_data['member_of_publisher_trade_body'] != 'False' and \
                len(trade_bodies) == 0:
            self.add_error('trade_bodies', constants.NO_TRADE_BODIES)

        if 'Other' in selected_trade_bodies and 'trade_bodies_other' in self.data\
                and str(self.data['trade_bodies_other']).strip() == '':
            self.add_error('trade_bodies', constants.NO_OTHER_TRADE_BODY)

        return trade_bodies

    countries = [(c.alpha_3, c.name) for c in list(pycountry.countries)]
    countries.sort(key=lambda e: e[1])

    country = forms.ChoiceField(choices=[('', '---------')] + countries)

    services = ModelMultipleChoiceRegistrationField(
        queryset=ServicesModel.objects.all(),
        widget=RegistrationCheckbox(attrs={
            'onchange': "checkOther(this);",
        }))

    services_other = forms.CharField(required=False)

    inasp_journals = forms.ChoiceField(
        choices=models.JournalOnline.choices,
        widget=forms.RadioSelect(), required=False)

    trade_bodies = ModelMultipleChoiceRegistrationField(
        queryset=TradeBodiesModel.objects.all(),
        widget=RegistrationCheckbox(attrs={
            'onchange': "checkOther(this);",
        }), required=False)

    trade_bodies_other = forms.CharField(required=False)

    member_of_cope = forms.ChoiceField(
        choices=[("True", "Yes"), ("False", "No")],
        widget=forms.RadioSelect)

    member_of_publisher_trade_body = forms.ChoiceField(
        choices=[("True", "Yes"), ("False", "No")],
        widget=forms.RadioSelect(attrs={
            'onchange': "checkTradeBodies(this);",
        }))

    postal_address2 = forms.CharField(required=False)
    postal_address3 = forms.CharField(required=False)

    class Meta:
        model = models.PublisherAccount
        fields = '__all__'
        exclude = ['verified', 'created']


class PublisherAccountReadonly(PublisherAccount):
    def __init__(self, *args, **kwargs):
        super(PublisherAccountReadonly, self).__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].widget.attrs['disabled'] = True

    class Meta:
        model = models.PublisherAccount
        fields = '__all__'


class UserForm(forms.ModelForm):

    class Meta:
        model = models.PSTFUser
        fields = ['title', 'name']


class PublisherVerification(forms.ModelForm):
    class Meta:
        model = models.PublisherAccount
        fields = ['postal_address1', 'postal_address2', 'postal_address3',
                  'postcode', 'city', 'country']


class PublisherLinkRegistrationForm(forms.Form):
    title = forms.CharField(required=False)

    name = forms.CharField(
        widget=forms.TextInput(
            attrs={
                "placeholder": _("Full Name"),
                'size': '40'
            }
        ), required=True)

    email = forms.EmailField(widget=forms.EmailInput(
        attrs={"placeholder": _("Email")}))

    phone = PhoneNumberField(widget=PhoneNumberPrefixWidget())
