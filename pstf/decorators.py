import logging
import uuid
from typing import Callable

from django.shortcuts import redirect
from django.contrib import messages

from pstf import constants
from accounts import models

logger = logging.getLogger(__name__)


def user_group(group_name: str, redirect_to: str = constants.LOGIN_URL):
    """
    Decorator to check if the user is coalitionS user.
    Otherwise renders the 'render_to' template
    :param group_name:
    :param redirect_to: template to render
    """
    def decorator(func):
        def wrapper(request, id=None):
            if request.user.groups.filter(name=group_name).exists():
                if id:
                    return func(request, id)
                else:
                    return func(request)
            else:
                return redirect(redirect_to)
        return wrapper
    return decorator


def is_institutional_user(func: Callable):
    """
    Decorator to check if the user is institutional user or institutional admin user.
    Otherwise redirects to login page
    """
    def wrapper(request, id=None, **kwargs):
        if request.user.groups.filter(name__in=[constants.INSTITUTIONAL_SUPER_USER_GROUP,
                                      constants.INSTITUTIONAL_USER_GROUP]).exists():
            if id:
                return func(request, id)
            elif 'issns' in kwargs:
                return func(request, kwargs['issns'])
            elif 'journal_id' in kwargs:
                return func(request, kwargs['journal_id'], kwargs['year'] if 'year' in kwargs else None)
            elif 'type' in kwargs:
                if 'query' in kwargs:
                    return func(request, kwargs['type'], kwargs['query'])
                else:
                    return func(request, kwargs['type'])
            else:
                return func(request)
        else:
            if not request.user.is_authenticated:
                # save this url the to reload after login
                request.session[constants.PREVIOUS_URL] = request.get_full_path()

            messages.error(request, constants.INSTITUTIONAL_USERS_ONLY)
            return redirect(constants.LOGIN_URL)
    return wrapper


def is_publisher_user(func: Callable):
    """
    Decorator to check if the user is publisher user or publisher admin user.
    Otherwise redirects to login page
    """
    def wrapper(request, id=None, **kwargs):
        if request.user.groups.filter(name__in=[constants.SUPER_PUBLISHER_GROUP,
                                      constants.PUBLISHER_GROUP]).exists():
            if id:
                return func(request, id)
            elif 'issns' in kwargs:
                return func(request, kwargs['issns'])
            elif 'journal_id' in kwargs:
                return func(request, kwargs['journal_id'], kwargs['year'] if 'year' in kwargs else None)
            elif 'type' in kwargs and 'query' in kwargs:
                return func(request, kwargs['type'], kwargs['query'])
            else:
                return func(request)
        else:
            messages.error(request, constants.PUBLISHER_USERS_ONLY)
            return redirect(constants.LOGIN_URL)
    return wrapper


def validate_ins_user_request(func: Callable):
    """
    Decorator to check if the user belongs to same organization as the requested user.
    """
    def wrapper(request, id):
        if not request.user.is_authenticated:
            # User isn't logged in because his session has expired
            return redirect(constants.LOGIN_URL)

        try:
            user = models.PSTFUser.objects.get(id=id)
            user_org_id = user.organisation.id
            admin_org_id = request.user.organisation.id
            if request.user.groups.filter(name=constants.INSTITUTIONAL_SUPER_USER_GROUP).exists()\
                    and user_org_id == admin_org_id:
                if id:
                    return func(request, id)
                else:
                    return func(request)
            else:
                messages.error(request, constants.USER_DOES_NOT_EXIST)
                return redirect(constants.SINSTITUTIONAL_USERS_DASHBOARD)
        except models.PSTFUser.DoesNotExist:
            messages.error(request, constants.USER_DOES_NOT_EXIST)
            return redirect(constants.SINSTITUTIONAL_USERS_DASHBOARD)
        except Exception as exp:
            uid = str(uuid.uuid1())
            logger.exception(str(exp) + uid)
            messages.error(request, constants.UNKNOWN_ERROR + uid)
            return redirect(constants.SINSTITUTIONAL_USERS_DASHBOARD)
    return wrapper


def validate_publisher_user_request(func: Callable):
    """
    Decorator to check if the user belongs to same publisher as the requested user.
    """
    def wrapper(request, id):
        if not request.user.is_authenticated:
            # User isn't logged in because his session has expired
            return redirect(constants.LOGIN_URL)

        try:
            user = models.PSTFUser.objects.get(id=id)
            user_publisher_id = user.publisher.id
            admin_publisher_id = request.user.publisher.id
            if request.user.groups.filter(name=constants.SUPER_PUBLISHER_GROUP).exists()\
                    and user_publisher_id == admin_publisher_id:
                if id:
                    return func(request, id)
                else:
                    return func(request)
            else:
                messages.error(request, constants.USER_DOES_NOT_EXIST)
                return redirect(constants.SPUBLISHER_USERS_DASHBOARD)
        except models.PSTFUser.DoesNotExist:
            messages.error(request, constants.USER_DOES_NOT_EXIST)
            return redirect(constants.SPUBLISHER_USERS_DASHBOARD)
        except Exception as exp:
            uid = str(uuid.uuid1())
            logger.exception(str(exp) + uid)
            messages.error(request, constants.UNKNOWN_ERROR + uid)
            return redirect(constants.SPUBLISHER_USERS_DASHBOARD)
    return wrapper
