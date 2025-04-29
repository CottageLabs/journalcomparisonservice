import logging
import uuid
from datetime import datetime

from django.utils.timezone import utc
from django.shortcuts import render, redirect
from django.utils.translation import gettext as _
from django.db.utils import IntegrityError
from django.contrib.auth.models import Group
from django.contrib import messages
from django.conf import settings
from ratelimit.decorators import ratelimit
from viewflow.decorators import flow_start_view
from accounts.models import PublisherAccount, NewAccountRequest, EndUserAccount
from login.forms import OTPForm
from login.views import check_rate_limit
from pstf import constants, utils as common_utils
from .utils import execute_psr_next_task, execute_linkreg_next_task, generate_qr_code
from .decorators import check_if_psr_task_finished
from . import forms

from twilio.base.exceptions import TwilioRestException
from viewflow.decorators import flow_view

logger = logging.getLogger(__name__)


def publisher_self_register(request, **kwargs):
    return redirect("/workflow/registration/publisherselfregister/start/")


def terms_conditions(request, **kwargs):
    """Start the workflow and display terms and condition to register"""
    template_url = "super_publisher/terms.html"

    if request.POST:
        return redirect('self_reg_uap')

    return render(request, template_url)


def accept_uap(request):
    """Display terms and condition to register"""
    template_url = "super_publisher/uap.html"

    if request.POST:
        return redirect('publisher_self_register')

    return render(request, template_url)


@flow_start_view
@check_if_psr_task_finished(constants.LOGIN_URL)
def self_register(request, **kwargs):
    """
    Super publisher user self register start page
    :param request: HTTP Request
    :param kwargs:
    :return: Renders the page
    """
    template_url = "super_publisher/self_register.html"
    uid = str(uuid.uuid1())

    context = {}
    form = forms.SelfRegisterForm(request.POST or None)
    context['form'] = form
    context['activation'] = request.activation
    common_utils.add_admin_registration_step(context, '3')
    request.activation.prepare(request.POST or None)

    if request.POST:
        if form.is_valid():
            user = create_or_get_user(form)
            if user.publisher:
                messages.error(request, constants.PUBLISHER_CONSTRAINT)
            else:
                publisher_name = form.cleaned_data['publisher_name']
                request.activation.process.email = user.email
                request.activation.process.publisher_name = publisher_name

                try:
                    user.save()

                    request.activation.process.save()
                    request.activation.done()
                    # Execute next task if available
                    result = execute_psr_next_task(request)
                    if result:
                        return result
                    return redirect(constants.LOGIN_URL)
                except IntegrityError as ie:
                    logger.error(str(ie) + "-" + uid)
                    reason = common_utils.exception_reason(ie)
                    messages.error(request, reason)
                except Exception as exp:
                    logger.error(str(exp) + "-" + uid)
                    messages.error(request, constants.UNKNOWN_ERROR + uid)
        else:
            messages.error(request, constants.INVALID_FORM)

    return render(request, template_url, context)

@ratelimit(key='ip', rate=settings.RATE_LIMIT, method='POST')
@flow_view
@check_if_psr_task_finished(constants.LOGIN_URL)
def email_otp(request, **kwargs):
    """
    Generate and validate email OTP
    :param request: HTTP Request object
    :param kwargs:
    :return:
    """
    template_url = 'common/email_otp.html'
    uid = str(uuid.uuid1())

    request.activation.prepare(request.POST or None)

    context = {}
    form = OTPForm(request.POST or None)
    context['form'] = form
    context['activation'] = request.activation
    context['otp_title'] = _("Enter OTP from email")
    common_utils.add_admin_registration_step(context, '4')
    email = request.activation.process.email

    if not email:
        return redirect('publisher_self_register')

    try:
        user = common_utils.get_pstfuser(email=email)

        if getattr(request, 'limited', False):
            return check_rate_limit(request)

        if request.POST and not 'resend' in request.POST:
            if form.is_valid():
                # Validate OTP
                otp = form.cleaned_data.get("otp")

                if not user.is_emailed_otp_expired():
                    messages.error(request, constants.OTP_EXPIRED)
                elif user.is_emailed_otp_correct(otp):
                    request.activation.done()
                    result = execute_psr_next_task(request)
                    if result:
                        return result
                else:
                    messages.error(request, constants.INVALID_OTP_ENTERED)

            else:
                messages.error(request, constants.INVALID_FORM)

        try:
            resend_otp = request.POST and 'resend' in request.POST
            if not request.POST or resend_otp:
                user.email_otp(request)
                if resend_otp:
                    messages.info(request, constants.OTP_RE_SENT)
        except ConnectionRefusedError as cre:
            logger.error(str(cre) + uid)
            messages.error(request, constants.EMAIL_NOT_SENT + uid)

    except Exception as exp:
        logger.error(str(exp) + uid)
        messages.error(request, constants.UNKNOWN_ERROR + uid)

    return render(request, template_url, context)


@flow_view
@check_if_psr_task_finished(constants.LOGIN_URL)
def publisher_info(request, **kwargs):
    """
    Populates publisher information
    :param request: HTTP Request object
    :return: Renders the page
    """
    template_url = 'super_publisher/publisher_info.html'
    success_url = 'super_publisher/registration_submission.html'

    request.activation.prepare(request.POST or None)

    context = {'user_type': request.activation.flow_class.USER_TYPE}
    form = forms.PublisherAccount(request.POST or None)
    user_form = forms.UserForm(request.POST or None)
    context['form'] = form
    context['activation'] = request.activation
    email = request.activation.process.email
    context['email'] = email
    context['publisher_name'] = request.activation.process.publisher_name
    context['user_form'] = user_form
    common_utils.add_admin_registration_step(context, '8')

    if request.POST:
        if form.is_valid() and user_form.is_valid():
            user_form.cleaned_data['email'] = email
            user = create_or_get_user(user_form)
            # Check if the user is already existing member of JCS
            if common_utils.is_user_part_of_a_group(user):
                messages.error(request, constants.ALREADY_MEMBER_OF_JCS)
            else:
                # User must be deactivated until approved
                user.is_active = False
                instance = form.save()
                user.publisher = instance

                # Add the user to Super Publisher group
                group = Group.objects.get(name=constants.SUPER_PUBLISHER_GROUP)
                user.groups.add(group)

                user.save()

                request.activation.process.name = user.name
                request.activation.process.save()

                request.activation.done()

                img, secret_key = generate_qr_code(user)
                context = {"img": img, 'secret': secret_key}
                # notify the coalition s user about the new request
                common_utils.send_email(request, constants.NEW_ACCOUNT_EMAIL_TITLE, common_utils.get_cs_email_ids(),
                                        constants.NEW_ACCOUNT_EMAIL_BODY)
                return render(request, success_url, context)

        else:
            messages.error(request, constants.INVALID_FORM)

    return render(request, template_url, context)


def publisher_registration_with_id(request, id):
    """
    The registration process for publisher user with registration url
    :param request:
    :param id: registration id
    """
    process_url = '/workflow/registration/publisherlinkregister/start/?id=' + id
    return redirect(process_url)


def ins_user_registration_with_id(request, id):
    """
    The registration process for Institutional users with registration url
    :param request:
    :param id: registration id
    """
    process_url = '/workflow/registration/insuserlinkregister/start/?id=' + id
    return redirect(process_url)


@flow_start_view
@check_if_psr_task_finished(constants.LOGIN_URL)
def link_registration_uap(request):
    template_url = "registration/publisher/uap.html"
    context = {'activation': request.activation}
    common_utils.add_user_registration_step(context, '1')
    request.activation.prepare(request.POST or None)

    if not request.activation.process.link_id:
        request.activation.process.link_id = request.GET['id']

        # Check if the link is valid. If the link is not valid user will be redirected to
        # login screen with error message
        try:
            account = NewAccountRequest.objects.get(id=request.activation.process.link_id)
        except NewAccountRequest.DoesNotExist:
            messages.error(request, constants.INVALID_LINK)
            return redirect(constants.LOGIN_URL)

        if account.created_date and \
                (datetime.utcnow().replace(
                    tzinfo=utc) - account.created_date).days > settings.P_USER_LINK_VALID_IN_DAYS:
            messages.error(request, constants.P_USER_LINK_EXPIRED)
            return redirect(constants.LOGIN_URL)

    if request.POST:
        user_type = request.activation.flow_class.USER_TYPE
        request.activation.done()
        # Execute next task if available
        result = execute_linkreg_next_task(request, user_type)
        if result:
            return result

    return render(request, template_url, context)


@flow_view
@check_if_psr_task_finished(constants.LOGIN_URL)
def link_registration(request, **kwargs):
    template = 'registration/publisher/registration.html'
    form = forms.PublisherLinkRegistrationForm(request.POST or None)
    request.activation.prepare(request.POST or None)
    user_type = request.activation.flow_class.USER_TYPE
    context = {'activation': request.activation, 'form': form, 'user_type': user_type}
    common_utils.add_user_registration_step(context, '2')

    try:
        account = NewAccountRequest.objects.get(id=request.activation.process.link_id)
        if user_type == constants.USER_TYPE_PUBLISHER:
            pub_id = account.account_id
            publisher = PublisherAccount.objects.get(id=pub_id)
            context['pub_name'] = publisher.publisher_name
        else:
            org_id = account.account_id
            organisation = EndUserAccount.objects.get(id=org_id)
            context['org_name'] = organisation.organisation_name
        if request.POST:
            if form.is_valid():
                # email id must match with the email id given at the time of the link creation
                if account.email.lower() == form.cleaned_data['email'].lower():
                    user = create_or_get_user(form)
                    if common_utils.is_user_part_of_a_group(user):
                        messages.error(request, constants.ALREADY_MEMBER_OF_JCS)
                        # delete the account as the user already exist
                        account.delete()
                    else:
                        request.activation.process.email = user.email
                        request.activation.process.name = user.name

                        try:
                            # Publisher User
                            if user_type == constants.USER_TYPE_PUBLISHER:
                                user.publisher = publisher
                                user.save()
                                group = Group.objects.get(name=constants.PUBLISHER_GROUP)
                                user.groups.add(group)
                                user.save()

                            # Institutional User
                            else:
                                user.organisation = organisation
                                user.save()
                                group = Group.objects.get(name=constants.INSTITUTIONAL_USER_GROUP)
                                user.groups.add(group)
                                user.save()

                            request.activation.process.save()
                            request.activation.done()
                            result = execute_linkreg_next_task(request, user_type)
                            if result:
                                return result

                        except IntegrityError as ie:
                            logger.error(str(ie))

                else:
                    messages.error(request, constants.PUBLISHER_EMAIL_DOEST_NOT_MATCH)

            else:
                messages.error(request, constants.INVALID_FORM)

    except NewAccountRequest.DoesNotExist:
        return render(request, "registration/publisher/invalid_id.html", context)

    return render(request, template, context)


@ratelimit(key='ip', rate=settings.RATE_LIMIT, method='POST')
@flow_view
@check_if_psr_task_finished(constants.LOGIN_URL)
def link_reg_email_otp(request):
    """
    Validates the email otp. If validation success, renders registration success page
    :param request: HTTP Request object
    """
    template = "common/email_otp.html"
    form = OTPForm(request.POST or None)
    request.activation.prepare(request.POST or None)
    context = {'activation': request.activation, 'form': form}
    common_utils.add_user_registration_step(context, '3')
    email = request.activation.process.email
    user = common_utils.get_pstfuser(email=email)
    user_type = request.activation.flow_class.USER_TYPE

    # OTP submitted
    if request.POST and 'resend' not in request.POST:
        if getattr(request, 'limited', False):
            return check_rate_limit(request)

        if form.is_valid():
            otp = form.cleaned_data.get("otp")
            if not user.is_emailed_otp_expired():
                messages.error(request, constants.OTP_EXPIRED)
            elif user.is_emailed_otp_correct(otp):
                id = request.activation.process.link_id
                # remove the account with the link
                account = NewAccountRequest.objects.get(id=id)
                account.delete()
                request.activation.done()
                result = execute_linkreg_next_task(request, user_type)
                if result:
                    return result
            else:
                messages.error(request, constants.INVALID_OTP_ENTERED)

        else:
            messages.error(request, constants.INVALID_FORM)

    try:
        resend_otp = request.POST and 'resend' in request.POST

        if resend_otp and getattr(request, 'limited', False):
            return check_rate_limit(request)

        if not request.POST or resend_otp:
            user.email_otp(request)
            if resend_otp:
                messages.info(request, constants.OTP_RE_SENT)
    except ConnectionRefusedError as cre:
        uid = str(uuid.uuid1())
        logger.error(str(cre) + uid)
        messages.error(request, constants.EMAIL_NOT_SENT + uid)
    return render(request, template, context)


@flow_view
@check_if_psr_task_finished(constants.LOGIN_URL)
def registration_success(request, **kwargs):
    success_template = 'registration/publisher/submission.html'
    context = {'activation': request.activation}
    request.activation.prepare(request.POST or None)
    email = request.activation.process.email
    user = common_utils.get_pstfuser(email=email)

    # notify the admin about the new request
    # Check if the user is Institutional User or Publisher user and get respective admin email ids
    admin_email_ds = None
    if common_utils.get_user_group(user) == constants.PUBLISHER_GROUP:
        admin_email_ds = common_utils.get_spublisher_email_ids(user.publisher)
    elif common_utils.get_user_group(user) == constants.INSTITUTIONAL_USER_GROUP:
        admin_email_ds = common_utils.get_institutional_admin_email_ids(user.organisation)

    if admin_email_ds:
        common_utils.send_email(request, constants.NEW_ACCOUNT_EMAIL_TITLE,
                                admin_email_ds,
                                constants.NEW_ACCOUNT_EMAIL_BODY)
    else:
        common_utils.send_email(request, constants.NEW_ACCOUNT_BY_UNKNOWN_USER_EMAIL_TITLE,
                                common_utils.get_cs_email_ids(),
                                constants.NEW_ACCOUNT_BY_UNKNOWN_USER_EMAIL_BODY.format(user=user.email))
    request.activation.done()
    return render(request, success_template, context)


def create_or_get_user(form):
    user, created = common_utils.get_or_create_pstfuser(form.cleaned_data['email'])
    if 'title' in form.cleaned_data:
        user.title = form.cleaned_data['title']
    elif 'title' in form.data:
        user.title = form.data['title']
    if 'name' in form.cleaned_data:
        user.name = form.cleaned_data['name']
    elif 'name' in form.data:
        user.name = form.data['name']
    if 'phone' in form.cleaned_data:
        user.phone = form.cleaned_data['phone']
    elif 'phone' in form.data:
        user.phone = form.data['phone']
    elif 'phone_0' in form.cleaned_data:
        user.phone = form.cleaned_data['phone_0'] + form.cleaned_data['phone_1']
    elif 'phone_0' in form.data:
        user.phone = form.data['phone_0'] + form.data['phone_1']

    return user


def select_user_type(request, **kwargs):
    """ Select type of user for registration """
    template_url = "registration/select_user_type.html"

    if request.POST:
        if 'publisher' in request.POST:
            return redirect('self_reg_tc')
        elif 'institutional_user' in request.POST:
            return redirect('ins_self_reg_tc')

    return render(request, template_url)


def qr_code(request, user_type: str):
    template_url = "registration/common/second_otp_qrcode.html"
    request.activation.prepare(request.POST or None)
    email = request.activation.process.email
    user = common_utils.get_pstfuser(email=email)
    img, secret_key = generate_qr_code(user)

    if request.POST:
        request.activation.done()
        # Execute next task if available
        result = execute_psr_next_task(request)
        if result:
            return result
        return redirect(constants.LOGIN_URL)

    context = {"img": img, 'secret': secret_key, "activation": request.activation}
    if user_type == 'admin':
        common_utils.add_admin_registration_step(context, '5')
    elif user_type == 'user':
        common_utils.add_user_registration_step(context, '4')

    return render(request, template_url, context)


@flow_view
@check_if_psr_task_finished(constants.LOGIN_URL)
def admin_qr_code(request, **kwargs):
    return qr_code(request, 'admin')


@flow_view
@check_if_psr_task_finished(constants.LOGIN_URL)
def user_qr_code(request, **kwargs):
    return qr_code(request, 'user')


@ratelimit(key='ip', rate=settings.RATE_LIMIT, method='POST')
def select_2fa(request, user_type):
    email = request.activation.process.email
    user = common_utils.get_pstfuser(email=email)
    request.activation.prepare(request.POST or None)
    template_select_2fa = 'registration/common/select_2fa.html'
    form = OTPForm()

    if request.method == 'POST':
        if getattr(request, 'limited', False):
            return check_rate_limit(request)

        if 'device' not in request.POST:
            if 'sms' in request.POST or '_resend' in request.POST:
                request.activation.process.otp_type = constants.OTP_TYPE_SMS
        else:
            request.activation.process.otp_type = constants.OTP_TYPE_DEVICE

        request.activation.process.save()

        if form.is_valid() or 'sms' in request.POST:
            if 'sms' in request.POST or '_resend' in request.POST:
                try:
                    user.send_sms()
                except TwilioRestException as tre:
                    logger.error(tre)
                    messages.error(request, constants.SMS_ERROR + str(tre.msg))
                    return render(request, template_select_2fa)

                if '_resend' in request.POST:
                    messages.info(request, constants.SMS_RESENT)
                else:
                    messages.info(request, constants.SMS_SENT)

                logger.info('SMS sent to {}'.format(user))

        request.activation.done()
        # Execute next task if available
        result = execute_psr_next_task(request)
        if result:
            return result
        return redirect(constants.LOGIN_URL)

    context = {'form': form, "activation": request.activation,
               'sms': request.activation.process.otp_type}
    if user_type == 'admin':
        common_utils.add_admin_registration_step(context, '6')
    elif user_type == 'user':
        common_utils.add_user_registration_step(context, '5')

    # Render page where he can select between SMS and TOTP
    return render(request, template_select_2fa, context)


@flow_view
@check_if_psr_task_finished(constants.LOGIN_URL)
def admin_select_2fa(request, **kwargs):
    return select_2fa(request, 'admin')


@flow_view
@check_if_psr_task_finished(constants.LOGIN_URL)
def user_select_2fa(request, **kwargs):
    return select_2fa(request, 'user')


@ratelimit(key='ip', rate=settings.RATE_LIMIT, method='POST')
def verify_otp(request, user_type: str):
    email = request.activation.process.email
    user = common_utils.get_pstfuser(email=email)
    request.activation.prepare(request.POST or None)
    template_otp = 'registration/common/verify_2nd_otp.html'
    form = OTPForm()
    context = {'form': form, "activation": request.activation,
               'sms': request.activation.process.otp_type == constants.OTP_TYPE_SMS}
    if user_type == 'admin':
        common_utils.add_admin_registration_step(context, '7')
    elif user_type == 'user':
        common_utils.add_user_registration_step(context, '6')

    if request.method == 'POST':
        if getattr(request, 'limited', False):
            return check_rate_limit(request)

        form = OTPForm(request.POST)

        if 'device' in request.POST:
            request.activation.process.otp_type = constants.OTP_TYPE_DEVICE
            request.activation.process.save()
        elif 'sms' in request.POST or '_resend' in request.POST:
            try:
                request.activation.process.otp_type = constants.OTP_TYPE_SMS
                request.activation.process.save()
                user.send_sms()
            except TwilioRestException as tre:
                logger.error(tre)
                messages.error(request, constants.SMS_ERROR + str(tre.msg))
                return render(request, template_otp, context)

            if '_resend' in request.POST:
                messages.info(request, constants.SMS_RESENT)
            else:
                messages.info(request, constants.SMS_SENT)

            logger.info('SMS sent to {}'.format(user))

        if form.is_valid() and '_continue' in request.POST:
            # Second OTP has been submitted, either from SMS or TOTP
            otp = form.cleaned_data.get("otp")

            if request.activation.process.otp_type == constants.OTP_TYPE_SMS:

                if not user.is_sms_otp_expired():
                    messages.error(request, constants.OTP_EXPIRED)
                elif user.is_sms_otp_correct(otp):
                        logger.info('SMS OTP verified for {}'.format(user))
                        request.activation.process.valid_otp = True
                        request.activation.process.save()
                        request.activation.done()
                        # Execute next task if available
                        result = execute_psr_next_task(request)
                        if result:
                            return result
                        return redirect(constants.LOGIN_URL)
                else:
                    logger.debug('Incorrect second OTP for user {}.'.format(email))
                    messages.error(request, constants.INVALID_OTP_ENTERED)
                    request.activation.process.valid_otp = False
                    request.activation.process.save()

            elif user.is_totp_valid(otp):
                logger.info('TOTP verified for {}'.format(user))
                request.activation.process.valid_otp = True
                request.activation.process.save()
                request.activation.done()
                # Execute next task if available
                result = execute_psr_next_task(request)
                if result:
                    return result
                return redirect(constants.LOGIN_URL)
            else:
                request.activation.process.valid_otp = False
                request.activation.process.save()
                logger.debug('Incorrect second OTP for user {}.'.format(email))
                messages.error(request, constants.INVALID_OTP_ENTERED)

    context['sms'] = request.activation.process.otp_type == constants.OTP_TYPE_SMS
    # Render page where he can select between SMS and TOTP
    return render(request, template_otp, context)


@flow_view
@check_if_psr_task_finished(constants.LOGIN_URL)
def admin_verify_otp(request, **kwargs):
    return verify_otp(request, 'admin')


@flow_view
@check_if_psr_task_finished(constants.LOGIN_URL)
def user_verify_otp(request, **kwargs):
    return verify_otp(request, 'user')
