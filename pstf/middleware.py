from django.contrib.auth import logout
from django.contrib import messages
from django.utils.deprecation import MiddlewareMixin
from django.contrib.sessions.models import Session

from pstf import constants


class UserSessionMiddleware(MiddlewareMixin):
    """This middleware class monitors all requests and checks two things.
        A) whether user has a second active session and if so, deletes that session
        B) whether an already logged-in user has been deactivated and if so, logs that user out """
    @staticmethod
    def process_request(request):
        user = request.user
        if not user.is_authenticated:
            return
        else:
            # Check if the user has logged on multiple session and logout from other sessions
            if user.current_session_key:
                if user.current_session_key != request.session.session_key:
                    # Delete the old session
                    Session.objects.filter(session_key=user.current_session_key).delete()
                    user.current_session_key = request.session.session_key
                    user.save()
            else:
                user.current_session_key = request.session.session_key
                user.save()

        if not user.is_active:
            user.log_out()
            logout(request)
            messages.error(request, constants.DEACTIVATED)


class PreviousPageHandler(MiddlewareMixin):
    """Check if previous has been accessed and remove from session"""
    @staticmethod
    def process_request(request):
        if request.user.is_authenticated:
            if constants.PREVIOUS_URL in request.session:
                # Check if previous url in session is same as current url. If same that means that
                # the user is accessing previous url. Remove the url from session as the url is accessed.
                # If not removed, it may go into infinite loop
                if request.get_full_path() == request.session[constants.PREVIOUS_URL]:
                    del request.session[constants.PREVIOUS_URL]