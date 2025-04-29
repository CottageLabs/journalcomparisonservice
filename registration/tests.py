from django.test import TestCase, Client
from django.db.models.functions import Now
from django.core.management import call_command
from unittest.mock import patch
from django.urls import reverse

from accounts.models import PSTFUser
from pstf import utils


def mock_sms(*args, **kwargs):
    pass


def mock_send_email(*args, **kwargs):
    pass


class InsRegistrationTests(TestCase):

    def setUp(self):
        self.client = Client()
        call_command('create_groups', verbosity=0)

    def test_terms_Conditions(self):
        response = self.client.get(reverse('ins_self_reg_tc'))
        self.assertTrue(response.status_code == 200)
        self.assertTemplateUsed(response, "registration/ins_super_user/terms.html")

    def test_uap(self):
        response = self.client.get(reverse('ins_self_reg_uap'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "registration/ins_super_user/uap.html")

    @patch.object(PSTFUser, "send_sms", mock_sms)
    @patch.object(utils, "send_email", mock_send_email)
    def test_registration_workflow(self):
        response = self.client.get("/workflow/registration/insselfregister/start/")
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "registration/ins_super_user/self_register.html")

        data = {'_viewflow_activation-started': '2000-01-01', 'organisation_name': 'Organisation1',
                'email': 'test@test.com', 'phone_0': 'IN', 'phone_1': '1234567890'}
        response = self.client.post("/workflow/registration/insselfregister/start/", data)
        self.assertEqual(response.status_code, 302)
        self.assertTrue('email_otp' in response.url)

        email_otp_url = response.url
        response = self.client.get(email_otp_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "common/email_otp.html")

        user = utils.get_pstfuser(email='test@test.com')
        data = {'_viewflow_activation-started': '2000-01-01', 'otp': user.otp}
        response = self.client.post(email_otp_url, data)
        self.assertEqual(response.status_code, 302)

        qrcode_url = response.url
        response = self.client.get(qrcode_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "registration/common/second_otp_qrcode.html")

        data = {'_viewflow_activation-started': '2000-01-01'}
        response = self.client.post(qrcode_url, data)
        self.assertEqual(response.status_code, 302)

        select_2fa = response.url
        response = self.client.get(select_2fa)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "registration/common/select_2fa.html")

        data = {'_viewflow_activation-started': '2000-01-01', 'sms': True}
        response = self.client.post(select_2fa, data)
        self.assertEqual(response.status_code, 302)
        user.sms_otp = user.get_otp()
        user.sms_otp_generated = Now()
        user.set_state(user.States.SMS_OTP_SENT)

        verify_otp = response.url
        response = self.client.get(verify_otp)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "registration/common/verify_2nd_otp.html")

        data = {'_viewflow_activation-started': '2000-01-01', 'otp': user.sms_otp, 'sms': True, '_continue': True}
        response = self.client.post(verify_otp, data)
        self.assertEqual(response.status_code, 302)

        end_user_info_url = response.url
        response = self.client.get(end_user_info_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "registration/ins_super_user/end_user_info.html")

        data = {'_viewflow_activation-started': '2000-01-01', 'organisation_name': 'Organisation1',
                'organisation_type': 'LIBRARY', 'name': 'Test User', 'postal_address1': 'address 1',
                'postcode': '12345', 'city': 'city1', 'country': 'IND',
                'ror_id': '052gg0110', 'esf_name': 'Someone', 'esf_email': 'someone@test.com',
                'home_page_url': 'www.xyz.com', 'open_access_agreement': '12345'}
        response = self.client.post(end_user_info_url, data)
        self.assertEqual(response.status_code, 200)

        user = utils.get_pstfuser(email='test@test.com')
        self.assertEqual(user.organisation.organisation_name, 'Organisation1')
        self.assertEqual(user.organisation.organisation_type, 'LIBRARY')


class PublisherRegistrationTests(TestCase):

    def setUp(self) -> None:
        self.client = Client()
        call_command('create_groups', verbosity=0)
        call_command('create_services_and_trade_bodies')

    def test_terms_conditions(self):
        response = self.client.get(reverse('self_reg_tc'))
        self.assertTrue(response.status_code == 200)
        self.assertTemplateUsed(response, "super_publisher/terms.html")

    def test_uap(self):
        response = self.client.get(reverse('self_reg_uap'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "super_publisher/uap.html")

    def test_self_register(self):
        response = self.client.get("/workflow/registration/publisherselfregister/start/")
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "super_publisher/self_register.html")

    @patch.object(PSTFUser, "send_sms", mock_sms)
    @patch.object(utils, "send_email", mock_send_email)
    def test_registration_workflow(self):
        response = self.client.get("/workflow/registration/publisherselfregister/start/")
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "super_publisher/self_register.html")

        data = {'_viewflow_activation-started': '2000-01-01', 'publisher_name': 'Publisher1',
                'email': 'test@test.com', 'phone_0': 'IN', 'phone_1': '1234567890'}
        response = self.client.post("/workflow/registration/publisherselfregister/start/", data)
        self.assertEqual(response.status_code, 302)
        self.assertTrue('email_otp' in response.url)

        email_otp_url = response.url
        response = self.client.get(email_otp_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "common/email_otp.html")

        user = utils.get_pstfuser(email='test@test.com')
        data = {'_viewflow_activation-started': '2000-01-01', 'otp': user.otp}
        response = self.client.post(email_otp_url, data)
        self.assertEqual(response.status_code, 302)

        qrcode_url = response.url
        response = self.client.get(qrcode_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "registration/common/second_otp_qrcode.html")

        data = {'_viewflow_activation-started': '2000-01-01'}
        response = self.client.post(qrcode_url, data)
        self.assertEqual(response.status_code, 302)

        select_2fa = response.url
        response = self.client.get(select_2fa)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "registration/common/select_2fa.html")

        data = {'_viewflow_activation-started': '2000-01-01', 'sms': True}
        response = self.client.post(select_2fa, data)
        self.assertEqual(response.status_code, 302)
        user.sms_otp = user.get_otp()
        user.sms_otp_generated = Now()
        user.set_state(user.States.SMS_OTP_SENT)

        verify_otp = response.url
        response = self.client.get(verify_otp)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "registration/common/verify_2nd_otp.html")

        data = {'_viewflow_activation-started': '2000-01-01', 'otp': user.sms_otp, 'sms': True, '_continue': True}
        response = self.client.post(verify_otp, data)
        self.assertEqual(response.status_code, 302)

        publisher_info_url = response.url
        response = self.client.get(publisher_info_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "super_publisher/publisher_info.html")

        data = {'_viewflow_activation-started': '2000-01-01', 'publisher_name': 'Publisher1',
                'name': 'Test User', 'postal_address1': 'address 1',
                'postcode': '12345', 'city': 'city1', 'country': 'IND',
                'esf_name': 'Someone', 'esf_email': 'someone@test.com',
                'url': 'www.xyz.com', 'journal': 'journal1', 'issn': '1234-4567', 'services': '1',
                'member_of_cope': 'False', 'member_of_publisher_trade_body': 'False'}
        response = self.client.post(publisher_info_url, data)
        self.assertEqual(response.status_code, 200)

        user = utils.get_pstfuser(email='test@test.com')
        self.assertEqual(user.publisher.publisher_name, 'Publisher1')
        self.assertEqual(user.publisher.issn, '1234-4567')
