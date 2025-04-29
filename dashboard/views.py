import logging
import uuid
import re
from typing import List, Tuple
from zipfile import BadZipFile

import requests
from django.contrib.auth.models import Group
from django.contrib.sessions.models import Session
from django.utils import timezone
from elasticsearch import Elasticsearch

from django.contrib.messages import get_messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, FileResponse, HttpResponseBadRequest, HttpResponseForbidden
from django.contrib import messages
from django.core.files.storage import default_storage
from django.shortcuts import render, redirect
from django.db.models import Q

from data.models import InformationPower, FairOpenAccessAlliance
from data.documents import *
from data.utils import title_variants
from login.views import login_view
from django.conf import settings
from pstf.utils import send_email, get_cs_email_ids

from registration import forms as regforms
from pstf.decorators import *
from pstf import constants, utils

from accounts import models
from upload import forms
from upload.models import UploadFile, frameworks, publisher_directory
from upload.spreadsheets import ValidateSpreadsheet


from .forms import UserUpdateForm, UserForm, ChangeUserForm
from dashboard import exceptions

logger = logging.getLogger(__name__)

# Uncomment the code when publisher journal search is enabled
# @is_publisher_user
# def publisher_journal_search(request):
#     template = 'publisher/search.html'
#     context = {'role': utils.get_user_group(request.user)}
#
#     return render(request, template, context)


def get_journal_record_by_issn(issn, year, publisher_id) -> Tuple:
    candidates = []
    for ip in InformationPower.objects.filter(issn=issn, year=year):
        if ip.upload.publisher.id == publisher_id:
            candidates.append(ip)
    if len(candidates) == 1:
        return (constants.FRAMEWORK_IP, candidates[0])
    if len(candidates) > 1:
        raise exceptions.MultipleRecordsPerISSNException(issn, year)

    for foaa in FairOpenAccessAlliance.objects.filter(issn=issn, year=year):
        if foaa.upload.publisher.id == publisher_id:
            candidates.append(foaa)
    if len(candidates) == 1:
        return (constants.FRAMEWORK_FOAA, candidates[0])
    if len(candidates) > 1:
        raise exceptions.MultipleRecordsPerISSNException(issn, year)

    return (None, None)


def get_years_for(issn, publisher_id) -> List:
    ip_records = InformationPower.objects.filter(issn=issn).values("year", "upload").distinct()
    ipyears = []
    for ipr in ip_records:
        uf = UploadFile.objects.get(pk=ipr.get("upload"))
        if uf.publisher.id == publisher_id:
            ipyears.append(ipr.get("year"))

    foaa_records = FairOpenAccessAlliance.objects.filter(issn=issn).values("year", "upload").distinct()
    foaayears = []
    for foaa in foaa_records:
        uf = UploadFile.objects.get(pk=foaa.get("upload"))
        if uf.publisher.id == publisher_id:
            foaayears.append(foaa.get("year"))

    return list(set(ipyears + foaayears))


def get_publisher_for_journal_record(journal):
    return journal.upload.publisher

# Uncomment the code when publisher journal search is enabled
# @is_publisher_user
# def journal(request, journal_id, year=None):
#     publisher_id = request.user.publisher.id
#     years = get_years_for(journal_id, publisher_id)
#     years.sort(reverse=True)
#     if len(years) == 0:
#         raise Http404("No data for that journal")   # this is where the security for this route lies - if there is no year data for that publisher, then they do not have access
#
#     if year is None:
#         year = years[0]
#
#     if year not in years:
#         raise Http404("No data for that journal")   # this is the other part of the security - the requested year must be in the list of years that publisher provided data
#
#     try:
#         framework, journal = get_journal_record_by_issn(journal_id, year, publisher_id)
#     except exceptions.MultipleRecordsPerISSNException:
#         raise Http404("Multiple journals with that identifier for that year")
#
#     if journal is None:
#         raise Http404("No journal found with that identifier for that year")
#
#     publisher = get_publisher_for_journal_record(journal)
#
#     template = 'publisher/journal.html'
#     context = {
#         "role": utils.get_user_group(request.user),
#         "journal": journal,
#         "framework": framework,
#         "constants": constants,
#         "year": year,
#         "years": years,
#         "publisher": publisher
#     }
#     return render(request, template, context)


@login_required
def download_file(request, file_id: int):
    """
    Looks for an uploaded file by id. If the user is not a CoalitionS admin
    then the file has to belong to the same publisher as the session user.
    The file is then proxy streamed from S3 if it is found.
    Returns 403 if a file is not found.
    :param request:
    :param file_id:
    :return:
    """
    kwargs = {'pk': file_id}

    if not request.user.groups.filter(name=constants.COALITION_S_GROUP).exists():
        kwargs['publisher'] = request.user.publisher

    upload_file = UploadFile.objects.filter(**kwargs).first()

    if upload_file:
        r = requests.get(upload_file.s3_url, stream=True)
        response = FileResponse(r.raw)
        response['Content-Disposition'] = f'inline; filename={upload_file.original_file_name}'

        return response

    return HttpResponseForbidden()


def get_files(startswith: str) -> List[UploadFile]:
    """
    Get user's publisher's files
    :param startswith:
    :return:
    """
    return UploadFile.objects \
        .filter(upload_file__startswith=startswith) \
        .order_by('-data_year')


def create_journal_autocomplete_document(ipobj, es: Elasticsearch):
    issn = ipobj.issn
    issns = [issn.lower(), issn.replace("-", "")]
    publishers = [ipobj.publisher_id]

    titles = title_variants(ipobj.journal_title)

    acdoc = JournalAutocompleteDocument(issn=issn, title=ipobj.journal_title, publisher_id=publishers,
                                        issn_ac=issns, title_ac=titles)
    acdoc.save(using=es, index=settings.ES_AUTOCOMPLETE_JOURNAL_ALIAS)


def create_discipline_autocomplete_document(ipobj, es: Elasticsearch):
    disc = ipobj.discipline
    variants = title_variants(disc)

    m = re.search(r'^(.+\. )', disc)
    if m:
        ex_number = disc[len(m.group(1)):]
        ex_number_variants = title_variants(ex_number)
        variants += ex_number_variants

    acdoc = DisciplineAutocompleteDocument(name=disc, name_ac=variants)
    acdoc.save(using=es, index=settings.ES_AUTOCOMPLETE_DISCIPLINE_ALIAS)


def create_ip_documents(objects):
    es = Elasticsearch(**settings.ELASTICSEARCH_DSL['default'])
    for ip in objects:
        ip_document = InformationPowerDocument(
            **{k: v for k, v in ip.__dict__.items() if not k.startswith('_')})

        ip_document.framework = "ip"
        ip_document.publisher = ip.publisher
        ip_document.publisher_id = ip.publisher_id

        ip_document.save(using=es, index=settings.ELASTICSEARCH_ALIAS)

        create_journal_autocomplete_document(ip, es)
        create_discipline_autocomplete_document(ip, es)


def process_upload(request, context):
    """
    Process upload
    :param request:
    :param context:
    :return:
    """
    if context['form'].is_valid():
        new_upload = context['form'].save(commit=False)
        new_upload.user = request.user
        new_upload.user_name = request.user.name
        new_upload.publisher = request.user.publisher
        new_upload.size = request.FILES['upload_file'].size
        new_upload.original_file_name = new_upload.upload_file.name

        aws_destination = publisher_directory(new_upload, new_upload.original_file_name)

        if UploadFile.objects.filter(Q(upload_file=aws_destination) & ~Q(data_year=new_upload.data_year)).count():
            messages.error(request, constants.NO_ACCIDENTAL_OVERWRITE.format(f=new_upload.original_file_name))
            logger.info(f'{request.user} attempted to overwrite {new_upload.original_file_name}.')
            return

        new_upload.save()

        file = default_storage.open(new_upload.upload_file.name, 'rb')

        try:
            vds = ValidateSpreadsheet(new_upload, file, request)
        except ValueError as ve:
            # File couldn't be read
            messages.add_message(request, settings.SPREADSHEET, ve)
            new_upload.delete()
            logger.exception(ve)
            default_storage.delete(new_upload.upload_file.name)
            return
        except BadZipFile as bzf:
            # File couldn't be read
            messages.add_message(request, settings.SPREADSHEET, bzf)
            new_upload.delete()
            default_storage.delete(new_upload.upload_file.name)
            logger.exception(bzf)
            return
        except Exception as exc:
            # Indeterminate exception
            uid = str(uuid.uuid1())
            messages.add_message(request, settings.SPREADSHEET, constants.UNKNOWN_ERROR + uid)
            logger.exception(str(exc) + "-" + uid)
            new_upload.delete()
            default_storage.delete(new_upload.upload_file.name)
            return

        if not vds.missing_headers and vds.is_valid():
            # Now that spreadsheet data has been verified we can save the number of journals as a property
            # of the uploaded file
            new_upload.journals = vds.journals
            new_upload.save()

            # Delete both the actual file in S3 and the db model instance
            # of data uploaded by user of same publisher, for the same year using the same framework
            for d in UploadFile.objects.filter(
                    publisher=new_upload.publisher,
                    framework=new_upload.framework,
                    data_year=new_upload.data_year, ).filter(~Q(id=new_upload.id)):
                default_storage.delete(d.name)
                logger.info(f'{request.user} deleted {d.name} when overwriting upload.')
                d.delete()

            # Now that the data has been validated we can run checks on the ISSNs to see if there are
            # any clashes, and if so email notifications
            vds.check_for_issn_duplicates()

            if vds.framework.acronym == 'ip':
                InformationPower.objects.bulk_create(vds.objects)
                # This is to push the document to elastic search
                # TODO: Implement this when there is a requirement to push when upload is done
                # create_ip_documents(vds.objects)

            elif vds.framework.acronym == 'foaa':
                FairOpenAccessAlliance.objects.bulk_create(vds.objects)

            # Calling all on queryset to refresh it (append the new file to results)
            context['files'] = context['files'].all()
            messages.success(request, constants.SUCCESSFUL_UPLOAD.format(f=dict(frameworks)[new_upload.framework],
                                                                         y=new_upload.data_year))
            logger.info(f'{request.user} uploaded {new_upload.upload_file.name}.')
        else:
            msg = (f'Deleted failed upload: {new_upload.original_file_name} from {new_upload.user} with '
                   f'{len(vds.errors)} errors and {len(vds.missing_headers)} missing headers.')
            logger.info(msg)
            vds.report_errors(request)
            new_upload.delete()
            default_storage.delete(new_upload.upload_file.name)
            logger.error(f'{request.user} uploaded {new_upload.upload_file.name} but it had {len(vds.errors)} errors.')


def alert_admin(request, upload_file: UploadFile):
    """
    Establish what users are super publishers and email them a notification.
    :param request:
    :param upload_file:
    :return:
    """

    admins = utils.get_spublisher_email_ids(upload_file.publisher)

    if len(admins):
        msg = constants.ALERT_PUBLISHER_FILE_DELETED_EMAIL_BODY.format(f=upload_file.original_file_name,
                                                                       u=upload_file.user.name,
                                                                       t=upload_file.uploaded)
        send_email(request=request,
                   subject=constants.ALERT_PUBLISHER_FILE_DELETED_EMAIL_TITLE,
                   message=msg,
                   to=admins)


def process_deletion(request, alert: bool = False):
    """
    Process a request to delete a file.
    Security is ensured as this function is only called by authenticated views, if the
    session user does not belong to the Coalition S admin group the lookup is limited
    to files belonging to the same publisher.
    :param alert:
    :param request:
    :return:
    """
    delete_form = forms.DeleteFileForm(request.POST)

    if delete_form.is_valid():
        kwargs = {'pk': request.POST['delete_file_id']}

        if not request.user.groups.filter(name=constants.COALITION_S_GROUP).exists():
            kwargs['publisher'] = request.user.publisher

        upload = UploadFile.objects.filter(**kwargs).first()

        if upload:
            if alert:
                alert_admin(request, upload)
            framework = [f[1] for f in frameworks if f[0] == upload.framework][0]
            year = upload.data_year
            filename = upload.original_file_name
            publisher = upload.publisher.publisher_name
            default_storage.delete(upload.name)
            upload.delete()
            messages.warning(request, constants.DELETED_FILE.format(f=framework, y=year))
            logger.info(str(request.user) + " " + constants.DELETED_FILE.format(f=framework, y=year) + " (" +
                        filename + ") for " + publisher)
        else:
            # An attempt has been made to delete a file that either does not exist or
            # user isn't authorized to delete.
            logger.error(str(request.user) + " attempted to delete #" + kwargs['pk'])


def _separate_messages(request):
    """
    Separates spreadsheet messages from other messages.
    :param request:
    :return:
    """
    spreadsheet = []
    general = []
    msgs = get_messages(request)
    for m in msgs:
        if m.tags == "spreadsheet":
            spreadsheet.append(m)
        else:
            general.append(m)

    return general, spreadsheet


@user_group(constants.COALITION_S_GROUP)
def coalitions_account_search(request):
    context = {'VERSION': settings.VERSION}
    template = 'coalitions/account_search.html'
    return render(request, template, context)


@user_group(constants.COALITION_S_GROUP)
def coalitions_dashboard(request):
    """
    Dashboard for coalitionS User.
    :param request: Http Request object
    :return: Renders dashboard
    """
    template = 'coalitions/dashboard.html'
    context = {'role': constants.COALITION_S_GROUP,
               'publisher': request.user.publisher,
               'frameworks': dict(frameworks), }

    utils.add_all_superusers(context)

    # Render first user by default
    if context['approve_awaiting_users'].count() > 0:
        first_user = context['approve_awaiting_users'].first()
        return redirect(constants.COALITION_S_AWAITING_USERS + str(first_user.id))
    elif context['awaiting_contract_signing_users'].count() > 0:
        first_user = context['awaiting_contract_signing_users'].first()
        return redirect(constants.COALITION_S_CONTRACT_SIGNING_USERS + str(first_user.id))
    elif context['approve_awaiting_ins_users'].count() > 0:
        first_user = context['approve_awaiting_ins_users'].first()
        return redirect(constants.COALITION_S_AWAITING_INS_USERS + str(first_user.id))
    elif context['awaiting_contract_signing_ins_users'].count() > 0:
        first_user = context['awaiting_contract_signing_ins_users'].first()
        return redirect(constants.COALITION_S_CONTRACT_SIGNING_INS_USERS + str(first_user.id))
    elif context['approved_users'].count() > 0:
        first_user = context['approved_users'].first()
        return redirect(constants.COALITION_S_APPROVED_USERS + str(first_user.id))
    elif context['approved_ins_users'].count() > 0:
        first_user = context['approved_ins_users'].first()
        return redirect(constants.COALITION_S_APPROVED_INS_USERS + str(first_user.id))
    elif context['archived_users'].count() > 0:
        first_user = context['archived_users'].first()
        return redirect(constants.COALITION_S_ARCHIVED_USERS + str(first_user.id))
    elif context['archived_ins_users'].count() > 0:
        first_user = context['archived_ins_users'].first()
        return redirect(constants.COALITION_S_ARCHIVED_INS_USERS + str(first_user.id))

    return render(request, template, context)


@user_group(constants.SUPER_PUBLISHER_GROUP)
def s_publisher_dashboard(request):
    """
    Dashboard for Super Publisher User.
    :param request: Http Request object
    :return: Renders the dashboard template
    """
    template = 'super_publisher/dashboard.html'
    context = {'role': constants.SUPER_PUBLISHER_GROUP,
               'publisher': request.user.publisher,
               'frameworks': dict(frameworks),
               'delete_form': forms.DeleteFileForm(),
               'files': get_files(request.user.publisher.directory_name),
               'disable_foaa': utils.disable_foaa_functionality()
    }

    if request.method == 'GET':
        context['form'] = forms.UploadFileForm()
    elif request.method == 'POST':
        # Disable FOAA TODO: Remove all FOAA code. Issue#650
        post_data = request.POST.copy()
        if utils.disable_foaa_functionality():
            post_data['framework'] = constants.FRAMEWORK_IP

        if request.FILES:
            context['form'] = forms.UploadFileForm(post_data, request.FILES)
            process_upload(request, context)
        else:
            context['form'] = forms.UploadFileForm()

        if 'delete_file_id' in request.POST:
            process_deletion(request)

        context['messages'], context['spreadsheet'] = _separate_messages(request)

    return render(request, template, context)


@user_group(constants.SUPER_PUBLISHER_GROUP)
def generate_new_activation_link(request):
    """
    Subpage for super publisher to generate new activation link
    :param request: Http Request object
    :return: Renders the dashboard template
    """
    template = 'super_publisher/generate.html'
    context = {'role': constants.SUPER_PUBLISHER_GROUP}
    add_to_context(request.user, context)
    create_publisher_user_form(request, context)

    return render(request, template, context)


@user_group(constants.PUBLISHER_GROUP)
def publisher_dashboard(request):
    """
    Dashboard for Publisher User.
    :param request: Http Request object
    :return: Renders publisher dashboard template
    """
    template = 'publisher/dashboard.html'
    context = {'role': constants.PUBLISHER_GROUP,
               'publisher': request.user.publisher,
               'frameworks': dict(frameworks),
               'delete_form': forms.DeleteFileForm(),
               'files': get_files(request.user.publisher.directory_name),
               'disable_foaa': utils.disable_foaa_functionality()
               }

    if request.method == 'GET':
        context['form'] = forms.UploadFileForm()
    elif request.method == 'POST':
        # Disable FOAA TODO: Remove all FOAA code. Issue#650
        post_data = request.POST.copy()
        if utils.disable_foaa_functionality():
            post_data['framework'] = constants.FRAMEWORK_IP

        if request.FILES:
            context['form'] = forms.UploadFileForm(post_data, request.FILES)
            process_upload(request, context)
        else:
            context['form'] = forms.UploadFileForm()

        if 'delete_file_id' in request.POST:
            process_deletion(request)

        context['messages'], context['spreadsheet'] = _separate_messages(request)

    return render(request, template, context)


def create_publisher_user_form(request, context):
    form = UserForm(request.POST or None)
    context['puser_form'] = form
    return form


@user_group(constants.SUPER_PUBLISHER_GROUP)
def create_publisher_link(request):
    """
    Create a link for new publisher
    :param request: HTTP Request object
    """
    context = {'role': constants.SUPER_PUBLISHER_GROUP}

    account_type = constants.PUBLISHER_GROUP
    account_id = request.user.publisher.id

    form = create_publisher_user_form(request, context)

    if request.POST:
        if form.is_valid():
            email = form.cleaned_data['email']
            link = models.NewAccountRequest(account_type=account_type, account_id=account_id, email=email)
            link.save()

            context['link_url'] = request.build_absolute_uri('/')[:-1] + "/" + constants.REGISTER + "/publisher/" + str(
                link.id)
        else:
            messages.error(request, constants.PUBLISHER_EMAIL_REQUIRED)
    # add all users to context to display users on users page
    add_to_context(request.user, context)

    return render(request, constants.PUBLISHER_GENERATE_LINK_TEMPLATE, context)


@user_group(constants.SUPER_PUBLISHER_GROUP)
def publisher_users(request):
    template = 'super_publisher/users.html'
    context = {'role': constants.SUPER_PUBLISHER_GROUP}
    create_publisher_user_form(request, context)
    add_to_context(request.user, context)

    # Render first user by default
    if context['approve_awaiting_users'].count() > 0:
        first_user = context['approve_awaiting_users'].first()
        return redirect(constants.SPUBLISHER_AWAITING_USERS + str(first_user.id))
    elif context['approved_users'].count() > 0:
        first_user = context['approved_users'].first()
        return redirect(constants.SPUBLISHER_APPROVED_USERS + str(first_user.id))
    elif context['archived_users'].count() > 0:
        first_user = context['archived_users'].first()
        return redirect(constants.SPUBLISHER_ARCHIVED_USERS + str(first_user.id))

    return render(request, template, context)


def add_awaiting_approval_users(super_user, context):
    """
    Add users who are waiting for approval to context
    :param super_user: current user logged in
    :param  context: context object
    :return: users list
    """
    not_active = Q(is_active=False)
    has_publisher = Q(publisher=super_user.publisher)
    group = Q(groups__name=constants.PUBLISHER_GROUP)
    not_rejected = Q(rejected=False)
    context['approve_awaiting_users'] = models.PSTFUser.objects.filter(not_active & has_publisher
                                                                       & group & not_rejected).order_by('name')


def add_approved_users(super_user, context):
    """
    Add all approved users to context
    :param super_user: current user logged in
    :param  context: context object
    :return: users list
    """
    active = Q(is_active=True)
    has_publisher = Q(publisher=super_user.publisher)
    group = Q(groups__name=constants.PUBLISHER_GROUP)
    context['approved_users'] = models.PSTFUser.objects.filter(active & has_publisher & group).order_by('name')


def add_archived_users(super_user, context):
    """
    Add all archived users to context. These users may be rejected users or deactivated users
    :param super_user: current user logged in
    :param  context: context object
    :return: users list
    """
    active = Q(rejected=True)
    has_publisher = Q(publisher=super_user.publisher)
    group = Q(groups__name=constants.PUBLISHER_GROUP)
    context['archived_users'] = models.PSTFUser.objects.filter(active & has_publisher & group).order_by('name')


def add_to_context(super_user, context):
    add_awaiting_approval_users(super_user, context)
    add_approved_users(super_user, context)
    add_archived_users(super_user, context)


@validate_publisher_user_request
@user_group(constants.SUPER_PUBLISHER_GROUP)
def publisher_awaiting_user(request, _id):
    template = 'super_publisher/awaiting_approval.html'
    context = {'role': constants.SUPER_PUBLISHER_GROUP}

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
                return redirect(constants.SPUBLISHER_APPROVED_USERS + _id)
            else:
                user.is_active = False
                user.rejected = True
                user.save()
                utils.send_email(request, constants.ACTIVATION_EMAIL_TITLE,
                                 user.email, constants.COMMISERATE_REJECTION_P_USER.format(
                                                                    admin_email=request.user.email))
                logger.info(f'{request.user} rejected {user}')
                messages.success(request, constants.ACCOUNT_REJECTED)
                return redirect(constants.SPUBLISHER_ARCHIVED_USERS + _id)

        context['auser'] = user
        create_publisher_user_form(request, context)

    except models.PSTFUser.DoesNotExist:
        messages.error(request, constants.USER_DOES_NOT_EXIST)
        template = constants.PUBLISHER_USERS_TEMPLATE
    except Exception as exp:
        uid = str(uuid.uuid1())
        logger.exception(str(exp) + uid)
        messages.error(request, constants.UNKNOWN_ERROR + uid)

    add_to_context(request.user, context)

    return render(request, template, context)


@validate_publisher_user_request
@user_group(constants.SUPER_PUBLISHER_GROUP)
def publisher_approved_user(request, _id):
    template = 'super_publisher/approved_user.html'
    context = {'role': constants.SUPER_PUBLISHER_GROUP,
               'publisher': request.user.publisher,
               'frameworks': dict(frameworks), }

    try:
        # Ensure that the user belongs to same publisher as requesting user and that he
        # belongs to the publisher group
        user = models.PSTFUser.objects.get(id=_id, publisher=request.user.publisher,
                                           groups__name__in=[constants.PUBLISHER_GROUP], is_active=True)

        if request.POST:
            if 'promote' in request.POST:
                utils.change_user_group(request, user, constants.PUBLISHER_GROUP, constants.SUPER_PUBLISHER_GROUP)
                return redirect(constants.SPUBLISHER_USERS_DASHBOARD)
            elif 'deactivate' in request.POST:
                user.is_active = False
                # Deactivating an existing user is kind of rejecting
                # so that this user will be available in archive list
                user.rejected = True
                user.save()
                utils.send_email(request, constants.DEACTIVATION_EMAIL_TITLE,
                                 user.email,
                                 constants.DEACTIVATION_EMAIL_BODY_P_USER.format(
                                     admin_email=request.user.email))
                messages.success(request, constants.SUCCESSFUL_DEACTIVATION)
                logger.info(f'{request.user} deactivated {user}')
                return redirect(constants.SPUBLISHER_ARCHIVED_USERS + _id)

        context['auser'] = user
        create_publisher_user_form(request, context)

    except models.PSTFUser.DoesNotExist:
        messages.error(request, constants.USER_DOES_NOT_EXIST)
        template = constants.PUBLISHER_USERS_TEMPLATE
    except Exception as exp:
        uid = str(uuid.uuid1())
        logger.exception(str(exp) + uid)
        messages.error(request, constants.UNKNOWN_ERROR + uid)

    add_to_context(request.user, context)

    return render(request, template, context)


@validate_publisher_user_request
@user_group(constants.SUPER_PUBLISHER_GROUP)
def publisher_archived_user(request, _id):
    template = 'super_publisher/archived_user.html'
    context = {'role': constants.SUPER_PUBLISHER_GROUP,
               'publisher': request.user.publisher,
               'frameworks': dict(frameworks), }

    try:
        # Ensure that the user belongs to same publisher as requesting user
        user = models.PSTFUser.objects.get(id=_id, publisher=request.user.publisher, rejected=True)

        if request.POST:
            if 'reactivate' in request.POST:
                user.is_active = False
                user.rejected = False
                user.review_status = models.PSTFUser.ReviewStatus.AWAITING_REVIEW
                user.save()

                messages.success(request, constants.SUCCESSFUL_REACTIVATION)
                logger.info(f'{request.user} reactivated {user}')
                return redirect(constants.SPUBLISHER_AWAITING_USERS + _id)
            # Delete the user
            elif 'delete' in request.POST:
                user.delete()
                messages.success(request, constants.SUCCESSFUL_DELETION)
                logger.info(f'{request.user} deleted {user}')
                return redirect(constants.SPUBLISHER_USERS_DASHBOARD)

        context['auser'] = user
        create_publisher_user_form(request, context)

    except models.PSTFUser.DoesNotExist:
        messages.error(request, constants.USER_DOES_NOT_EXIST)
        template = constants.PUBLISHER_USERS_TEMPLATE
    except Exception as exp:
        uid = str(uuid.uuid1())
        logger.exception(str(exp) + uid)
        messages.error(request, constants.UNKNOWN_ERROR + uid)

    add_to_context(request.user, context)

    return render(request, template, context)


@user_group(constants.COALITION_S_GROUP)
def publisher_approved_superuser(request, _id):
    template = 'coalitions/approved_user.html'
    context = {'role': constants.COALITION_S_GROUP,
               'user_type': constants.USER_TYPE_PUBLISHER,
               'publisher': request.user.publisher,
               'frameworks': dict(frameworks), }

    try:
        user = models.PSTFUser.objects.get(id=_id, is_active=True)
        user_form = ChangeUserForm(request.POST or None, instance=user)
        account = models.PublisherAccount.objects.get(id=user.publisher.id)
        form = regforms.PublisherAccount(request.POST or None, instance=account)

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
                user.publisher.verified = False
                user.publisher.save()
                user.save()
                utils.send_email(request, constants.DEACTIVATION_EMAIL_TITLE,
                                 user.email, constants.DEACTIVATION_EMAIL_BODY, bcc=True)
                messages.success(request, constants.SUCCESSFUL_DEACTIVATION)
                logger.info(f'{request.user} deactivated {user}')

                return redirect(constants.COALITION_S_ARCHIVED_USERS + _id)
            elif 'delete_file_id' in request.POST:
                user_form = UserUpdateForm(instance=user)
                form = regforms.PublisherAccount(instance=account)

                process_deletion(request, True)

        context['form'] = form
        context['user_form'] = user_form
        context['puser'] = user
        context['files'] = get_files(user.publisher.directory_name)

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
def publisher_archived_superuser(request, _id):
    template = 'coalitions/archived_user.html'
    delete_confirmation_template = 'coalitions/delete_confirmation.html'
    context = {'role': constants.COALITION_S_GROUP,
               'user_type': constants.USER_TYPE_PUBLISHER,
               'publisher': request.user.publisher,
               'frameworks': dict(frameworks), }

    try:
        user = models.PSTFUser.objects.get(id=_id, rejected=True)

        if request.POST:
            if 'reactivate' in request.POST:
                user.is_active = False
                user.rejected = False
                user.review_status = models.PSTFUser.ReviewStatus.AWAITING_REVIEW
                user.save()
                messages.success(request, constants.SUCCESSFUL_REACTIVATION)

                logger.info(f'{request.user} reactivated {user}')

                return redirect(constants.COALITION_S_AWAITING_USERS + _id)

            elif 'cancel' in request.POST:
                return redirect(request.path)
            # Delete the user
            elif 'delete_user_confirm' in request.POST:
                user.delete()
                messages.success(request, constants.SUCCESSFUL_DELETION)
                logger.info(f'{request.user} deleted {user} user')
                return redirect(constants.COALITION_S_DASHBOARD)
            # Delete publisher and all users
            elif 'delete_account' in request.POST:
                user_count = user.publisher.users.count()
                user.publisher.delete()
                messages.success(request, constants.SUCCESSFUL_PUB_DELETION.format(users=user_count))
                logger.info(f'{request.user} deleted {user.publisher} publisher and {user_count} associated users')
                return redirect(constants.COALITION_S_DASHBOARD)
            elif 'delete' in request.POST:
                publisher = user.publisher

                # Before deleting the super publisher, check if there is at least one more super publisher left.
                has_more_super_publisher = publisher.users.exclude(pk=user.id)\
                        .filter(groups__name=constants.SUPER_PUBLISHER_GROUP).exists()

                # Delete user if there is at least one more super publisher. This check is important because if there
                # is no super publisher left, the publisher cannot be managed.
                if has_more_super_publisher:
                    user.delete()
                    messages.success(request, constants.SUCCESSFUL_DELETION)
                    logger.info(f'{request.user} deleted {user} user')
                    return redirect(constants.COALITION_S_DASHBOARD)
                else:
                    # Warn the user that there is no super publisher left and the publisher can be deleted.
                    context['account_type'] = constants.USER_TYPE_PUBLISHER
                    context['path'] = request.path
                    context['account_name'] = user.publisher.publisher_name
                    context['user_name'] = user.name
                    return render(request, delete_confirmation_template, context)

            elif 'delete_file_id' in request.POST:
                process_deletion(request, True)

        context['form'] = regforms.PublisherAccountReadonly(instance=user.publisher)
        context['puser'] = user
        context['files'] = get_files(user.publisher.directory_name)

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
def publisher_awaiting_superuser(request, _id):
    template = 'coalitions/awaiting_approval.html'
    uid = str(uuid.uuid1())

    context = {'role': constants.SUPER_PUBLISHER_GROUP,
               'user_type': constants.USER_TYPE_PUBLISHER,
               'publisher': request.user.publisher,
               'frameworks': dict(frameworks), }

    try:
        user = models.PSTFUser.objects.get(id=_id, is_active=False)
        user_form = UserUpdateForm(request.POST or None, instance=user)
        account = models.PublisherAccount.objects.get(id=user.publisher.id)
        form = regforms.PublisherAccount(request.POST or None, instance=account)

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
                user.publisher.verified = True
                user.publisher.save()
                user.save()

                messages.success(request, constants.MOVE_TO_CONTRACT_SIGN)
                logger.info(f'{request.user} moved {user}/{user.publisher} to contract signing')
                return redirect(constants.COALITION_S_CONTRACT_SIGNING_USERS + _id)

            elif 'reject' in request.POST:
                user.is_active = False
                user.rejected = True
                user.review_status = models.PSTFUser.ReviewStatus.REJECTED
                user.publisher.verified = False
                user.publisher.save()
                user.save()

                utils.send_email(request, constants.REJECTION_EMAIL_TITLE,
                                 user.email, constants.COMMISERATE_REJECTION, bcc=True)
                messages.success(request, constants.ACCOUNT_REJECTED)
                logger.info(f'{request.user} rejected {user}/{user.publisher}')
                return redirect(constants.COALITION_S_ARCHIVED_USERS + _id)

        context['form'] = form
        context['user_form'] = user_form
        context['puser'] = user
        context['files'] = get_files(user.publisher.directory_name)

    except models.PSTFUser.DoesNotExist:
        messages.error(request, constants.USER_DOES_NOT_EXIST)
        template = constants.COALITIONS_USERS_TEMPLATE
    except Exception as exp:
        logger.error(str(exp) + uid)
        messages.error(request, constants.UNKNOWN_ERROR + uid)

    utils.add_all_superusers(context)

    return render(request, template, context)


@user_group(constants.COALITION_S_GROUP)
def publisher_awaiting_contract_signing_superuser(request, _id):
    template = 'coalitions/awaiting_contract_signing.html'
    uid = str(uuid.uuid1())

    context = {'role': constants.SUPER_PUBLISHER_GROUP,
               'user_type': constants.USER_TYPE_PUBLISHER,
               'publisher': request.user.publisher,
               'frameworks': dict(frameworks), }

    try:
        user = models.PSTFUser.objects.get(id=_id, is_active=False)
        user_form = UserUpdateForm(request.POST or None, instance=user)
        account = models.PublisherAccount.objects.get(id=user.publisher.id)
        form = regforms.PublisherAccount(request.POST or None, instance=account)

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
                user.publisher.verified = True
                user.publisher.save()
                user.save()

                utils.send_email(request, constants.ACTIVATION_EMAIL_TITLE,
                                 user.email, constants.CONGRATULATE_SPUBLISHER_ACTIVATION, bcc=True)
                messages.success(request, constants.ACCOUNT_APPROVED)
                logger.info(f'{request.user} approved {user}')
                return redirect(constants.COALITION_S_APPROVED_USERS + _id)

            elif 'reject' in request.POST:
                user.is_active = False
                user.rejected = True
                user.review_status = models.PSTFUser.ReviewStatus.REJECTED
                user.publisher.verified = False
                user.publisher.save()
                user.save()

                utils.send_email(request, constants.REJECTION_EMAIL_TITLE,
                                 user.email, constants.COMMISERATE_REJECTION, bcc=True)
                messages.success(request, constants.ACCOUNT_REJECTED)
                logger.info(f'{request.user} rejected {user}')
                return redirect(constants.COALITION_S_ARCHIVED_USERS + _id)

        context['form'] = form
        context['user_form'] = user_form
        context['puser'] = user
        context['files'] = get_files(user.publisher.directory_name)

    except models.PSTFUser.DoesNotExist:
        messages.error(request, constants.USER_DOES_NOT_EXIST)
        template = constants.COALITIONS_USERS_TEMPLATE
    except Exception as exp:
        logger.error(str(exp) + uid)
        messages.error(request, constants.UNKNOWN_ERROR + uid)

    utils.add_all_superusers(context)

    return render(request, template, context)


@login_required
def user_profile(request):
    # store user phone number to validate
    phone_number = request.user.phone
    template = 'common/profile.html'
    form = UserUpdateForm(request.POST or None, instance=request.user)
    context = {'form': form}

    if request.POST:
        if form.is_valid():
            form.save()
            if phone_number != form.cleaned_data['phone']:
                send_email(request=request,
                           subject=constants.PROFILE_UPDATE_SUBJECT,
                           message=constants.PROFILE_MOBILE_UPDATE.format(new_mobile=form.cleaned_data['phone']),
                           _from=settings.SENDER_ADDRESS,
                           to=request.user.email)
            messages.success(request, constants.PROFILE_SAVED)
    return render(request, template, context)


def feedback(request):
    # request should be ajax and method should be POST.

    if not (request.is_ajax and request.method == "POST"):
        return redirect(login_view)

    comment = request.POST['comment']

    message = 'Name - ' + request.POST['name'] + '\n' \
              + 'Email - ' + request.POST['email'] + '\n' \
              + 'appCodeName - ' + request.POST['appCodeName'] + '\n' \
              + 'appName - ' + request.POST['appName'] + '\n' \
              + 'appVersion - ' + request.POST['appVersion'] + '\n' \
              + 'cookieEnabled - ' + request.POST['cookieEnabled'] + '\n' \
              + 'language - ' + request.POST['language'] + '\n' \
              + 'platform - ' + request.POST['platform'] + '\n' \
              + 'userAgent - ' + request.POST['userAgent'] + '\n' \
              + 'vendor - ' + request.POST['vendor'] + '\n' \
              + 'url - ' + request.POST['url'] + '\n\n' \
              + 'Comment:' + '\n\n' \
              + '**' + comment + '**'
    # Get subject till new line or 30 characters of the comment
    subject = '[JCS] ' + comment.splitlines()[0][:min(len(comment), 30)]

    try:
        send_email(request=request,
                   subject=subject,
                   message=message,
                   _from=request.POST['email'],
                   to=settings.FEEDBACK_EMAIL,
                   use_html=False)

        # Create a github issue for the feed back
        # Enable creating github issue when required
        # create_github_issue(subject, message)

        return JsonResponse({"status": "Success"}, status=200)

    except Exception as exp:
        uid = str(uuid.uuid1())
        logger.error(str(exp) + uid)
        messages.error(request, constants.EMAIL_NOT_SENT + uid)

        return JsonResponse({"error": ""}, status=400)
