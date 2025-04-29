from django.db.models import CharField, Value
from django.forms.models import model_to_dict
from data.models import InformationPower, FairOpenAccessAlliance
from upload.models import UploadFile
from pstf import constants

import string
from unidecode import unidecode


def title_variants(title):
    title = title.lower()
    variants = [title]
    variants += _asciifold(title)
    variants += [x for x in [_ampersander(t) for t in variants] if x is not None]
    return list(set(variants))


def _asciifold(val):
    try:
        asciititle = unidecode(val)
    except:
        asciititle = val

    throwlist = string.punctuation + '\n\t'
    unpunctitle = "".join(c for c in val if c not in throwlist).strip()
    asciiunpunctitle = "".join(c for c in asciititle if c not in throwlist).strip()

    return [unpunctitle, asciititle, asciiunpunctitle]


def _ampersander(val):
    if " & " in val:
        return val.replace(" & ", " and ")
    if " and " in val:
        return val.replace(" and ", " & ")
    return None


def add_publisher(model_obj, framework):
    model_obj.publisher = model_obj.upload.publisher.publisher_name
    row_dict = model_to_dict(model_obj)
    row_dict['framework'] = framework.upper()

    return row_dict


def get_all_ip_data():
    """
    Query to retrieve all IP data
    """
    ip_list = []

    for row in InformationPower.objects.all():
        ip_list.append(add_publisher(row, constants.FRAMEWORK_IP))

    return ip_list


def get_all_foaa_data():
    """
    Query to retrieve all FOAA data
    """
    foaa_list = []
    for row in FairOpenAccessAlliance.objects.all():
        foaa_list.append(add_publisher(row, constants.FRAMEWORK_FOAA))

    return foaa_list


def get_ip_data_for_issn_list(issn_list):
    """
    Query to retrieve all IP data for given issn list
    """
    ip_list = []

    for row in InformationPower.objects.filter(issn__in=issn_list).all():

        ip_list.append(add_publisher(row, constants.FRAMEWORK_IP))

    return ip_list


def get_foaa_data_for_issn_list(issn_list):
    """
    Query to retrieve all FOAA data for given issn list
    """

    foaa_list = []
    for row in FairOpenAccessAlliance.objects.filter(issn__in=issn_list).all():

        foaa_list.append(add_publisher(row, constants.FRAMEWORK_FOAA))

    return foaa_list


def get_ip_data_for_issn_dict(issn_dict_list):
    """
    Query to retrieve all IP data for given issn dict list
    """
    ip_list = []
    for item in issn_dict_list:
        rows = []
        for row in InformationPower.objects.filter(issn=item['issn'], year=item['year']).all():
            rows.append(add_publisher(row, constants.FRAMEWORK_IP))
        ip_list.extend(rows)
    return ip_list


def get_foaa_data_for_issn_dict(issn_dict_list):
    """
    Query to retrieve all FOAA data for given issn list
    """
    foaa_list = []
    for item in issn_dict_list:
        rows = []
        for row in FairOpenAccessAlliance.objects.filter(issn=item['issn'], year=item['year']).all():
            rows.append(add_publisher(row, constants.FRAMEWORK_FOAA))
        foaa_list.extend(rows)
    return foaa_list
