import datetime

from django import template
from django.template.defaultfilters import register as filter_register
from django.db.models import QuerySet
from django.utils.safestring import mark_safe
from django.conf import settings

from pstf.utils import has_group
from pstf import constants

from upload.models import UploadFile, frameworks

register = template.Library()


@filter_register.filter(name='dict_key')
def dict_key(d, k):
    """Returns the given key from a dictionary."""
    try:
        return d[k]
    except KeyError:
        return ""


@register.simple_tag
def last_year():
    return datetime.datetime.now().year - 1


@register.simple_tag
def check_framework(files: QuerySet[UploadFile]):
    last_years_files = [f for f in list(files) if f.data_year == last_year()]
    list_existing = []

    for framework in frameworks:
        if framework[0] in [f.framework for f in last_years_files]:
            list_existing.append({'framework': framework[0],
                                  'year': last_year(),
                                  'full_name': framework[1]})

    return mark_safe(list_existing)


@register.simple_tag
def settings_value(name):
    return getattr(settings, name, "")


@register.filter(name='is_institutional_user')
def is_institutional_user(user):
    return has_group(user, [constants.INSTITUTIONAL_SUPER_USER_GROUP, constants.INSTITUTIONAL_USER_GROUP])
