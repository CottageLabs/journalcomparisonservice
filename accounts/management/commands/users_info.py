import csv
from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group
from accounts.models import PSTFUser


class Command(BaseCommand):
    help = '''
        Export Users info to a CSV file.

        Options:
          --group GROUP_NAME  Group name to filter by (default: SuperPublisher)
          valid group names are:
          SuperPublisher
          InstitutionalSuperUser
          Publisher
          InstitutionalUser
          CoalitionS

        Example:
          python manage.py users_info output.csv --group SuperPublisher --settings pstf.settings.dev
        '''

    def add_arguments(self, parser):
        parser.add_argument('output_file', help='Output file path')
        parser.add_argument('--group', dest='group_name', default='SuperPublisher', help='Group name to filter by')

    def handle(self, *args, **options):
        columns = ['name', 'email']
        csv_fieldnames = ['name', 'email']
        group_name = options['group_name']

        try:
            Group.objects.get(name=options['group_name'])
        except Group.DoesNotExist:
            self.handle_error('Invalid group name: {}'.format(group_name))

        if group_name == 'SuperPublisher' or group_name == 'Publisher':
            columns.append('publisher__publisher_name')
            csv_fieldnames.append('publisher name')
        elif group_name == 'InstitutionalSuperUser' or group_name == 'InstitutionalUser':
            columns.append('organisation__organisation_name')
            csv_fieldnames.append('institution name')

        users = PSTFUser.objects.filter(groups__name=group_name).values(*columns)

        with open(options['output_file'], 'w', newline='') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=csv_fieldnames)
            writer.writeheader()
            for user in users:
                row = {'name': user['name'], 'email': user['email']}
                if group_name == 'SuperPublisher' or group_name == 'Publisher':
                    row['publisher name'] = user['publisher__publisher_name']
                elif group_name == 'InstitutionalSuperUser' or group_name == 'InstitutionalUser':
                    row['institution name'] = user['organisation__organisation_name']
                writer.writerow(row)

    def handle_error(self, message):
        self.stderr.write(self.style.ERROR('Error: {}.'.format(message)))

