import re
import uuid
import logging
import traceback
import json
from typing import List
import datetime

import requests

from django.contrib import messages
from django.contrib.auth.models import Group
from django.contrib.sessions.models import Session
from django.shortcuts import redirect
from django.db.models import Q
from django.db.utils import IntegrityError
from django.utils import timezone
from django.utils.translation import gettext as _
from django.core.mail import EmailMessage
from django.conf import settings
from django.http import Http404

from accounts import models
from . import constants

logger = logging.getLogger(__name__)


def execute_next_task(request, flow):
    """
    Get next available task from the process and execute
    :param request: HTTP Request object
    :param flow: Process Workflow
    :return: Redirect URL or None if next task not available
    """
    url_path = request.path
    str_list = url_path.split("/")
    if len(str_list) > 3:
        if request.activation:
            process_id = str(request.activation.process.id)
            tasks_list = list(flow.task_class.objects.filter(
                Q(process_id=process_id, status='ASSIGNED') | Q(process_id=process_id, status='NEW')))
            if len(tasks_list) > 0:
                task = tasks_list[0]
                result = task.activate()
                if task.status == "NEW":
                    result.assign()
                task_id = str(result.task.id)
                task_name = result.flow_task.name

                return redirect(f'/workflow/{str_list[2]}/{str_list[3]}/{process_id}/{task_name}/{task_id}/')

    return None


def exception_reason(exception):
    """
    Find the cause of the exception
    :param exception: Exception
    :return: Exception cause
    """
    if isinstance(exception, IntegrityError):
        exp = str(exception)
        # email constraint
        user_email = ["UNIQUE constraint", "pstfuser.email"]
        publisher_uname = ['UNIQUE constraint', 'accounts_publisheraccount.uname']
        publisher_name = ['UNIQUE constraint', 'accounts_publisheraccount.publisher_name']
        if all(x in exp for x in user_email):
            return constants.EMAIL_CONSTRAINT
        if all(x in exp for x in publisher_uname) or all(x in exp for x in publisher_name):
            return _("Publisher name already exists")

    return ''


def get_pstfuser(email):
    """
    Convert email to lower case to make sure there is unique email
    :param email: case sensitive email
    :return: user
    """
    return models.PSTFUser.objects.get(email=email.lower())


def get_or_create_pstfuser(email):
    """
    Convert email to lower case to make sure there is unique email
    :param email: case-sensitive email
    :return: user, created
    """
    return models.PSTFUser.objects.get_or_create(email=email.lower())


def send_email(request, subject: str, to, message, _from=settings.SENDER_ADDRESS, use_html=True,
               bcc=False):
    """
    Utility function to send email.
    All email calls should be made using this function to ensure consistent handling.
    :param request:
    :param subject:
    :param to:
    :param message:
    :param _from:
    :param use_html:
    :param bcc: Set it to True to notify bcc users
    :return:
    """
    # To send messages in html format
    # message = get_template("common/email.html").render({'message': message})

    if not isinstance(to, list):
        to = [to]

    try:
        mail = EmailMessage(
            subject=subject,
            body=message,
            from_email=_from,
            to=to,
            reply_to=[],
        )

        if bcc:
            mail.bcc = [settings.BCC_NOTIFICATION_EMAIL]

        if use_html:
            mail.content_subtype = "html"

        mail.send()
    except Exception:
        uid = str(uuid.uuid1())
        logger.error(traceback.format_exc() + " " + uid)

        if request is not None:
            messages.error(request, constants.EMAIL_NOT_SENT + uid)


def add_approved_superusers(context):
    """
    Add all approved super users to context
    :param  context: context object
    """
    active = Q(is_active=True)
    group = Q(groups__name=constants.SUPER_PUBLISHER_GROUP)
    publisher_not_none = ~Q(publisher=None)
    context['approved_users'] = models.PSTFUser.objects.filter(active & group & publisher_not_none).order_by('-created')


def add_archived_superusers(context):
    """
    Add all archived users to context. These users may be rejected users or deactivated users
    :param  context: context object
    """
    active = Q(rejected=True)
    group = Q(groups__name=constants.SUPER_PUBLISHER_GROUP)
    publisher_not_none = ~Q(publisher=None)
    context['archived_users'] = models.PSTFUser.objects.filter(active & group & publisher_not_none).order_by('-created')


def add_awaiting_approval_superusers(context):
    """
    Add super users who are waiting for review to context
    :param  context: context object
    """
    not_active = Q(is_active=False)
    group = Q(groups__name=constants.SUPER_PUBLISHER_GROUP)
    not_rejected = Q(rejected=False)
    publisher_not_none = ~Q(publisher=None)
    awaiting_review = Q(review_status=models.PSTFUser.ReviewStatus.AWAITING_REVIEW)
    context['approve_awaiting_users'] = models.PSTFUser.objects.filter(not_active & group & not_rejected &
                                                          awaiting_review & publisher_not_none).order_by('-created')


def add_awaiting_contract_signing_superusers(context):
    """
    Add super users who are waiting for contract signing to context
    :param  context: context object
    """
    not_active = Q(is_active=False)
    group = Q(groups__name=constants.SUPER_PUBLISHER_GROUP)
    not_rejected = Q(rejected=False)
    publisher_not_none = ~Q(publisher=None)
    awaiting_contract_signing = Q(review_status=models.PSTFUser.ReviewStatus.AWAITING_CONTRACT_SIGNING)
    context['awaiting_contract_signing_users'] = models.PSTFUser.objects.filter(not_active & group & not_rejected &
                                            awaiting_contract_signing & publisher_not_none).order_by('-created')


def add_approved_ins_superusers(context):
    """
    Add all approved super users to context
    :param  context: context object
    """
    active = Q(is_active=True)
    group = Q(groups__name=constants.INSTITUTIONAL_SUPER_USER_GROUP)
    context['approved_ins_users'] = models.PSTFUser.objects.filter(active & group).order_by('name')


def add_archived_ins_superusers(context):
    """
    Add all archived users to context. These users may be rejected users or deactivated users
    :param  context: context object
    """
    active = Q(rejected=True)
    group = Q(groups__name=constants.INSTITUTIONAL_SUPER_USER_GROUP)
    context['archived_ins_users'] = models.PSTFUser.objects.filter(active & group).order_by('name')


def add_awaiting_approval_ins_superusers(context):
    """
    Add super users who are waiting for approval to context
    :param  context: context object
    """
    not_active = Q(is_active=False)
    group = Q(groups__name=constants.INSTITUTIONAL_SUPER_USER_GROUP)
    not_rejected = Q(rejected=False)
    awaiting_review = Q(review_status=models.PSTFUser.ReviewStatus.AWAITING_REVIEW)
    context['approve_awaiting_ins_users'] = models.PSTFUser.objects.filter(not_active & group &
                                                             awaiting_review & not_rejected).order_by('name')


def add_awaiting_contract_signing_ins_superusers(context):
    """
    Add super users who are waiting for contract signing to context
    :param  context: context object
    """
    not_active = Q(is_active=False)
    group = Q(groups__name=constants.INSTITUTIONAL_SUPER_USER_GROUP)
    awaiting_contract_signing = Q(review_status=models.PSTFUser.ReviewStatus.AWAITING_CONTRACT_SIGNING)
    not_rejected = Q(rejected=False)

    context['awaiting_contract_signing_ins_users'] = models.PSTFUser.objects.filter(not_active & group &
                                                            awaiting_contract_signing & not_rejected).order_by('name')


def add_all_superusers(context):
    add_approved_superusers(context)
    add_archived_superusers(context)
    add_awaiting_approval_superusers(context)
    add_awaiting_contract_signing_superusers(context)
    # Institutional Users
    add_approved_ins_superusers(context)
    add_archived_ins_superusers(context)
    add_awaiting_approval_ins_superusers(context)
    add_awaiting_contract_signing_ins_superusers(context)


def is_user_part_of_a_group(user):
    for group in constants.ALL_GROUPS:
        if user.groups.filter(name=group).exists():
            return True
    return False


def create_github_issue(title, body):
    """
    Create github issue and add to a card
    :param title: Title of the issue
    :param body: issue
    """
    if settings.TRACK_ON_GITHUB:
        try:
            headers = {
                "Authorization": 'token %s' % settings.GITHUB_TOKEN,
                "Accept": "application/vnd.github.v3+json"
            }
            data = {
                "title": title,
                "body": body
            }
            # Create github issue
            res = requests.post(settings.GITHUB_ISSUES_API, headers=headers, data=json.dumps(data))

            if res.status_code == 201:
                res_json = res.json()
                carddata = {
                    "contentId": res_json['id'],
                    "content_id": res_json['id'],
                    "content_type": "Issue"
                }
                # add the issue to a project card
                res1 = requests.post(settings.GITHUB_CARDS_API, headers=headers, data=json.dumps(carddata))
                if res1.status_code != 201:
                    logger.error("Github Response: " + str(res.status_code) + " : " + res.text)
            else:
                logger.error("Github Response: " + str(res.status_code) + " : " + res.text)
        except Exception as exp:
            uid = str(uuid.uuid1())
            logger.error(traceback.format_exc() + " " + uid)


def change_user_group(request, user, removed_group_name: str, added_group_name: str):
    added_group = Group.objects.get(name=added_group_name)
    removed_group = Group.objects.get(name=removed_group_name)

    if user.get_state() == 'LI':
        # If user is marked as logged in we will log him out by
        # deleting his active sessions
        user_sessions = []
        all_sessions = Session.objects.filter(expire_date__gte=timezone.now())
        for session in all_sessions:
            if str(user.pk) == session.get_decoded().get('_auth_user_id'):
                user_sessions.append(session.pk)
        Session.objects.filter(pk__in=user_sessions).delete()
        # Remember, this only saves models state
        user.log_out()
        logger.info(f'manually logged out {user}')

    added_group.user_set.add(user)
    removed_group.user_set.remove(user)
    send_email(request, constants.PROMOTION_EMAIL_TITLE,
               get_cs_email_ids() + [user.email],
               constants.PROMOTION_EMAIL_BODY.format(admin_email=request.user.email,
                                                     new_admin_email=user.email))
    messages.success(request, constants.SUCCESSFUL_PROMOTION)
    logger.info(f'{request.user} promoted {user} to {added_group_name}')


def get_cs_email_ids() -> List[str]:
    """
    Returns email ids of all the cOAlitionS users
    """
    is_active = Q(is_active=True)
    group = Q(groups__name=constants.COALITION_S_GROUP)
    cs_users_email_ids = list(models.PSTFUser.objects.values_list('email', flat=True).filter(is_active & group))

    return cs_users_email_ids


def get_spublisher_email_ids(publisher):
    """
    Returns email ids of all the super publisher(Admin) users of the given publisher
    :param publisher: publisher of which the email ids of admins required
    """
    is_active = Q(is_active=True)
    has_publisher = Q(publisher=publisher)
    group = Q(groups__name=constants.SUPER_PUBLISHER_GROUP)
    sp_users_email_ids = list(models.PSTFUser.objects.values_list('email', flat=True).
                              filter(is_active & has_publisher & group))

    return sp_users_email_ids


def get_institutional_admin_email_ids(organisation):
    """
    Returns email ids of all the Institutional Admin users of the given organisation
    :param organisation: organisation of which the email ids of admins required
    """
    is_active = Q(is_active=True)
    has_organisation = Q(organisation=organisation)
    group = Q(groups__name=constants.INSTITUTIONAL_SUPER_USER_GROUP)
    s_users_email_ids = list(models.PSTFUser.objects.values_list('email', flat=True).
                             filter(is_active & has_organisation & group))

    return s_users_email_ids


def get_absolute_url(request):
    return request.build_absolute_uri('/')[:-1] + "/"


def validate_issn(value) -> bool:
    """
    Validates the structure of an ISSN and its checksum.
    :param value:
    :return:
    """
    if not (isinstance(value, str)):
        return False

    if not re.match(r'^\d{4}-\d{3}(\d|X|x)$', value):
        return False

    issn = str(value).replace('-', '').lower()

    c = int(issn[7]) if issn[7] != 'x' else issn[7]

    remainder = (sum([int(i) * (8 - ind) for ind, i in enumerate(issn[0:7])]) % 11)

    if (remainder > 0 and (11 - remainder != c)) and (c != 'x' or 11 - remainder != 10):
        return False

    return True


def get_user_group(user) -> str:
    groups = [constants.INSTITUTIONAL_SUPER_USER_GROUP, constants.INSTITUTIONAL_SUPER_USER_GROUP,
              constants.INSTITUTIONAL_USER_GROUP, constants.SUPER_PUBLISHER_GROUP,
              constants.PUBLISHER_GROUP, constants.COALITION_S_GROUP]

    for group in groups:
        if user.groups.filter(name=group).exists():
            return group

    raise Http404("User does not belong to any of the groups")


def has_group(user, groups) -> bool:
    for group in groups:
        if get_user_group(user) == group:
            return True

    return False


def add_registration_steps(context, current_step, total_steps):
    context['current_step'] = current_step
    context['total_steps'] = total_steps


def add_admin_registration_step(context, current_step):
    add_registration_steps(context, current_step, constants.TOTAL_STEPS_ADMIN_REGISTRATION)


def add_user_registration_step(context, current_step):
    add_registration_steps(context, current_step, constants.TOTAL_STEPS_USER_REGISTRATION)


# Disable FOAA TODO: Remove all FOAA code. Issue#650
def disable_foaa_functionality() -> bool:
    # current date
    current_date = datetime.date.today()

    # FOAA disable date
    foaa_disable_date = settings.FOAA_DISABLE_DATE

    # Check if the current date is after October 31, 2024
    return current_date > foaa_disable_date
