from django.contrib.messages import get_messages
from django.core import mail
from django.core.management import call_command
from django.test import TestCase

from django.urls import reverse
from django.contrib.auth.models import Group
from accounts.models import PSTFUser
from login.forms import LoginForm, OTPForm
from pstf import constants


class LoginTest(TestCase):
    def setUp(self):
        PSTFUser.objects.create(email="inactive@user.com")
        PSTFUser.objects.create(email="active@user.com", is_active=True)
        call_command('create_groups', verbosity=0)

    def test_view_uses_correct_template(self):
        response = self.client.get(reverse('pstf-login'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'login/login.html')
        self.assertIsInstance(response.context['form'], LoginForm)

    def test_login_form(self):
        form_data = {'email': 'normal@user.com'}
        form = LoginForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_unactivated_user_can_not_login(self):
        user = PSTFUser.objects.get(email='inactive@user.com')
        response = self.client.post(reverse('email-otp'), {'email': user.email})
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(str(messages[0]), constants.ONE_GROUP)

    def test_email_otp(self):
        user = PSTFUser.objects.get(email="active@user.com")
        group = Group.objects.get(name=constants.COALITION_S_GROUP)
        user.groups.add(group)
        user.save()
        response = self.client.post(reverse('email-otp'), {'email': user.email})
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn(user.email, mail.outbox[0].to)
        user.refresh_from_db()
        self.assertIsNotNone(user.otp_generated)
        self.assertEqual(len(user.otp), 6)
        self.assertEqual(user.state, 'EOS')
        self.assertEqual(user.hotp_counter, 1)
        self.assertIsInstance(response.context['form'], OTPForm)
        self.assertIn(user.otp, mail.outbox[0].body)

    def test_otp_form(self):
        form_data = {'otp': '666666'}
        form = OTPForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_verify_otp_no_phone(self):
        user = PSTFUser.objects.get(email="active@user.com")
        group = Group.objects.get(name=constants.COALITION_S_GROUP)
        user.groups.add(group)
        user.save()
        self.client.post(reverse('email-otp'), {'email': user.email})
        user.refresh_from_db()
        session = self.client.session
        session['email'] = user.email
        session.save()
        response = self.client.post(reverse('verify-otp'), {'otp': user.otp})
        messages = list(get_messages(response.wsgi_request))

        self.assertTemplateUsed(response, 'login/verify_otp.html')
        self.assertEqual(str(messages[0]), constants.ENTER_TOTP)



