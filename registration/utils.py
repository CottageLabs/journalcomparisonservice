from typing import Tuple

import pyotp
from accounts.utils import totp_qrcode
from pstf import constants
from pstf.utils import execute_next_task
from django.conf import settings

from . import flows


def execute_psr_next_task(request):
    """
    Executes Publisher Self Registration next task
    :param request: HTTP Request object
    :return:
    """
    return execute_next_task(request, flows.PublisherSelfRegisterFlow)


def execute_linkreg_next_task(request, user_type: str):
    """
    Executes Publisher verification next task
    :param user_type:
    :param request: HTTP Request object
    :return:
    """
    if user_type == constants.USER_TYPE_PUBLISHER:
        return execute_next_task(request, flows.PublisherLinkRegisterFlow)
    # Institutional User
    else:
        return execute_next_task(request, flows.InsUserLinkRegisterFlow)


def generate_qr_code(user: str) -> Tuple[str, str]:
    """
    Generates QR code image
    :param user: User to whom qrcode is generated
    :return: qrcode and secret key
    """
    totp = pyotp.TOTP(user.mfa_hash)
    url = totp.provisioning_uri(name=user.email, issuer_name=settings.ISSUER_NAME)

    return totp_qrcode(url), user.mfa_hash