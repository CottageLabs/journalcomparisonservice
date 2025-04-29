import logging
import uuid

from django.shortcuts import render, redirect
from django.db.utils import IntegrityError
from django.contrib.auth.models import Group
from django.contrib import messages
from viewflow.decorators import flow_start_view, flow_view
from pstf import constants, utils as common_utils
from .utils import execute_psr_next_task, generate_qr_code
from .decorators import check_if_psr_task_finished
from . import ins_forms, forms, views

logger = logging.getLogger(__name__)


def ins_self_register_workflow(request, **kwargs):
    return redirect("/workflow/registration/insselfregister/start/")


def terms_conditions(request, **kwargs):
    """Start the workflow and display terms and condition to register"""
    template_url = "registration/ins_super_user/terms.html"

    if request.POST:
        return redirect('ins_self_reg_uap')

    return render(request, template_url)


def accept_uap(request):
    """Display terms and condition to register"""
    template_url = "registration/ins_super_user/uap.html"

    if request.POST:
        return redirect('ins_self_register')

    return render(request, template_url)


@flow_start_view
@check_if_psr_task_finished(constants.LOGIN_URL)
def ins_self_register(request, **kwargs):
    """
    Institutional user self register start page
    :param request: HTTP Request
    :param kwargs:
    :return: Renders the page
    """
    template_url = "registration/ins_super_user/self_register.html"
    uid = str(uuid.uuid1())

    context = {}
    form = ins_forms.InsSelfRegisterForm(request.POST or None)
    context['form'] = form
    context['activation'] = request.activation
    common_utils.add_admin_registration_step(context, '3')
    request.activation.prepare(request.POST or None)

    if request.POST:
        if form.is_valid():
            user = views.create_or_get_user(form)
            if user.organisation:
                messages.error(request, constants.ORGANISATION_CONSTRAINT)
            else:
                request.activation.process.email = user.email
                request.activation.process.organisation_name = form.cleaned_data['organisation_name']

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


@flow_view
@check_if_psr_task_finished(constants.LOGIN_URL)
def end_user_info(request, **kwargs):
    """
    Populates End User information
    :param request: HTTP Request object
    :return: Renders the page
    """
    template_url = 'registration/ins_super_user/end_user_info.html'
    success_url = 'registration/ins_super_user/registration_submission.html'

    request.activation.prepare(request.POST or None)

    context = {'user_type': request.activation.flow_class.USER_TYPE}
    form = ins_forms.EndUserAccount(request.POST or None, initial={'organisation_type': 'LIBRARY'})
    user_form = forms.UserForm(request.POST or None)
    context['form'] = form
    context['activation'] = request.activation
    email = request.activation.process.email
    context['email'] = email
    context['organisation_name'] = request.activation.process.organisation_name
    context['user_form'] = user_form
    common_utils.add_admin_registration_step(context, '8')
    if request.POST:
        if form.is_valid() and user_form.is_valid():
            user_form.cleaned_data['email'] = email
            user = views.create_or_get_user(user_form)
            # Check if the user is already existing member of JCS
            if common_utils.is_user_part_of_a_group(user):
                messages.error(request, constants.ALREADY_MEMBER_OF_JCS)
            else:
                # User must be deactivated until approved
                user.is_active = False
                instance = form.save()
                user.organisation = instance

                # Add the user to Super Publisher group
                group = Group.objects.get(name=constants.INSTITUTIONAL_SUPER_USER_GROUP)
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
