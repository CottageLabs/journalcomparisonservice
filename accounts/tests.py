import csv
import os
import pathlib
from typing import List

import phonenumbers
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.management import call_command, CommandError
from django.test import TestCase
from phonenumbers.phonenumberutil import NumberParseException

from accounts.models import PublisherAccount, get_sender
from pstf import constants


def read_lines(filename: str) -> List[List[str]]:
    with open(filename, 'r') as csvfile:
        csvreader = csv.reader(csvfile)
        return [r for r in csvreader]


class UsersManagersTests(TestCase):

    def setUp(self) -> None:
        """
        User model is used by most test methods
        :return:
        """
        self.user_model = get_user_model()

    def tearDown(self) -> None:
        """
        Remove files outputted by CLI commands
        :return:
        """
        for f in ['publishers.csv', 'users.csv', 'users2.csv']:
            if pathlib.Path(f).resolve().is_file():
                os.remove(f)

    def test_create_user(self) -> None:
        user = self.user_model.objects.create_user(email='normal@user.com', password='foo')
        self.assertEqual(user.email, 'normal@user.com')
        self.assertFalse(user.is_active)
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)

        try:
            # username is None for the AbstractUser option
            # username does not exist for the AbstractBaseUser option
            self.assertIsNone(user.username)
        except AttributeError:
            pass
        with self.assertRaises(TypeError):
            self.user_model.objects.create_user()
        with self.assertRaises(ValueError):
            self.user_model.objects.create_user(email='')
        with self.assertRaises(ValueError):
            self.user_model.objects.create_user(email='', password="foo")

    def test_create_superuser(self) -> None:
        admin_user = self.user_model.objects.create_superuser(email='super@user.com', password='foo')
        self.assertEqual(admin_user.email, 'super@user.com')
        self.assertTrue(admin_user.is_active)
        self.assertTrue(admin_user.is_staff)
        self.assertTrue(admin_user.is_superuser)

        try:
            # username is None for the AbstractUser option
            # username does not exist for the AbstractBaseUser option
            self.assertIsNone(admin_user.username)
        except AttributeError:
            pass
        with self.assertRaises(ValueError):
            self.user_model.objects.create_superuser(email='super@user.com', password='foo', is_superuser=False)

    def test_assign_user_to_group(self) -> None:
        """
        Test assigning user to group
        :return:
        """
        user, _ = self.user_model.objects.get_or_create(email='normal@user.com')
        publisher, _ = Group.objects.get_or_create(name=constants.PUBLISHER_GROUP)
        publisher.user_set.add(user)

        self.assertTrue(user.groups.filter(name=constants.PUBLISHER_GROUP).exists())

    def test_creating_active_user(self) -> None:
        """
        Test assigning user to group
        :return:
        """
        user, _ = self.user_model.objects.get_or_create(email='normal@user.com', is_active=True)
        self.assertTrue(user.is_active)

    def test_cli_users_info(self) -> None:
        """
        Test that the command line command 'users_info' outputs a file with default
        headers.
        :return:
        """
        # It is required to pass file name
        with self.assertRaises(CommandError):
            call_command('users_info', verbosity=0)

        # Creating groups or error message "Error: Invalid group name: SuperPublisher." is printed
        call_command('create_groups', verbosity=0)

        call_command('users_info', 'users.csv', verbosity=0)

        self.assertTrue(pathlib.Path('users.csv').resolve().is_file())

        lines = read_lines('users.csv')

        self.assertEqual(['name', 'email', 'publisher name'], lines[0])

    def test_cli_users_info_with_user(self) -> None:
        """
        Test that the command line command 'users_info' outputs a file containing information about
        a created publisher user.
        :return:
        """
        user_email = 'somexx-125@user.com'
        publisher_name = 'RandomPublishingHOUSE'
        publisher, _ = PublisherAccount.objects.get_or_create(publisher_name=publisher_name)

        user, _ = self.user_model.objects.get_or_create(email=user_email, is_active=True, publisher=publisher)

        group, _ = Group.objects.get_or_create(name=constants.PUBLISHER_GROUP)

        group.user_set.add(user)

        call_command('users_info', 'users2.csv', verbosity=0, group='Publisher')

        self.assertTrue(pathlib.Path('users2.csv').resolve().is_file())

        lines = read_lines('users2.csv')

        self.assertTrue(user_email in lines[1])
        self.assertTrue(publisher_name in lines[1])

    def test_cli_publishers_info(self) -> None:
        """
        Test that the command line command 'publishers_info' outputs a file containing information about
        publishers.
        :return:
        """
        user_email = 'some987@user.com'
        publisher_name = 'Publisher123XX'
        publisher, create = PublisherAccount.objects.get_or_create(publisher_name=publisher_name, verified=True)

        user, _ = self.user_model.objects.get_or_create(email=user_email, is_active=True, publisher=publisher)

        group, _ = Group.objects.get_or_create(name=constants.PUBLISHER_GROUP)

        group.user_set.add(user)

        call_command('publishers_info', verbosity=0)

        self.assertTrue(pathlib.Path('publishers.csv').resolve().is_file())

        lines = read_lines('publishers.csv')

        self.assertEqual(len(lines), 2)
        self.assertEqual(['id', 'publisher', 'user name', 'email', 'role'], lines[0])
        self.assertIn(publisher_name, lines[1])
        self.assertIn(user_email, lines[1])
        self.assertEqual('Publisher', lines[1][4])

    def test_numbers(self):
        numbers = '+447814087136', '+491738413211', '+46700373660', '+4535332916', '+13256650285', '+393760798210', \
            '+46790607509', '+61409492348', '+31620241228', '+573003045338', '+441223267043', '+61410731078',\
            '+441133437252', '+12084264538', '+447980003483', '+34686724352', '+306945927322', '+33620204908', '+4432'

        for number in numbers:
            try:
                phonenumber = phonenumbers.parse(number)
            except NumberParseException:
                pass

            if phonenumber.country_code == 44:
                self.assertEqual(get_sender(number), settings.TWILIO_SENDER_ID)
            else:
                self.assertEqual(get_sender(number), settings.TWILIO_PHONENUMBER)