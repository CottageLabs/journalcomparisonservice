import logging
import uuid
from typing import Tuple, List

from django.contrib import messages
from django.shortcuts import render, redirect
from django.db.models import Q
from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned
from django.http import Http404, HttpResponse
from django.conf import settings

from elasticsearch import Elasticsearch
from elasticsearch_dsl import Search

from pstf.decorators import *
from pstf import constants, utils
from accounts import models
from .forms import UserUpdateForm, UserForm, ChangeUserForm
from dashboard import exceptions
from registration import ins_forms
from data import audit_log

from data.models import InformationPower, FairOpenAccessAlliance

logger = logging.getLogger(__name__)


def get_journal_record_by_issn(issn, year) -> Tuple:
    try:
        return (constants.FRAMEWORK_IP, InformationPower.objects.filter(issn=issn, year=year).get())
    except MultipleObjectsReturned:
        raise exceptions.MultipleRecordsPerISSNException(issn)
    except ObjectDoesNotExist:
        pass

    try:
        return (constants.FRAMEWORK_FOAA, FairOpenAccessAlliance.objects.filter(issn=issn, year=year).get())
    except MultipleObjectsReturned:
        raise exceptions.MultipleRecordsPerISSNException(issn)
    except ObjectDoesNotExist:
        return (None, None)


def get_years_for(issn) -> List:
    ip_records = InformationPower.objects.filter(issn=issn)
    ipyears = [record.year for record in ip_records.iterator()]

    foaa_records = FairOpenAccessAlliance.objects.filter(issn=issn)
    foaayears = [record.year for record in foaa_records.iterator()]

    return list(set(ipyears + foaayears))


def get_publisher_for_journal_record(journal):
    return journal.upload.publisher


@is_institutional_user
def journal(request, journal_id, year=None):
    audit_log.log_visit(request, journal_id)
    years = get_years_for(journal_id)
    years.sort(reverse=True)
    if len(years) == 0:
        raise Http404("No data for that journal")

    if year is None:
        year = years[0]

    try:
        framework, journal = get_journal_record_by_issn(journal_id, year)
    except exceptions.MultipleRecordsPerISSNException:
        raise Http404("Multiple journals with that identifier for that year")

    if journal is None:
        raise Http404("No journal found with that identifier for that year")

    publisher = get_publisher_for_journal_record(journal)

    template = 'ins_user/journal.html'
    context = {
        "role": utils.get_user_group(request.user),
        "journal": journal,
        "framework": framework,
        "constants": constants,
        "year": year,
        "years": years,
        "publisher": publisher
    }
    return render(request, template, context)


@is_institutional_user
def publishers(request):
    client = Elasticsearch(**settings.ELASTICSEARCH_DSL['default'])
    s = (Search.from_dict({"query": {"match_all": {}}, "size": 1000})
         .using(client).index(settings.ES_AUTOCOMPLETE_PUBLISHER_ALIAS))
    response_obj = s.execute()
    response = response_obj.to_dict()

    publishers = [p.get("_source", {}) for p in response.get("hits", {}).get("hits", [])]
    sorted_publishers = sorted(publishers, key=lambda x: x['name'].lower())

    template = 'ins_user/publishers.html'
    context = {
        "role": utils.get_user_group(request.user),
        "publishers": sorted_publishers
    }
    return render(request, template, context)


@user_group(constants.COALITION_S_GROUP)
def awaiting_ins_superuser(request, _id):
    template = 'coalitions/ins_suser_awaiting_approval.html'

    context = {'role': constants.COALITION_S_GROUP,
               'user_type': constants.USER_TYPE_INSTITUTIONAL}

    try:
        user = models.PSTFUser.objects.get(id=_id, is_active=False)
        user_form = UserUpdateForm(request.POST or None, instance=user)
        if user.organisation:
            account = models.EndUserAccount.objects.get(id=user.organisation.id)
            form = ins_forms.EndUserAccount(request.POST or None, instance=account)

            if request.POST:
                if 'save' in request.POST:
                    if form.is_valid() and user_form.is_valid():
                        form.save()
                        user_form.save()
                        messages.success(request, constants.SUCCESSFUL_CHANGES)
                    else:
                        messages.error(request, constants.INVALID_FORM)

                elif 'approve' in request.POST:
                    user.is_active = False
                    user.rejected = False
                    user.review_status = models.PSTFUser.ReviewStatus.AWAITING_CONTRACT_SIGNING
                    user.organisation.verified = True
                    user.organisation.save()
                    user.save()

                    messages.success(request, constants.MOVE_TO_CONTRACT_SIGN)
                    logger.info(f'{request.user} approved {user}')
                    return redirect(constants.COALITION_S_CONTRACT_SIGNING_INS_USERS + _id)

                elif 'reject' in request.POST:
                    user.is_active = False
                    user.rejected = True
                    user.review_status = models.PSTFUser.ReviewStatus.REJECTED
                    user.organisation.verified = False
                    user.organisation.save()
                    user.save()

                    utils.send_email(request, constants.REJECTION_EMAIL_TITLE,
                                     user.email, constants.COMMISERATE_REJECTION, bcc=True)
                    messages.success(request, constants.ACCOUNT_REJECTED)
                    logger.info(f'{request.user} rejected {user}')
                    return redirect(constants.COALITION_S_ARCHIVED_INS_USERS + _id)

            context['form'] = form
        else:
            messages.error(request, constants.DOES_NOT_HAVE_ORGANISATION)

        context['user_form'] = user_form
        context['puser'] = user

    except models.PSTFUser.DoesNotExist:
        messages.error(request, constants.USER_DOES_NOT_EXIST)
        template = constants.COALITIONS_USERS_TEMPLATE
    except Exception as exp:
        uid = str(uuid.uuid1())
        logger.exception(str(exp) + uid)
        messages.error(request, constants.UNKNOWN_ERROR + uid)

    utils.add_all_superusers(context)

    return render(request, template, context)


@user_group(constants.COALITION_S_GROUP)
def awaiting_contract_signing_ins_superuser(request, _id):
    template = 'coalitions/ins_suser_awaiting_contract_signing.html'

    context = {'role': constants.COALITION_S_GROUP,
               'user_type': constants.USER_TYPE_INSTITUTIONAL}

    try:
        user = models.PSTFUser.objects.get(id=_id, is_active=False)
        user_form = UserUpdateForm(request.POST or None, instance=user)
        if user.organisation:
            account = models.EndUserAccount.objects.get(id=user.organisation.id)
            form = ins_forms.EndUserAccount(request.POST or None, instance=account)

            if request.POST:
                if 'save' in request.POST:
                    if form.is_valid() and user_form.is_valid():
                        form.save()
                        user_form.save()
                        messages.success(request, constants.SUCCESSFUL_CHANGES)
                    else:
                        messages.error(request, constants.INVALID_FORM)

                elif 'approve' in request.POST:
                    user.is_active = True
                    user.rejected = False
                    user.review_status = models.PSTFUser.ReviewStatus.APPROVED
                    user.organisation.verified = True
                    user.organisation.save()
                    user.save()

                    utils.send_email(request, constants.ACTIVATION_EMAIL_TITLE,
                                     user.email, constants.CONGRATULATE_ACTIVATION)
                    messages.success(request, constants.ACCOUNT_APPROVED)
                    logger.info(f'{request.user} approved {user}')
                    return redirect(constants.COALITION_S_APPROVED_INS_USERS + _id)

                elif 'reject' in request.POST:
                    user.is_active = False
                    user.rejected = True
                    user.review_status = models.PSTFUser.ReviewStatus.REJECTED
                    user.organisation.verified = False
                    user.organisation.save()
                    user.save()

                    utils.send_email(request, constants.REJECTION_EMAIL_TITLE,
                                     user.email, constants.COMMISERATE_REJECTION)
                    messages.success(request, constants.ACCOUNT_REJECTED)
                    logger.info(f'{request.user} rejected {user}')
                    return redirect(constants.COALITION_S_ARCHIVED_INS_USERS + _id)

            context['form'] = form
        else:
            messages.error(request, constants.DOES_NOT_HAVE_ORGANISATION)

        context['user_form'] = user_form
        context['puser'] = user

    except models.PSTFUser.DoesNotExist:
        messages.error(request, constants.USER_DOES_NOT_EXIST)
        template = constants.COALITIONS_USERS_TEMPLATE
    except Exception as exp:
        uid = str(uuid.uuid1())
        logger.exception(str(exp) + uid)
        messages.error(request, constants.UNKNOWN_ERROR + uid)

    utils.add_all_superusers(context)

    return render(request, template, context)


@user_group(constants.COALITION_S_GROUP)
def approved_ins_superuser(request, _id):
    template = 'coalitions/ins_suser_approved_user.html'
    context = {'role': constants.COALITION_S_GROUP,
               'user_type': constants.USER_TYPE_INSTITUTIONAL}

    try:
        user = models.PSTFUser.objects.get(id=_id, is_active=True)
        user_form = ChangeUserForm(request.POST or None, instance=user)

        if user.organisation:
            account = models.EndUserAccount.objects.get(id=user.organisation.id)
            form = ins_forms.EndUserAccount(request.POST or None, instance=account)

            if request.POST:
                if 'save' in request.POST:
                    if form.is_valid() and user_form.is_valid():
                        form.save()
                        user_form.save()
                        messages.success(request, constants.SUCCESSFUL_CHANGES)
                    else:
                        messages.error(request, constants.INVALID_FORM)
                elif 'deactivate' in request.POST:
                    user.is_active = False
                    # Deactivating an existing user is kind of rejecting
                    # so that this user will be available in archive list
                    user.rejected = True
                    user.review_status = models.PSTFUser.ReviewStatus.REJECTED
                    user.organisation.verified = False
                    user.organisation.save()
                    user.save()
                    utils.send_email(request, constants.DEACTIVATION_EMAIL_TITLE,
                                     user.email, constants.DEACTIVATION_EMAIL_BODY, bcc=True)
                    messages.success(request, constants.SUCCESSFUL_DEACTIVATION)
                    logger.info(f'{request.user} deactivated {user}')
                    return redirect(constants.COALITION_S_ARCHIVED_INS_USERS + _id)

            context['form'] = form
        else:
            messages.error(request, constants.DOES_NOT_HAVE_ORGANISATION)

        context['user_form'] = user_form
        context['puser'] = user

    except models.PSTFUser.DoesNotExist:
        messages.error(request, constants.USER_DOES_NOT_EXIST)
        template = constants.COALITIONS_USERS_TEMPLATE
    except Exception as exp:
        uid = str(uuid.uuid1())
        logger.exception(str(exp) + uid)
        messages.error(request, constants.UNKNOWN_ERROR + uid)

    utils.add_all_superusers(context)

    return render(request, template, context)


@user_group(constants.COALITION_S_GROUP)
def archived_ins_superuser(request, _id):
    template = 'coalitions/ins_suser_archived_user.html'
    delete_confirmation_template = 'coalitions/delete_confirmation.html'
    context = {'role': constants.COALITION_S_GROUP,
               'user_type': constants.USER_TYPE_INSTITUTIONAL}

    try:
        user = models.PSTFUser.objects.get(id=_id, rejected=True)

        if user.organisation:
            account = models.EndUserAccount.objects.get(id=user.organisation.id)
            form = ins_forms.EndUserAccount(request.POST or None, instance=account)

            if request.POST:
                if 'reactivate' in request.POST:
                    user.is_active = False
                    user.rejected = False
                    user.review_status = models.PSTFUser.ReviewStatus.AWAITING_REVIEW
                    user.save()
                    messages.success(request, constants.SUCCESSFUL_REACTIVATION)
                    logger.info(f'{request.user} reactivated {user} user')

                    return redirect(constants.COALITION_S_AWAITING_INS_USERS + _id)
                elif 'cancel' in request.POST:
                    return redirect(request.path)
                # Delete the user
                elif 'delete_user_confirm' in request.POST:
                    user.delete()
                    messages.success(request, constants.SUCCESSFUL_DELETION)
                    logger.info(f'{request.user} deleted {user} user')
                    return redirect(constants.COALITION_S_DASHBOARD)
                # Delete institution and all users
                elif 'delete_account' in request.POST:
                    user_count = user.organisation.end_users.count()
                    user.organisation.delete()
                    messages.success(request, constants.SUCCESSFUL_ORG_DELETION.format(users=user_count))
                    logger.info(f'{request.user} deleted {user.organisation} organisation and '
                                f'{user_count} associated users')
                    return redirect(constants.COALITION_S_DASHBOARD)
                elif 'delete' in request.POST:
                    has_more_admins = account.end_users.exclude(pk=user.id)\
                        .filter(groups__name=constants.INSTITUTIONAL_SUPER_USER_GROUP).exists()

                    # Delete user if there is at least one more admin. This check is important because if there
                    # is no admins left, the institution/organisation cannot be managed.
                    if has_more_admins:
                        user.delete()
                        messages.success(request, constants.SUCCESSFUL_DELETION)
                        logger.info(f'{request.user} deleted {user} user')
                        return redirect(constants.COALITION_S_DASHBOARD)
                    else:
                        # Warn the user that there is no admin left and the Institution can be deleted.
                        context['path'] = request.path
                        context['account_type'] = constants.USER_TYPE_INSTITUTION
                        context['account_name'] = user.organisation.organisation_name
                        context['user_name'] = user.name
                        return render(request, delete_confirmation_template, context)

            context['form'] = form
        else:
            messages.error(request, constants.DOES_NOT_HAVE_ORGANISATION)

        context['puser'] = user

    except models.PSTFUser.DoesNotExist:
        messages.error(request, constants.USER_DOES_NOT_EXIST)
        template = constants.COALITIONS_USERS_TEMPLATE
    except Exception as exp:
        uid = str(uuid.uuid1())
        logger.exception(str(exp) + uid)
        messages.error(request, constants.UNKNOWN_ERROR + uid)

    utils.add_all_superusers(context)

    return render(request, template, context)


@user_group(constants.INSTITUTIONAL_SUPER_USER_GROUP)
def ins_s_user_dashboard(request):
    """
    Dashboard for Super Institutional User.
    :param request: Http Request object
    :return: Renders the dashboard template
    """
    template = "ins_user/search.html"
    context = {'role': constants.INSTITUTIONAL_SUPER_USER_GROUP}

    return render(request, template, context)


@user_group(constants.INSTITUTIONAL_SUPER_USER_GROUP)
def ins_s_user_users(request):
    template = 'ins_super_user/users.html'
    context = {'role': constants.INSTITUTIONAL_SUPER_USER_GROUP}
    add_to_context(request.user, context)

    # Render first user by default
    if context['approve_awaiting_users'].count() > 0:
        first_user = context['approve_awaiting_users'].first()
        return redirect(constants.S_INS_AWAITING_USERS + str(first_user.id))
    elif context['approved_users'].count() > 0:
        first_user = context['approved_users'].first()
        return redirect(constants.S_INS_APPROVED_USERS + str(first_user.id))
    elif context['archived_users'].count() > 0:
        first_user = context['archived_users'].first()
        return redirect(constants.S_INS_ARCHIVED_USERS + str(first_user.id))

    return render(request, template, context)


def add_awaiting_approval_users(super_user, context):
    """
    Add users who are waiting for approval to context
    :param super_user:
    :param  context: context object
    :return: users list
    """
    not_active = Q(is_active=False)
    has_organisation = Q(organisation=super_user.organisation)
    group = Q(groups__name=constants.INSTITUTIONAL_USER_GROUP)
    not_rejected = Q(rejected=False)
    context['approve_awaiting_users'] = models.PSTFUser.objects.filter(not_active & group & has_organisation &
                                                                       not_rejected).order_by('name')


def add_approved_users(super_user, context):
    """
    Add all approved users to context
    :param super_user:
    :param  context: context object
    :return: users list
    """
    active = Q(is_active=True)
    has_organisation = Q(organisation=super_user.organisation)
    group = Q(groups__name=constants.INSTITUTIONAL_USER_GROUP)
    context['approved_users'] = models.PSTFUser.objects.filter(active & group & has_organisation).order_by('name')


def add_archived_users(super_user, context):
    """
    Add all archived users to context. These users may be rejected users or deactivated users
    :param super_user:
    :param  context: context object
    :return: users list
    """
    rejected = Q(rejected=True)
    has_organisation = Q(organisation=super_user.organisation)
    group = Q(groups__name=constants.INSTITUTIONAL_USER_GROUP)
    context['archived_users'] = models.PSTFUser.objects.filter(rejected & group & has_organisation).order_by('name')


def add_to_context(super_user, context):
    add_awaiting_approval_users(super_user, context)
    add_approved_users(super_user, context)
    add_archived_users(super_user, context)


@validate_ins_user_request
@user_group(constants.INSTITUTIONAL_SUPER_USER_GROUP)
def ins_awaiting_user(request, _id):
    template = 'ins_super_user/awaiting_approval.html'
    context = {'role': constants.INSTITUTIONAL_SUPER_USER_GROUP}

    try:
        user = models.PSTFUser.objects.get(id=_id, is_active=False)

        if request.POST:
            if 'approve' in request.POST:
                user.is_active = True
                user.save()
                utils.send_email(request, constants.ACTIVATION_EMAIL_TITLE,
                                 user.email, constants.CONGRATULATE_ACTIVATION)
                messages.success(request, constants.ACCOUNT_APPROVED)
                logger.info(f'{request.user} approved {user}')
                return redirect(constants.S_INS_APPROVED_USERS + _id)
            else:
                user.is_active = False
                user.rejected = True
                user.save()
                utils.send_email(request, constants.ACTIVATION_EMAIL_TITLE,
                                 user.email, constants.COMMISERATE_REJECTION_P_USER.format(
                                                                    admin_email=request.user.email))
                messages.success(request, constants.ACCOUNT_REJECTED)
                logger.info(f'{request.user} rejected {user}')
                return redirect(constants.S_INS_ARCHIVED_USERS + _id)

        context['auser'] = user

    except models.PSTFUser.DoesNotExist:
        messages.error(request, constants.USER_DOES_NOT_EXIST)
        template = constants.INS_USERS_TEMPLATE
    except Exception as exp:
        uid = str(uuid.uuid1())
        logger.exception(str(exp) + uid)
        messages.error(request, constants.UNKNOWN_ERROR + uid)

    add_to_context(request.user, context)

    return render(request, template, context)


@validate_ins_user_request
@user_group(constants.INSTITUTIONAL_SUPER_USER_GROUP)
def ins_approved_user(request, _id):
    template = 'ins_super_user/approved_user.html'
    context = {'role': constants.INSTITUTIONAL_SUPER_USER_GROUP}

    try:
        user = models.PSTFUser.objects.get(id=_id, is_active=True)

        if request.POST:
            if 'promote' in request.POST:
                utils.change_user_group(request, user, constants.INSTITUTIONAL_USER_GROUP,
                                        constants.INSTITUTIONAL_SUPER_USER_GROUP)
                return redirect(constants.SINSTITUTIONAL_USERS_DASHBOARD)
            elif 'deactivate' in request.POST:
                user.is_active = False
                # Deactivating an existing user is kind of rejecting
                # so that this user will be available in archive list
                user.rejected = True
                user.save()
                utils.send_email(request, constants.DEACTIVATION_EMAIL_TITLE,
                                 user.email,
                                 constants.DEACTIVATION_EMAIL_BODY_INS_USER.format(
                                                                    admin_email=request.user.email))
                messages.success(request, constants.SUCCESSFUL_DEACTIVATION)
                logger.info(f'{request.user} deactivated {user}')
                return redirect(constants.S_INS_ARCHIVED_USERS + _id)

        context['auser'] = user

    except models.PSTFUser.DoesNotExist:
        messages.error(request, constants.USER_DOES_NOT_EXIST)
        template = constants.INS_USERS_TEMPLATE
    except Exception as exp:
        uid = str(uuid.uuid1())
        logger.exception(str(exp) + uid)
        messages.error(request, constants.UNKNOWN_ERROR + uid)

    add_to_context(request.user, context)

    return render(request, template, context)


@validate_ins_user_request
@user_group(constants.INSTITUTIONAL_SUPER_USER_GROUP)
def ins_archived_user(request, _id):
    template = 'ins_super_user/archived_user.html'
    context = {'role': constants.INSTITUTIONAL_SUPER_USER_GROUP}

    try:
        user = models.PSTFUser.objects.get(id=_id, rejected=True)

        if request.POST:
            if 'reactivate' in request.POST:
                user.is_active = False
                user.rejected = False
                user.save()

                messages.success(request, constants.SUCCESSFUL_REACTIVATION)
                logger.info(f'{request.user} reactivated {user}')
                return redirect(constants.S_INS_AWAITING_USERS + _id)
            # Delete the user
            elif 'delete' in request.POST:
                user.delete()
                messages.success(request, constants.SUCCESSFUL_DELETION)
                logger.info(f'{request.user} deleted {user}')
                return redirect(constants.SINSTITUTIONAL_USERS_DASHBOARD)

        context['auser'] = user

    except models.PSTFUser.DoesNotExist:
        messages.error(request, constants.USER_DOES_NOT_EXIST)
        template = constants.INS_USERS_TEMPLATE
    except Exception as exp:
        uid = str(uuid.uuid1())
        logger.exception(str(exp) + uid)
        messages.error(request, constants.UNKNOWN_ERROR + uid)

    add_to_context(request.user, context)

    return render(request, template, context)


@user_group(constants.INSTITUTIONAL_SUPER_USER_GROUP)
def generate_new_activation_link(request):
    """
    Subpage to generate new activation link
    :param request: Http Request object
    :return: Renders the dashboard template
    """
    context = {'role': constants.INSTITUTIONAL_SUPER_USER_GROUP}
    add_to_context(request.user, context)
    form = UserForm(request.POST or None)
    context['puser_form'] = form

    return render(request, constants.INS_GENERATE_LINK_TEMPLATE, context)


@user_group(constants.INSTITUTIONAL_SUPER_USER_GROUP)
def create_ins_link(request):
    """
    Create a link for new Institutional User
    :param request: HTTP Request object
    """
    context = {'role': constants.INSTITUTIONAL_SUPER_USER_GROUP}

    account_type = constants.INSTITUTIONAL_USER_GROUP
    account_id = request.user.organisation.id

    form = UserForm(request.POST or None)
    context['puser_form'] = form

    if request.POST:
        if form.is_valid():
            email = form.cleaned_data['email']
            link = models.NewAccountRequest(account_type=account_type, account_id=account_id, email=email)
            link.save()

            context['link_url'] = (request.build_absolute_uri('/')[:-1] + "/"
                                   + constants.REGISTER + "/ins_user/" + str(link.id))
        else:
            messages.error(request, constants.INS_USER_EMAIL_REQUIRED)
    # add all users to context to display users on users page
    add_to_context(request.user, context)

    return render(request, constants.INS_GENERATE_LINK_TEMPLATE, context)


@user_group(constants.INSTITUTIONAL_USER_GROUP)
def ins_user_dashboard(request):
    """
    Dashboard for Institutional User.
    :param request: Http Request object
    :return: Renders Institutional User dashboard template
    """
    template = 'ins_user/search.html'
    context = {'role': constants.INSTITUTIONAL_USER_GROUP}

    return render(request, template, context)


def set_tnc_cookie(request) -> HttpResponse:
    response = HttpResponse()
    if utils.has_group(request.user,
                       [constants.INSTITUTIONAL_SUPER_USER_GROUP,
                        constants.INSTITUTIONAL_USER_GROUP]):
        response.set_cookie(
            settings.TNC_COOKIE_KEY,
            settings.TNC_COOKIE_VALUE,
            max_age=settings.TNC_COOKIE_MAX_AGE,
            samesite=None,
            secure=True
        )
    return response
