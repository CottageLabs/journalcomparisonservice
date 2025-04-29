import os
import shutil
import csv

from django.db.models import Q
from django.shortcuts import render
from django.http import FileResponse

from accounts import models
from pstf import constants
from pstf.decorators import user_group
import pycountry


def total_publishers():
    return models.PublisherAccount.objects.all()


def total_institutions():
    return models.EndUserAccount.objects.all()


def users_count(group):
    return models.PSTFUser.objects.filter(group)


def publisher_admin_users():
    group = Q(groups__name=constants.SUPER_PUBLISHER_GROUP)
    return users_count(group)


def publisher_users():
    group = Q(groups__name=constants.PUBLISHER_GROUP)
    return users_count(group)


def institutional_admin_users():
    group = Q(groups__name=constants.INSTITUTIONAL_SUPER_USER_GROUP)
    return users_count(group)


def institutional_users():
    group = Q(groups__name=constants.INSTITUTIONAL_USER_GROUP)
    return users_count(group)


def publisher_admin_users_count(publishers):
    count = 0
    for publisher in list(publishers):
        count += publisher_admin_users().filter(publisher=publisher).count()
    return count


def publisher_users_count(publishers):
    count = 0
    for publisher in list(publishers):
        count += publisher_users().filter(publisher=publisher).count()
    return count


def ins_admin_users_count(organisations):
    count = 0
    for organisation in list(organisations):
        count += institutional_admin_users().filter(organisation=organisation).count()
    return count


def ins_users_count(organisations):
    count = 0
    for organisation in list(organisations):
        count += institutional_users().filter(organisation=organisation).count()
    return count


def country_filter(query, country):
    return query.filter(country=country)


def countries_list_of_publishers():
    return total_publishers().values_list('country', flat=True).distinct()


def countries_list_of_institutions():
    return total_institutions().values_list('country', flat=True).distinct()


def users_data():
    publishers = "publishers"
    institutions = "institutions"
    pub_super_users = "pub_super_users"
    pub_users = "pub_users"
    ins_supers_users = "ins_supers_users"
    ins_users = "ins_users"
    data = {}
    total_pub_admin_count = publisher_admin_users().count()
    total_ins_admin_count = institutional_admin_users().count()
    all_data = {publishers: total_publishers().count(),
                institutions: total_institutions().count(),
                pub_super_users: total_pub_admin_count,
                pub_users: publisher_users().count() + total_pub_admin_count,
                ins_supers_users: total_ins_admin_count,
                ins_users: institutional_users().count() + total_ins_admin_count
                }

    for country in countries_list_of_publishers():
        country_name = pycountry.countries.get(alpha_3=country).name

        pub_admin_count = publisher_admin_users_count(country_filter(total_publishers(), country))
        ins_admin_count = ins_admin_users_count(country_filter(total_institutions(), country))
        data[country_name] = {publishers: country_filter(total_publishers(), country).count(),
                         institutions: country_filter(total_institutions(), country).count(),
                         pub_super_users: pub_admin_count,
                         pub_users: publisher_users_count(country_filter(total_publishers(), country)) +
                                    pub_admin_count,
                         ins_supers_users: ins_admin_count,
                         ins_users: ins_users_count(country_filter(total_institutions(), country)) + ins_admin_count
                         }
    # Some of the countries may not be there is the Publisher's accounts which are there in Organization data
    # Retrieve the remaining  countries
    for country in countries_list_of_institutions():
        country_name = pycountry.countries.get(alpha_3=country).name

        #  skip countries which are added already
        if country_name in data:
            pass
        else:
            ins_admin_count = ins_admin_users_count(country_filter(total_institutions(), country))
            data[country_name] = {publishers: 0, pub_super_users: 0, pub_users: 0}
            data[country_name][institutions] = country_filter(total_institutions(), country).count()
            data[country_name][ins_supers_users] = ins_admin_count
            data[country_name][ins_users] = ins_users_count(country_filter(total_institutions(), country)) + ins_admin_count

    # Sort the data by country names
    sorted_data = {k: v for k, v in sorted(data.items())}
    sorted_data["All"] = all_data

    return sorted_data


def get_users_report_as_list():
    report = []
    for k, v in  users_data().items():
        row_data = {"country":k}
        row_data.update(v)
        report.append(row_data)

    return report


@user_group(constants.COALITION_S_GROUP)
def user_reports(request):
    template = "coalitions/user_reports.html"
    context = {'role': constants.COALITION_S_GROUP,
               'data': users_data()}
    return render(request, template, context)


@user_group(constants.COALITION_S_GROUP)
def download_user_reports(request):
    export_data = ExportData(request.user.id)
    export_data.write_data_to_csv(get_users_report_as_list())
    file_path = export_data.get_file_path()

    file_to_download = open(file_path, 'rb')
    response = FileResponse(file_to_download, content_type='application/force-download')
    response['Content-Disposition'] = 'inline; filename=' + ExportData.CSV_FILE
    return response


class ExportData:
    """
    Class to create users report csv file
    """
    # Fields contains the information of the fields for the CSV file header
    FIELDS = ['country', 'publishers', 'pub_users', 'pub_super_users', 'institutions','ins_users', 'ins_supers_users']

    HEADER_ROW = {'country': 'Country', 'publishers': 'Total Publishers', 'institutions': 'Total Institutions',
               'pub_super_users': 'Of which Publisher Super Users', 'pub_users': 'Publisher Users',
               'ins_supers_users': 'Of which Institutional Super Users', 'ins_users': 'Institutional Users'}

    CSV_FILE = 'users_report.csv'

    def __init__(self, user_id=None):
        self.csv_file_path = None
        self.user_id = user_id
        self.create_temp_dir_path()

    def create_temp_dir_path(self):
        user_id = self.user_id
        tmp_dir_name = str(user_id) + "_users_report"
        tmp_dir_path = os.path.join(constants.TEMP_DIR, tmp_dir_name)
        self.csv_file_path = os.path.join(tmp_dir_path, self.CSV_FILE)
        if not os.path.exists(tmp_dir_path):
            os.makedirs(tmp_dir_path)
        return self

    def write_data_to_csv(self, data_list):
        with open(self.csv_file_path, 'w') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=self.FIELDS, extrasaction='ignore')
            writer.writerow(self.HEADER_ROW)
            writer.writerows(data_list)
        return self

    def get_file_path(self):
        return self.csv_file_path
