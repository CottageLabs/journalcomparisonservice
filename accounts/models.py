import logging
import re

from datetime import datetime

import phonenumbers
import pyotp
import uuid

from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.utils.timezone import utc
from django.utils.translation import gettext_lazy as _
from django.db.models.functions import Now
from phonenumber_field.modelfields import PhoneNumberField
from django.db import models
from django.conf import settings
from phonenumbers.phonenumberutil import NumberParseException

from pstf import constants
from pstf.utils import send_email
from .managers import PSTFUserManager
from unidecode import unidecode, UnidecodeError

from twilio.rest import Client

logger = logging.getLogger(__name__)


class ServicesModel(models.Model):
    name = models.CharField(max_length=100)
    abbreviation = models.CharField(max_length=30)

    def __str__(self):
        return self.name


class TradeBodiesModel(models.Model):
    name = models.CharField(max_length=100)
    abbreviation = models.CharField(max_length=30)

    def __str__(self):
        return self.name


class JournalOnline(models.TextChoices):
    # Taken from https://www.inasp.info/project/journals-online-project
    AJO = "AJO", _("African Journals Online")
    BJO = "BJO", _("Bangladesh Journals Online")
    CAMJOL = "CAMJOL", _("Central American Journals Online")
    MJOL = "MJOL", _("Mongolia Journals Online")
    NJOL = "NJOL", _("Nepal Journals Online")
    PJOL = "PJOL", _("Philippines Journals Online")
    SJOL = "SJOL", _("Sri Lanka Journals Online")
    VJOL = "VJOL", _("Vietnam Journals Online")


class PublisherAccount(models.Model):
    """
    Model to store super publisher account details
    """

    publisher_name = models.CharField(max_length=100)
    # Name of the person who will sign Legal Agreement with ESF, on behalf of publisher
    esf_name = models.CharField(max_length=100)
    # email id of the person who is responsible to sign agreement on behalf of the publisher
    esf_email = models.EmailField()
    postal_address1 = models.CharField(max_length=100)
    postal_address2 = models.CharField(max_length=100, blank=True)
    postal_address3 = models.CharField(max_length=100, blank=True)
    postcode = models.CharField(max_length=15)
    city = models.CharField(max_length=150)
    country = models.CharField(max_length=150)
    url = models.URLField(max_length=300)
    journal = models.CharField(max_length=200)
    issn = models.CharField(max_length=50)
    services = models.ManyToManyField(ServicesModel)
    services_other = models.CharField(max_length=100, blank=True)
    inasp_journals = models.CharField(max_length=100, choices=JournalOnline.choices, blank=True)
    member_of_cope = models.BooleanField(default=False)
    member_of_publisher_trade_body = models.BooleanField(default=False)
    trade_bodies = models.ManyToManyField(TradeBodiesModel)
    trade_bodies_other = models.CharField(max_length=100, blank=True)
    verified = models.BooleanField(default=False)
    created = models.DateTimeField(auto_now_add=True)

    @property
    def directory_name(self):
        """
        This method returns a sanitized combination of the name of the publisher and
        the primary key id to create a unique directory name.
        Uploads from all users of that publisher are stored in this directory.
        :return:
        """

        publisher = str(self.publisher_name).lower().replace(' ', '_')

        try:
            return unidecode(publisher) + '_' + str(self.id)
        except UnidecodeError as ude:
            return "".join([c for c in publisher if re.match(r'\w', c)]) + '_' + str(self.id)

    def __str__(self):
        return self.publisher_name


class OrganisationType(models.TextChoices):
    INS_UNI = "INS_UNI", _("Institution/University")
    LIBRARY = "LIBRARY", _("Library consortium")
    FUNDER = "FUNDER", _("cOAlition S funder")


class EndUserAccount(models.Model):
    """
    Model to store End User account details
    """
    organisation_name = models.CharField(max_length=100)
    organisation_type = models.CharField(max_length=50, choices=OrganisationType.choices, default="INS_UNI")
    postal_address1 = models.CharField(max_length=100)
    postal_address2 = models.CharField(max_length=100, blank=True)
    postal_address3 = models.CharField(max_length=100, blank=True)
    postcode = models.CharField(max_length=15)
    city = models.CharField(max_length=150)
    country = models.CharField(max_length=150)
    ror_id = models.CharField(max_length=150, blank=True)
    home_page_url = models.URLField(max_length=300)
    # Name of the person who will sign Legal Agreement with ESF, on behalf of the Organisation
    esf_name = models.CharField(max_length=100)
    # email id of the person who is responsible to sign agreement on behalf of the Organisation
    esf_email = models.EmailField()
    open_access_agreement = models.CharField(max_length=300)
    verified = models.BooleanField(default=False)
    created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.organisation_name} ({self.country})'


def get_sender(raw_phonenumber: str) -> str:
    """
    Utility function to determine the country code of the recipient of the SMS.
    Further documentation:
    https://support.twilio.com/hc/en-us/articles/223133867-Using-Alphanumeric-Sender-ID-with-Messaging-Services
    https://support.twilio.com/hc/en-us/articles/223133767-International-support-for-Alphanumeric-Sender-ID
    :param raw_phonenumber:
    :return:
    """
    try:
        phonenumber = phonenumbers.parse(raw_phonenumber, None)

        if phonenumber.country_code == 44:
            return settings.TWILIO_SENDER_ID
    except NumberParseException:
        pass

    return settings.TWILIO_PHONENUMBER


class PSTFUser(AbstractBaseUser, PermissionsMixin):
    """
    Customised user that does not use passwords but requires 2FA through email and
    a second device. This user class has several methods to facilitate this multistep
    login workflow.
    """

    class States(models.TextChoices):
        LOGGED_OUT = 'LO', _('User is logged out.')
        EMAIL_OTP_SENT = 'EOS', _('OTP has been sent to user\'s email address.')
        EMAIL_OTP_CONFIRMED = 'EOC', _('OTP emailed to user has been confirmed.')
        TOTP_PENDING = 'TP', _('TOTP is pending.')
        # TOTP_CONFIRMED = 'TC', _('TOTP has been confirmed.')
        SMS_OTP_SENT = 'SOS', _('OTP has been sent to user\'s mobile phone.')
        # SMS_OTP_CONFIRMED = 'SOC', _('OTP sent by SMS has been confirmed.')
        LOGGED_IN = 'LI', _('User is logged in.')

    class ReviewStatus(models.TextChoices):
        AWAITING_REVIEW = "ar", "awaiting_review"
        AWAITING_CONTRACT_SIGNING = "acs", "awaiting_contract_signing"
        APPROVED = "app", "approved"
        REJECTED = "rej", "rejected"

    title = models.CharField(blank=True, default='', max_length=10)
    email = models.EmailField(_('email address'), unique=True)
    name = models.CharField(max_length=300)
    phone = PhoneNumberField(null=True, blank=True)
    is_active = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)
    created = models.DateTimeField(auto_now_add=True)
    otp = models.CharField(max_length=8, null=True)
    otp_generated = models.DateTimeField(null=True)
    sms_otp = models.CharField(max_length=8, null=True)
    sms_otp_generated = models.DateTimeField(null=True)
    hotp_counter = models.IntegerField(default=0)
    last_login = models.DateTimeField(null=True)
    mfa_hash = models.CharField(max_length=50, blank=True, default=pyotp.random_base32)
    state = models.CharField(max_length=3, default=States.LOGGED_OUT, choices=States.choices)
    totp_enabled = models.BooleanField(default=False)
    publisher = models.ForeignKey(PublisherAccount, on_delete=models.CASCADE, blank=True,
                                  null=True, related_name="users")
    organisation = models.ForeignKey(EndUserAccount, on_delete=models.CASCADE, blank=True,
                                     null=True, related_name="end_users")
    rejected = models.BooleanField(default=False)
    review_status = models.CharField(max_length=6, default=ReviewStatus.AWAITING_REVIEW, choices=ReviewStatus.choices)
    rate_exceeded = models.DateTimeField(null=True)
    current_session_key = models.CharField(max_length=40, blank=True, null=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    objects = PSTFUserManager()

    def save(self, *args, **kwargs):
        if self.email:
            self.email = self.email.lower()
        super().save(*args, **kwargs)

    def start_cool_off(self):
        """
        Sets a timestamp to when user exceeded rate so that he can be denied
        further service at start login page.
        :return:
        """
        self.rate_exceeded = Now()
        self.save()

    def is_user_cooling_off(self) -> bool:
        """
        Check whether user has exceeded rate limit within the last settings.RATE_LIMIT_SECONDS
        :return:
        """
        elapsed = (datetime.utcnow().replace(tzinfo=utc) - self.rate_exceeded).total_seconds()\
            if self.rate_exceeded else None
        return self.rate_exceeded and elapsed <= settings.RATE_LIMIT_SECONDS

    def is_required_publisher_not_verified(self) -> bool:
        """
        If a user belongs to either Super Publisher or Publisher group they
        need to "belong" to a verified publisher
        :return:
        """
        return (self.groups.filter(name=constants.PUBLISHER_GROUP).exists()
                or self.groups.filter(name=constants.SUPER_PUBLISHER_GROUP).exists()) \
                and (not self.publisher or not self.publisher.verified)

    def is_totp_valid(self, totp) -> bool:
        """
        Checks if an OTP is valid and logs user in if so.
        :param totp:
        :return:
        """
        if pyotp.TOTP(str(self.mfa_hash)).now() == totp:
            self.log_in()

            return True

        return False

    def email_otp(self, request):
        """
        Sends a HOTP generated OTP to the user's email and
        timestamps the event.
        :return:
        TODO Exception handling, timeouts, log response
        """
        self.otp = self.get_otp()
        self.otp_generated = Now()

        send_email(request, constants.OTP_SENT_EMAIL_TITLE,
                   self.email, constants.OTP_SENT_EMAIL_BODY.format(o=self.otp, m=settings.OTP_VALID_MINUTES))

        self.set_state(self.States.EMAIL_OTP_SENT)

        logger.debug('OTP emailed to {}'.format(self.email))

    def is_emailed_otp_expired(self) -> bool:
        """
        Checks if a submitted OTP was sent via email within a certain elapsed time and is valid.
        """
        elapsed = (datetime.utcnow().replace(tzinfo=utc) - self.otp_generated).total_seconds()

        return self.otp_generated and elapsed <= settings.OTP_VALID

    def is_emailed_otp_correct(self, otp: str) -> bool:
        """
        Checks if a submitted OTP sent via email is correct.
        If the user does not require 2fa then this concludes the authentication workflow and the
        user's state is set to logged in.

        NOTE this does not actually authenticate the user against Django's authentication system
        :param otp:
        :return:
        """
        if str(otp) == self.otp:

            self.otp = None

            if self.requires_2fa():
                self.set_state(self.States.EMAIL_OTP_CONFIRMED)
            else:
                self.log_in()

            return True

        logger.debug('Failed emailed OTP attempt for {}.'.format(self.email))
        return False

    def is_sms_otp_expired(self) -> bool:
        """
        Checks if a submitted OTP sent via sms within a certain elapsed time.
        :return:
        """
        return self.sms_otp_generated and \
               (datetime.utcnow().replace(tzinfo=utc) - self.sms_otp_generated).total_seconds() <= settings.OTP_VALID

    def is_sms_otp_correct(self, otp: str) -> bool:
        """
        Checks if a submitted OTP sent via sms is correct and logs user in.

        NOTE this does not actually authenticate the user against Django's authentication system
        :param otp:
        :return:
        """
        if str(otp) == self.sms_otp:
            self.sms_otp = None
            self.log_in()

            return True

        logger.debug('Failed texted OTP attempt for {}.'.format(self.email))
        return False

    def get_state(self) -> States:
        """
        Returns the user's current state.
        :return:
        """
        return self.States(self.state)

    def set_state(self, state: States):
        """
        Set user's state
        :param state:
        :return:
        """
        self.state = state
        self.save()

    def has_phone(self) -> bool:
        """
        Checks if user has registered a phonenumber.
        :return:
        """
        return self.phone is not None

    def increment_hotp(self) -> int:
        """
        Increments and returns the user's HOTP counter for OTP generation
        :return:
        """
        self.hotp_counter += 1
        self.save()
        return int(self.hotp_counter)

    def requires_2fa(self) -> bool:
        """
        Checks if a user is required to authenticate using 2FA.
        :return:
        """
        if self.last_login and \
                (datetime.utcnow().replace(tzinfo=utc) - self.last_login).days <= settings.DAY_LIMIT_FOR_2FA:
            return False

        return True

    def send_sms(self):
        """
        Sends a HOTP generated OTP to the user's phone and
        timestamps the event.
        TODO Exception handling, timeouts, log response
        :return:
        """
        self.sms_otp = self.get_otp()
        self.sms_otp_generated = Now()

        client = Client(settings.TWILIO_ACCOUNT_SID,
                        settings.TWILIO_AUTH_TOKEN)

        message = client.messages \
            .create(body=constants.SMS_BODY.format(o=self.sms_otp, m=settings.OTP_VALID_MINUTES),
                    from_=get_sender(str(self.phone)),
                    to=str(self.phone))

        self.set_state(self.States.SMS_OTP_SENT)

        logger.debug('OTP texted to {}.'.format(self.email))
        logger.debug(message)

    def get_otp(self):
        """
        Calculates the user's HOTP based on his incremented counter and returns.
        :return:
        """
        hotp = pyotp.HOTP(str(self.mfa_hash))
        return hotp.at(self.increment_hotp())

    def __str__(self):
        return self.email

    def log_out(self):
        """
        Sets user's state to logged out
        """
        self.set_state(self.States.LOGGED_OUT)

    def log_in(self):
        """
        Sets user's state to logged in
        :return:
        """
        self.set_state(self.States.LOGGED_IN)


class NewAccountRequest(models.Model):
    """ Model to store details of new user account creation"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    account_type = models.CharField(max_length=30)
    account_id = models.IntegerField()
    email = models.EmailField(null=True)
    created_date = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if self.email:
            self.email = self.email.lower()
        super().save(*args, **kwargs)
