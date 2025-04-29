import logging

import django_agent_trust
from django.conf import settings
from django.contrib import messages
from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from ratelimit.decorators import ratelimit
from twilio.base.exceptions import TwilioRestException

from login import forms
from accounts.models import PSTFUser
from pstf import constants, utils

logger = logging.getLogger(__name__)


def check_rate_limit(request):
    """
    Utility function that uses the django-ratelimit package.
    If rate limit is exceeded the view request is aborted and returned to current position
    with an error message.
    :param request:
    :return:
    """
    messages.error(request, constants.RATE_LIMIT_EXCEEDED)

    if 'email' in request.session:
        user = utils.get_pstfuser(email=request.session['email'])
        user.state = PSTFUser.States.LOGGED_OUT
        user.start_cool_off()

        for var in [v for v in ['sms', 'email'] if v in request.session]:
            del request.session[var]
        return redirect_to(request, user)

    return redirect_to(request)


def login_view(request):
    """
    This view renders the login page and posts the user's
    email to the next step, email otp.
    :param request:
    :return:

    URL: /login

    """
    # if already logged in, redirect to dashboard
    if request.user.is_authenticated:
        return redirect_to(request)

    return render(request, 'login/login.html', {'form': forms.LoginForm()})


@ratelimit(key='ip', rate=settings.RATE_LIMIT, method='POST')
def email_otp_view(request):
    """
    This view receives a posted email from LoginForm, verifies that a user exists
    and sends an OTP via email. Instead of submitting an OTP the user can also choose
    to have a new OTP sent.

    URL: /login/email-otp

    :param request:
    :return:
    """
    # Load passed data
    form = forms.LoginForm(request.POST)
    # Prepare template
    template = 'login/email_otp.html'
    # Prepare context
    context = {'form': forms.OTPForm()}

    if request.method == 'POST':

        if getattr(request, 'limited', False):
            return check_rate_limit(request)

        # Validating LoginForm means this will pass when either submitted from
        # step one, the login step or resubmitted to re-send OTP
        if form.is_valid():
            email = form.cleaned_data.get("email")
            try:
                user = utils.get_pstfuser(email=email)

                if user.is_user_cooling_off():
                    messages.error(request, constants.RATE_LIMIT_EXCEEDED)
                    return redirect(login_view)

                # Not sure if this is needed going forward but putting here while testing
                if user.groups.count() != 1:
                    messages.error(request, constants.ONE_GROUP)
                    return redirect(login_view)

                # If user is Publisher or Super Publisher staff, he has to be part of a verified publisher
                if user.is_required_publisher_not_verified():
                    messages.error(request, constants.PUBLISHER_NOT_VERIFIED)
                    return redirect(login_view)

                if not user.is_active:
                    messages.error(request, constants.ACCOUNT_NOT_ACTIVE)
                    return redirect(login_view)

                user.email_otp(request)

                if len(messages.get_messages(request)) == 0:
                    messages.info(request, constants.OTP_SENT)
                request.session['email'] = email

                return render(request, template, context)

            except PSTFUser.DoesNotExist:
                messages.error(request, constants.USER_DOES_NOT_EXIST)
        elif 'email' in request.session:
            # User has reposted for a second OTP to be sent
            email = request.session['email']
            user = utils.get_pstfuser(email=email)

            user.email_otp(request)

            if len(messages.get_messages(request)) == 0:
                messages.info(request, constants.OTP_RE_SENT)
            logger.debug(constants.OTP_RE_SENT)
            return render(request, template, context)

    # If user arrives here by manually entering the path
    elif request.method == 'GET':
        if 'email' in request.session:
            user = utils.get_pstfuser(email=request.session['email'])

            if user.state != PSTFUser.States.EMAIL_OTP_SENT:
                return redirect_to(request, user)
            return render(request, template, context)

    return redirect(login_view)


@ratelimit(key='ip', rate=settings.RATE_LIMIT, method='POST')
def verify_otp_view(request):
    """
    This view verifies an OTP received from email_otp_view and, if verified, depending on whether
    the user has a phone number registered, directs the user to select from possible 2FA methods. Otherwise,
    the user is required to enter a TOTP and is given the opportunity to submit it.

    URL: /login/verify-otp

    :param request:
    :return:
    """
    form = forms.OTPForm(request.POST)

    if request.method == 'POST':

        if getattr(request, 'limited', False):
            return check_rate_limit(request)

        if form.is_valid():
            email = request.session['email']
            pstf_user = utils.get_pstfuser(email=email)

            if not pstf_user.is_emailed_otp_expired():
                messages.error(request, constants.OTP_EXPIRED)
                return redirect_to(request, pstf_user)

            otp = form.cleaned_data.get("otp")

            logger.info("Verifying OTP for {}.".format(email))
            if pstf_user.is_emailed_otp_correct(otp):
                # Resetting form as we don't need to keep the OTP
                form = forms.OTPForm()

                logger.info("OTP verified for {}.".format(email))

                if pstf_user.requires_2fa() and not request.agent.is_trusted:
                    if pstf_user.has_phone():
                        # Render page where he can select between SMS and TOTP
                        return render(request, 'login/select_2fa.html')
                    else:
                        # Otherwise, the user can enter TOTP
                        messages.info(request, constants.ENTER_TOTP)
                else:
                    logger.info("{} logged in".format(pstf_user))
                    # Log user in using Django authentication system
                    login(request, pstf_user)

                    # Mark agent as trusted
                    django_agent_trust.trust_agent(request)
                    return redirect_to(request)
            else:
                logger.debug('Incorrect OTP for user {}.'.format(email))
                messages.error(request, constants.INVALID_OTP_ENTERED)
                return redirect_to(request, pstf_user)
    elif request.method == 'GET':
        # User has arrived here unconventionally
        if 'email' in request.session:
            user = utils.get_pstfuser(email=request.session['email'])

            if user.state != PSTFUser.States.EMAIL_OTP_SENT:
                return redirect_to(request, user)
        else:
            return redirect_to(request)

        form = forms.OTPForm()

    return render(request, 'login/verify_otp.html', {'form': form})


@ratelimit(key='ip', rate=settings.RATE_LIMIT, method='POST')
def verify_2nd_otp_view(request):
    """
    This view verifies the second OTP that the user enters, either having received an SMS or through TOTP.
    If a sms has not been delivered for some reason
    """
    form = forms.OTPForm()

    # The form is only valid if an OTP has been posted from the earlier step
    if request.method == 'POST':

        if getattr(request, 'limited', False):
            return check_rate_limit(request)

        if 'device' not in request.POST:
            form = forms.OTPForm(request.POST)
            if form.is_valid() or 'sms' in request.POST:
                email = request.session['email']
                pstf_user = utils.get_pstfuser(email=email)

                if 'sms' in request.POST or '_resend' in request.POST:
                    form = forms.OTPForm()

                    try:
                        pstf_user.send_sms()
                    except TwilioRestException as tre:
                        logger.error(tre)
                        messages.error(request, constants.SMS_ERROR + str(tre.msg))
                        return render(request, 'login/select_2fa.html')

                    request.session['sms'] = True

                    if '_resend' in request.POST:
                        messages.info(request, constants.SMS_RESENT)
                    else:
                        messages.info(request, constants.SMS_SENT)

                    logger.info('SMS sent to {}'.format(pstf_user))
                elif '_continue' in request.POST:
                    # Second OTP has been submitted, either from SMS or TOTP
                    otp = form.cleaned_data.get("otp")

                    if 'sms' in request.session:
                        if not pstf_user.is_sms_otp_expired():
                            messages.error(request, constants.OTP_EXPIRED)
                        elif pstf_user.is_sms_otp_correct(otp):
                            logger.info('SMS OTP verified for {}'.format(pstf_user))
                            del request.session['sms']
                            # Log user in using Django authentication system
                            login(request, pstf_user)

                            # Mark agent as trusted
                            django_agent_trust.trust_agent(request)
                            return redirect_to(request)
                        else:
                            logger.debug('Incorrect second OTP for user {}.'.format(email))
                            messages.error(request, constants.INVALID_OTP_ENTERED)
                    elif pstf_user.is_totp_valid(otp):
                        logger.info('TOTP verified for {}'.format(pstf_user))
                        # Log user in using Django authentication system
                        login(request, pstf_user)

                        # Mark agent as trusted
                        django_agent_trust.trust_agent(request)
                        return redirect_to(request)
                    else:
                        logger.debug('Incorrect second OTP for user {}.'.format(email))
                        messages.error(request, constants.INVALID_OTP_ENTERED)
        elif 'sms' in request.session:
            del request.session['sms']

    elif request.method == 'GET':
        # User has switched to TOTP or has arrived here unconventionally
        if 'email' in request.session:
            user = utils.get_pstfuser(email=request.session['email'])

            if user.state != PSTFUser.States.TOTP_PENDING and user.state != PSTFUser.States.SMS_OTP_SENT:
                return redirect_to(request, user)

            if request.GET.get('use'):
                request.session['sms'] = False

    context = {'form': form,
               'sms': request.session['sms'] if 'sms' in request.session else False}

    return render(request, 'login/verify_2nd_otp.html', context)


def pstf_logout(request):
    """Logout the user"""
    if request.user.is_authenticated:
        # Delete temporary session variables used for login
        for var in [v for v in ['sms', 'email'] if v in request.session]:
            del request.session[var]

        request.user.log_out()  # changes user model state
        logger.debug('{} logged out'.format(request.user))
        logout(request)  # actual logout function
    return redirect(constants.LOGIN_URL)


def redirect_to(request, user=None):
    """
    Redirects user depending on 1) login state and 2) if logged in, which group user belongs to
    :param user: PSTF user
    :param request: HttpRequest object
    :return: Redirects to correct URL
    """

    if request.user.is_anonymous and not user:
        # No way of identifying user

        return redirect(constants.LOGIN_URL)
    elif request.user.is_authenticated:
        # User known, just need to redirect to correct dashboard

        if request.user.groups.filter(name=constants.COALITION_S_GROUP).exists():
            request.session['role'] = constants.COALITION_S_GROUP
            return redirect(constants.COALITION_S_ACCOUNT_SEARCH)
        elif request.user.groups.filter(name=constants.SUPER_PUBLISHER_GROUP).exists():
            request.session['role'] = constants.SUPER_PUBLISHER_GROUP
            return redirect(constants.SP_DASHBOARD)
        elif request.user.groups.filter(name=constants.PUBLISHER_GROUP).exists():
            request.session['role'] = constants.PUBLISHER_GROUP
            return redirect(constants.PUBLISHER_DASHBOARD)
        elif request.user.groups.filter(name=constants.INSTITUTIONAL_SUPER_USER_GROUP).exists():
            request.session['role'] = constants.INSTITUTIONAL_SUPER_USER_GROUP
            return redirect(constants.INS_SUPER_USER_DASHBOARD)
        elif request.user.groups.filter(name=constants.INSTITUTIONAL_USER_GROUP).exists():
            request.session['role'] = constants.INSTITUTIONAL_USER_GROUP
            return redirect(constants.INS_USER_DASHBOARD)
        else:
            # User is authenticated Django admin
            return redirect('/admin')
    elif user:
        # User has started but not finished logging in

        if user.state == PSTFUser.States.LOGGED_OUT:
            return redirect(constants.LOGIN_URL)
        elif user.state == PSTFUser.States.EMAIL_OTP_SENT:
            return redirect(constants.EMAIL_OTP_URL)
        elif user.state == PSTFUser.States.EMAIL_OTP_CONFIRMED:
            return redirect(constants.VERIFY_OTP_URL)
        elif user.state == PSTFUser.States.SMS_OTP_SENT or user.state == PSTFUser.States.TOTP_PENDING:
            return redirect(constants.VERIFY_2ND_OTP_URL)

