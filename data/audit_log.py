import logging
from datetime import datetime

from pstf import constants


# __name__ is data.audit_log, logger predefined in base.py settings
logger = logging.getLogger(__name__)


def log(request, action, issn_list, description=''):
    now = datetime.now().strftime("%d-%m-%Y, %H:%M:%S")
    data = {'timestamp': now, 'user': request.user.email, 'action': action, 'issn': issn_list,
            'description': description}
    logger.info(data)


def log_visit(request, issn_list, description=''):
    log(request, constants.VISIT_ACTION, issn_list, description)


def log_download(request, issn_list=None, description=''):
    if issn_list is None:
        issn_list = []

    log(request, constants.DOWNLOAD_ACTION, issn_list, description)


def log_download_by_query(request, description=''):
    log(request, constants.QUERY_DOWNLOAD_ACTION, [], description)


def log_compare(request, issn_list, description=''):
    log(request, constants.COMPARE_ACTION, issn_list, description)
