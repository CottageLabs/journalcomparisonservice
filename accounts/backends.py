# users/backends.py
# https://docs.djangoproject.com/en/3.2/topics/auth/customizing/#writing-an-authentication-backend

from django.contrib.auth.backends import ModelBackend
from django.contrib.auth.hashers import check_password
from pstf import utils
from .models import PSTFUser


class PSTFBackend(ModelBackend):
    def authenticate(self, request, **kwargs):
        email = kwargs['username']
        try:
            pstf_user = utils.get_pstfuser(email=email)

            # Check password if it's a superuser
            if pstf_user.is_superuser and check_password(kwargs['password'], pstf_user.password):
                return pstf_user
            # Otherwise check state
            elif pstf_user.state == PSTFUser.States.LOGGED_IN:
                return pstf_user
        except PSTFUser.DoesNotExist:
            pass

        return None

    def get_user(self, user_id):
        try:
            return PSTFUser.objects.get(pk=user_id)
        except PSTFUser.DoesNotExist:
            return None
