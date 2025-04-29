from django import forms
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from django.utils.translation import gettext_lazy as _
from phonenumber_field.formfields import PhoneNumberField
from phonenumber_field.widgets import PhoneNumberPrefixWidget

from .models import PSTFUser, PublisherAccount, EndUserAccount


class AddPSTFUserForm(forms.ModelForm):
    """A form for adding users"""

    def __init__(self, *args, **kwargs):
        super(AddPSTFUserForm, self).__init__(*args, **kwargs)
        # make user group field required
        self.fields['groups'].required = True

    phone = PhoneNumberField(widget=PhoneNumberPrefixWidget())

    class Meta:
        model = PSTFUser
        fields = ('publisher', 'organisation', 'email', 'name')


class ChangePSTFUserForm(forms.ModelForm):
    """A form for updating users."""
    phone = PhoneNumberField(widget=PhoneNumberPrefixWidget())

    class Meta:
        model = PSTFUser
        fields = ('email', 'name', 'is_active', 'is_active', 'publisher', 'organisation', 'review_status')


class PSTFUserAdmin(BaseUserAdmin):
    # The forms to add and change user instances
    form = ChangePSTFUserForm
    add_form = AddPSTFUserForm

    # The fields to be used in displaying the User model.
    # These override the definitions on the base UserAdmin
    # that reference specific fields on auth.User.
    list_display = ('email', 'publisher', 'organisation', 'user_type', 'created', 'state', 'review_status',
                    'rejected', 'is_superuser', 'is_active')
    readonly_fields = ('state', 'last_login', 'created')
    list_filter = ('is_superuser',)
    fieldsets = (

        (None, {'fields': (('last_login',), ('created',))}),
        (None, {'fields': ('state', 'review_status', 'rejected', 'publisher', 'organisation', 'name', 'email',
                           'phone')}),
        (_('Permissions'), {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'), }),

    )
    # add_fieldsets is not a standard ModelAdmin attribute. UserAdmin
    # overrides get_fieldsets to use this attribute when creating a user.
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('publisher', 'organisation', 'email', 'name', 'phone', 'is_active', 'groups',
                       'user_permissions'),

        }),
    )

    search_fields = ('email',)
    ordering = ('email',)
    filter_horizontal = ('user_permissions',)

    def user_type(self, obj):
        """
        Display user group name
        """
        if obj.groups.exists():
            return obj.groups.first().name



class PublisherAccountAdmin(admin.ModelAdmin):
    list_display = ('publisher_name', 'created', 'verified')


class EndUserAccountAdmin(admin.ModelAdmin):
    list_display = ('organisation_name', 'created', 'verified')


admin.site.register(PSTFUser, PSTFUserAdmin)
admin.site.register(PublisherAccount, PublisherAccountAdmin)
admin.site.register(EndUserAccount, EndUserAccountAdmin)
