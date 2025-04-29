from datetime import date
from django.test import TestCase, Client, RequestFactory
from django.template import Template, Context
from django.urls import reverse
from django.contrib.auth import login
from django.contrib.auth.models import Group
from django.contrib.sessions.middleware import SessionMiddleware
from unittest.mock import patch

from accounts.models import PublisherAccount, PSTFUser
from pstf import utils

class UploadFileViewTests(TestCase):
    def setUp(self):

        from pstf import constants

        self.client = Client()
        self.factory = RequestFactory()

        self.super_publisher_group, _ = Group.objects.get_or_create(name=constants.SUPER_PUBLISHER_GROUP)
        self.publisher_group, _ = Group.objects.get_or_create(name=constants.PUBLISHER_GROUP)

    def create_user(self):
        user_email = 'some987@user.com'
        publisher_name = 'Publisher123XX'
        publisher, create = PublisherAccount.objects.get_or_create(publisher_name=publisher_name)

        self.user, _ = PSTFUser.objects.get_or_create(email=user_email, is_active=True, publisher=publisher)
    def super_publisher_login(self):
        self.create_user()
        self.super_publisher_group.user_set.add(self.user)
        self.custom_login(self.user)

    def publisher_login(self):
        self.create_user()
        self.publisher_group.user_set.add(self.user)
        self.custom_login(self.user)

    def custom_login(self, user):
        # Create a request object
        request = self.factory.get('/')
        # Add session middleware to the request
        middleware = SessionMiddleware()
        middleware.process_request(request)
        request.session.save()
        # Use the login function to attach the user to the request
        login(request, user)
        # Save the session
        request.session.save()
        # Ensure the client is using this session
        session_key = request.session.session_key
        self.client.cookies['sessionid'] = session_key

    def test_super_publisher_upload_file_view_foaa_enabled(self):
        self.super_publisher_login()
        with patch('pstf.utils.disable_foaa_functionality', return_value=False):
            response = self.client.get(reverse('s_publisher_dashboard'), {})
            self.assertEqual(response.status_code, 200)
            self.assertFalse("Framework : Information Power" in str(response.content))

    def test_super_publisher_upload_file_view_foaa_disabled(self):
        self.super_publisher_login()
        with patch('pstf.utils.disable_foaa_functionality', return_value=True):
            response = self.client.get(reverse('s_publisher_dashboard'), {})
            self.assertEqual(response.status_code, 200)
            self.assertTrue("Framework : Information Power" in str(response.content))

    def test_publisher_upload_file_view_foaa_enabled(self):
        self.publisher_login()
        with patch('pstf.utils.disable_foaa_functionality', return_value=False):
            response = self.client.get(reverse('publisher_dashboard'), {})
            self.assertEqual(response.status_code, 200)
            self.assertFalse("Framework : Information Power" in str(response.content))

    def test_publisher_upload_file_view_foaa_disabled(self):
        self.publisher_login()
        with patch('pstf.utils.disable_foaa_functionality', return_value=True):
            response = self.client.get(reverse('publisher_dashboard'), {})
            self.assertEqual(response.status_code, 200)
            self.assertTrue("Framework : Information Power" in str(response.content))

    def test_foaa_enabled(self):
        with patch('datetime.date') as mock_date:
            mock_date.today.return_value = date(2024, 1, 8)
            disable_foaa = utils.disable_foaa_functionality()
            self.assertFalse(disable_foaa)

    def test_foaa_disabled(self):
        with patch('datetime.date') as mock_date:
            mock_date.today.return_value = date(2024, 11, 8)
            disable_foaa = utils.disable_foaa_functionality()

            self.assertTrue(disable_foaa)
