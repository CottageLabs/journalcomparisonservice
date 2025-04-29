from viewflow import flow
from viewflow.base import this, Flow
from viewflow import frontend
from pstf import constants
from .models import *
from . import views, ins_views


@frontend.register
class PublisherSelfRegisterFlow(Flow):
    USER_TYPE = constants.USER_TYPE_PUBLISHER
    process_class = PublisherSelfRegisterProcess

    start = (
        flow.Start(
            views.self_register
        )).Next(this.email_otp)

    email_otp = (flow.View(
            views.email_otp
        )).Next(this.qr_code)

    qr_code = (flow.View(
        views.admin_qr_code
    )).Next(this.select_2fa)

    select_2fa = (flow.View(
        views.admin_select_2fa
    )).Next(this.verify_otp)

    verify_otp = (flow.View(
        views.admin_verify_otp
    )).Next(this.valid_otp)

    valid_otp = (flow.If(lambda activation: activation.process.valid_otp)
                 .Then(this.publisher_info)
                 .Else(this.select_2fa))

    publisher_info = (flow.View(
            views.publisher_info
        )).Next(this.end)

    end = flow.End()


@frontend.register
class PublisherLinkRegisterFlow(Flow):
    USER_TYPE = constants.USER_TYPE_PUBLISHER

    process_class = PublisherLinkRegisterProcess

    start = (flow.Start(views.link_registration_uap)).Next(this.uap)

    uap = (flow.View(
        views.link_registration
    )).Next(this.email_otp)

    email_otp = (flow.View(
        views.link_reg_email_otp
    )).Next(this.qr_code)

    qr_code = (flow.View(
        views.user_qr_code
    )).Next(this.select_2fa)

    select_2fa = (flow.View(
        views.user_select_2fa
    )).Next(this.verify_otp)

    verify_otp = (flow.View(
        views.user_verify_otp
    )).Next(this.valid_otp)

    valid_otp = (flow.If(lambda activation: activation.process.valid_otp)
                 .Then(this.success_message)
                 .Else(this.select_2fa))

    success_message = (flow.View(
        views.registration_success
    )).Next(this.end)

    end = flow.End()


@frontend.register
class InsSelfRegisterFlow(Flow):
    USER_TYPE = constants.USER_TYPE_INSTITUTIONAL
    process_class = InsSelfRegisterProcess

    start = (
        flow.Start(
            ins_views.ins_self_register
        )).Next(this.email_otp)

    email_otp = (flow.View(
            views.email_otp
        )).Next(this.qr_code)

    qr_code = (flow.View(
        views.admin_qr_code
    )).Next(this.select_2fa)

    select_2fa = (flow.View(
        views.admin_select_2fa
    )).Next(this.verify_otp)

    verify_otp = (flow.View(
        views.admin_verify_otp
    )).Next(this.valid_otp)

    valid_otp = (flow.If(lambda activation: activation.process.valid_otp)
                 .Then(this.success)
                 .Else(this.select_2fa))

    success = (flow.View(
            ins_views.end_user_info
        )).Next(this.end)

    end = flow.End()


@frontend.register
class InsUserLinkRegisterFlow(PublisherLinkRegisterFlow):
    USER_TYPE = constants.USER_TYPE_INSTITUTIONAL

    process_class = InsUserLinkRegisterProcess
