import csv
from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group

from phonenumber_field.phonenumber import to_python as to_phone_number

from accounts.models import PSTFUser, PublisherAccount, EndUserAccount, ServicesModel
from pstf import constants

"""
This script is used to create users defined in the csv file.

Different sheets are created for different environments. Choose the right sheet to create users

Execute the script as follows to create the users

python manage.py create_users_from_csv --csv_file <csv file absolute path> --settings pstf.settings.dev

Change settings file as per requirement
"""

def create_enduser():
    institution_name = "Test Institution"

    test_endusers = EndUserAccount.objects.filter(organisation_name=institution_name)
    if test_endusers.exists():
        test_enduser = test_endusers.first()
    else:
        test_enduser = EndUserAccount()
        test_enduser.organisation_name = institution_name
        test_enduser.organisation_type = "LIBRARY"
        test_enduser.postal_address1 = "address 1"
        test_enduser.postal_address2 = "address 2"
        test_enduser.postcode = "KY12 1HP"
        test_enduser.city = "London"
        test_enduser.country = "GBR"
        test_enduser.home_page_url = "http://institutionurl.com"
        test_enduser.esf_name = "test user"
        test_enduser.esf_email = "test@test.com"
        test_enduser.open_access_agreement = "ESAC registry 1234"
        test_enduser.verified = True
        test_enduser.save()

    return test_enduser


def create_publisher():
    publisher_name = "Test Publisher"

    test_pubs = PublisherAccount.objects.filter(publisher_name=publisher_name)
    if test_pubs.exists():
        test_pub = test_pubs.first()
    else:
        test_pub = PublisherAccount.objects.create(publisher_name=publisher_name)
        test_pub.esf_name = "Tester"
        test_pub.esf_email = "tester@testpublisher.com"
        test_pub.uname = "pub1"
        test_pub.postal_address1 = "123 address"
        test_pub.postal_address2 = "address 2"
        test_pub.postcode = "KY12 1HP"
        test_pub.city = "London"
        test_pub.country = "GBR"
        test_pub.url = "http://publisherurl.comm"
        test_pub.journal = "Test Journal"
        test_pub.issn = "1234-4567"
        test_pub.services.set([ServicesModel.objects.filter(abbreviation="DOAJ").first()])
        test_pub.verified = True
        test_pub.save()

    return test_pub


class Command(BaseCommand):
    help = 'Create users from a CSV file'

    def add_arguments(self, parser):
        parser.add_argument('--csv_file', type=str, help='The CSV file to process')

    def handle(self, *args, **kwargs):
        csv_file = kwargs['csv_file']

        if not csv_file:
            self.stdout.write(self.style.ERROR(f'No file path given using --csv_file.'))
            return

        # create the accounts if not available
        test_publisher = create_publisher()
        test_enduser = create_enduser()

        with open(csv_file, newline='') as file:
            reader = csv.DictReader(file)
            for row in reader:
                email = row['Email']
                raw_phone = row['Phone']
                name = row['Display Name']
                role = row['Role'].lower()

                try:
                    # Ensure the phone number is in international format
                    if not raw_phone.startswith('+'):
                        raw_phone = '+' + raw_phone

                    phone = to_phone_number(raw_phone)

                    # if the user exists, do nothing
                    if PSTFUser.objects.filter(email=email).exists():
                        self.stdout.write(self.style.WARNING(f'User with email {email} already exists. Skipping.'))
                        continue

                    # create new user
                    user = PSTFUser.objects.create_user(
                        name=name, email=email, phone=phone
                    )

                    # assign groups and organisations
                    if role == "admin":
                        group = Group.objects.get(name=constants.COALITION_S_GROUP)
                        user.groups.add(group)
                    elif role == "publisher admin":
                        group = Group.objects.get(name=constants.SUPER_PUBLISHER_GROUP)
                        user.groups.add(group)
                        user.publisher = test_publisher
                    elif role == "publisher user":
                        group = Group.objects.get(name=constants.PUBLISHER_GROUP)
                        user.groups.add(group)
                        user.publisher = test_publisher
                    elif role == "institutional admin":
                        group = Group.objects.get(name=constants.INSTITUTIONAL_SUPER_USER_GROUP)
                        user.groups.add(group)
                        user.organisation = test_enduser
                    elif role == "institutional user":
                        group = Group.objects.get(name=constants.INSTITUTIONAL_USER_GROUP)
                        user.groups.add(group)
                        user.organisation = test_enduser

                    user.is_active = True
                    user.rejected = False
                    user.review_status = PSTFUser.ReviewStatus.APPROVED

                    user.save()

                    self.stdout.write(self.style.SUCCESS(f'Successfully created {role}: {email}'))

                except Exception as exp:
                    self.stdout.write(self.style.ERROR(f'error occurred while creating user {email}. Error {exp}'))
