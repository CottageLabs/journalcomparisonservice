import os
import shutil
import datetime
import csv
import json
import logging
import uuid

from elasticsearch import Elasticsearch
from elasticsearch_dsl import Search

from django.conf import settings
from django.http import FileResponse, HttpResponse, Http404
from apscheduler.schedulers.background import BackgroundScheduler

from pstf import utils
from pstf.decorators import is_institutional_user
from data.utils import *
from data import audit_log


logger = logging.getLogger(__name__)


class ExportData:
    """
    Class to create export data package
    """
    # Fields contains the information of the fields for the CSV file header
    FIELDS = ['framework', 'publisher', 'year', 'issn', 'journal_title', 'cluster', 'discipline', 'owner_ror_id', 'publisher_ror_id',
              'apc_list_price_range_lower', 'apc_list_price_range_higher', 'apc_list_price_currency',
              'apc_waiver_discount_policy', 'subscription_list_price_range_lower',
              'subscription_list_price_range_higher',
              'subscription_list_price_for_member_of_the_association_of_americ', 'subscription_list_price_currency',
              'subscription_discount_policy', 'inhouse_or_outsourced_journal_operations', 'rejection_rate',
              'discounts_and_waivers_policy', 'price_breakdown_journal_operations', 'price_breakdown_publication',
              'price_breakdown_fees', 'price_breakdown_communication', 'price_breakdown_general',
              'price_breakdown_surplus_other_revenue', 'price_breakdown_discounts_and_waivers',
              'price_transparency_context', 'research_articles_published', 'acceptance_rate',
              'rejection_rate', 'issue_publication_frequency', 'median_number_reviews',
              'median_time_submission_to_first_decision', 'median_time_peer_review',
              'median_time_acceptance_to_publication', 'counter_5_unique_item_requests',
              'counter_5_total_item_requests', 'price_breakdown_journal_community_development',
              'price_breakdown_journal_submission_on_first_decision', 'price_breakdown_peer_review',
              'price_breakdown_services_acceptance_publication', 'price_breakdown_services_post_publication',
              'price_breakdown_platform_development_support', 'price_breakdown_sales_marketing',
              'price_breakdown_author_customer_support']

    USER_ID = 'user_id'
    UNIQUE_ID = 'uid'
    TMP_DIR_NAME = 'tmp_dir_name'
    TMP_DIR_PATH = 'tmp_dir_path'
    CSV_FILE = 'data_download.csv'
    AUP_FILE = 'JCS-Acceptable-Use-Policy.pdf'
    README_FILE = 'README.txt'
    NOT_FOUND = 'not_found.txt'
    WEEKLY_DATA_DIR_NAME = "data_dump"

    def __init__(self, user_id=None):
        self.NEW_CSV_FILE = None
        self.context = {self.USER_ID: user_id,
                        self.UNIQUE_ID: "_" + datetime.datetime.now().strftime("%m_%d_%H%M%S%f")}

    def create_temp_dir_path(self):
        user_id = self.context[self.USER_ID]

        tmp_dir_name = str(user_id) + self.context[self.UNIQUE_ID]

        self.context[self.TMP_DIR_NAME] = tmp_dir_name
        tmp_dir_path = os.path.join(constants.TEMP_DIR, tmp_dir_name)
        self.context[self.TMP_DIR_PATH] = tmp_dir_path
        return self

    def create_weekly_pkg_dir_path(self):

        self.context[self.TMP_DIR_NAME] = self.WEEKLY_DATA_DIR_NAME
        tmp_dir_path = os.path.join(constants.TEMP_DIR, self.WEEKLY_DATA_DIR_NAME)
        self.context[self.TMP_DIR_PATH] = tmp_dir_path
        # delete previously created directory
        self.delete_temp_dir()
        return self

    def rename_csv_file(self):
        csv_file = os.path.join(self.context[self.TMP_DIR_PATH], self.CSV_FILE)
        self.NEW_CSV_FILE = os.path.join(self.context[self.TMP_DIR_PATH], "data"+self.context[self.UNIQUE_ID]+".csv")
        os.rename(csv_file, self.NEW_CSV_FILE)

    def copy_files_to_tmp(self):
        tmp_dir_path = self.context[self.TMP_DIR_PATH]
        shutil.copytree(constants.EXPORT_DIR_PATH, tmp_dir_path)
        self.rename_csv_file()
        return self

    def write_data_to_csv(self, data_list):
        with open(self.NEW_CSV_FILE, 'a') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=self.FIELDS, extrasaction='ignore')
            writer.writerows(data_list)
        return self

    def write_not_found_data(self, not_found_list):
        """Writes list of ISSN(s) that are not found in the search to not_found.txt file"""
        txt_file = os.path.join(self.context[self.TMP_DIR_PATH], self.NOT_FOUND)
        with open(txt_file, 'a') as txtfile:
            txtfile.write(constants.ISSNS_NOT_FOUND)
            txtfile.write("\n")
            for issn in not_found_list:
                txtfile.write("\n")
                txtfile.writelines(issn)
        return self

    def create_download_package(self):
        zip_file = os.path.join(constants.TEMP_DIR, self.context[self.TMP_DIR_NAME])
        shutil.make_archive(zip_file, "zip", self.context[self.TMP_DIR_PATH])
        self.delete_temp_dir()

    def get_download_link(self):
        link = constants.EXPORT_DOWNLOAD + self.context[self.UNIQUE_ID] + '/'
        return link

    def delete_temp_dir(self):
        if os.path.exists(self.context[self.TMP_DIR_PATH]):
            shutil.rmtree(self.context[self.TMP_DIR_PATH])


def create_export_package(request, records, absolute_url, issns_not_found=None):
    try:
        if issns_not_found is None:
            issns_not_found = []

        if isinstance(records, list):
            if len(records):
                export_data = ExportData(request.user.id).create_temp_dir_path()

                export_data.copy_files_to_tmp()
                export_data.write_data_to_csv(records)
                if len(issns_not_found) > 0:
                    export_data.write_not_found_data(issns_not_found)
                export_data.create_download_package()

                link = absolute_url + export_data.get_download_link()

                utils.send_email(request, constants.DOWNLOAD_LINK_EMAIL_TITLE,
                                 request.user.email, constants.DOWNLOAD_LINK_SUCCESS_MSG.format(link=link))
            else:
                utils.send_email(request, constants.DOWNLOAD_LINK_EMAIL_TITLE,
                                 request.user.email, constants.NO_DATA_FOR_DOWNLOAD)
        else:
            uid = str(uuid.uuid1())
            logger.exception(constants.INVALID_DOWNLOAD_DATA)
            utils.send_email(request, constants.DOWNLOAD_LINK_EMAIL_TITLE,
                             request.user.email, constants.INVALID_DOWNLOAD_DATA_MSG + uid)
    except Exception as exp:
        uid = str(uuid.uuid1())
        logger.exception(str(exp) + uid)
        utils.send_email(request, constants.DOWNLOAD_LINK_EMAIL_TITLE,
                         request.user.email, constants.DOWNLOAD_LINK_FAILURE_MSG + uid)


@is_institutional_user
def download_file(request, id):
    zip_file = id + ".zip"
    # If not weekly data download, add user id for file name
    if id != ExportData.WEEKLY_DATA_DIR_NAME:
        zip_file = str(request.user.id) + zip_file
    else:
        audit_log.log_download(request, description=constants.DOWNLOAD_ALL_JOURNALS)
    file_path = os.path.join(constants.TEMP_DIR, zip_file)
    if os.path.exists(file_path):
        # download file
        file_to_download = open(file_path, 'rb')
        response = FileResponse(file_to_download, content_type='application/force-download')
        response['Content-Disposition'] = 'inline; filename=' + "JCS_" + id + ".zip"
        return response
    else:
        return HttpResponse(json.dumps({'result': 'error', 'message': 'Could not download file. '
                            'The download file does not exist. The link might be expired'}),
                            content_type="application/json")


def sanitise_query(query):
    sanitised_query = {'query': {}}
    if 'query' in  query:
        if 'match_all' in query['query']:
            sanitised_query['query']['match_all'] = {}
        if 'bool' in query['query']:
            sanitised_query['query']['bool'] = {}
            if 'must' in query['query']['bool']:
                sanitised_query['query']['bool']['must'] = []
                for term_query in query['query']['bool']['must']:
                    if 'terms' in term_query:
                        if 'issn.raw' in term_query['terms'] or 'publisher_id' in term_query['terms'] or \
                                'discipline.raw' in term_query['terms']:
                            sanitised_query['query']['bool']['must'].append(term_query)

    return sanitised_query


@is_institutional_user
def export(request):
    # Get absolute URL outside threads to avoid issues with uwsgi
    absolute_url = utils.get_absolute_url(request)
    if request.method == "GET":
        query = request.GET.get("query")
        audit_log.log_download_by_query(request, description=constants.DOWNLOAD_BY_QUERY.format(query=query))
        source = json.loads(query)
        # sanitise the query
        source = sanitise_query(source)

        scheduler = BackgroundScheduler()
        scheduler.add_job(create_export_package_by_query, args=[request, source, absolute_url])
        scheduler.start()

        return HttpResponse(json.dumps({"export": "by query"}), content_type="application/json")

    elif request.method == "POST":
        issns = json.loads(request.body)

        if isinstance(issns, list):
            audit_log.log_download(request, issns, description=constants.DOWNLOAD_FROM_COMPARE if len(issns) > 1 else
                                   constants.DOWNLOAD_FROM_JOURNAL)
            scheduler = BackgroundScheduler()
            scheduler.add_job(create_export_package_from_issns, args=[request, issns, absolute_url])
            scheduler.start()
        else:
            issns = [x.strip() for x in issns.split(",")]
            audit_log.log_download(request, issns, description=constants.DOWNLOAD_BY_ISSN)
            scheduler = BackgroundScheduler()
            scheduler.add_job(create_export_package_from_issns_list, args=[request, issns, absolute_url])
            scheduler.start()

        return HttpResponse(json.dumps({"export": "by issn"}), content_type="application/json")

    raise Http404("No such export mechanism")


def create_export_package_by_query(request, query, absolute_url):
    client = Elasticsearch(**settings.ELASTICSEARCH_DSL['default'])
    s = Search.from_dict(query).using(client).index(settings.ELASTICSEARCH_ALIAS)
    records = []
    for r in s.scan():
        doc = r.to_dict()
        records.append(doc)
    create_export_package(request, records, absolute_url)


def create_export_package_from_issns(request, issns, absolute_url):
    # {issn: "the issn", year: 2021 }
    # so an issn must be selected by year by the below function
    # also see how the function above `create_export_package_by_query` produces its output of issns
    data_list = []
    ip_data_list = get_ip_data_for_issn_dict(issns)
    foaa_data_list = get_foaa_data_for_issn_dict(issns)
    data_list.extend(ip_data_list)
    data_list.extend(foaa_data_list)
    create_export_package(request, data_list, absolute_url)


def create_export_package_from_issns_list(request, issns, absolute_url):
    data_list = []
    ip_data_list = get_ip_data_for_issn_list(issns)
    foaa_data_list = get_foaa_data_for_issn_list(issns)
    data_list.extend(ip_data_list)
    data_list.extend(foaa_data_list)

    # Get the ISSN list which are not available in the search
    filtered_issn = [obj['issn'] for obj in data_list]
    issns_not_found = set(issns) - set(filtered_issn)

    create_export_package(request, data_list, absolute_url, issns_not_found)
