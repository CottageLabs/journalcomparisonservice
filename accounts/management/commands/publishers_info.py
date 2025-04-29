import csv
from django.core.management.base import BaseCommand
from accounts.models import PublisherAccount
from data.models import UploadFile


def write_rows(rows, writer):
    for row in rows:
        writer.writerow(row)


class Command(BaseCommand):
    help = '''
    This command is used to generate publishers data who has and who has not uploaded data for the given years.
    
    Example:
          python manage.py publishers_info --upload_years 2021,2022 --uploaded_only --settings pstf.settings.dev
    '''
    verbosity = 1

    def add_arguments(self, parser):
        parser.add_argument('--upload_years', dest='upload_years', default=None,
                            help='Comma separated data upload years. example --upload_years 2021,2022')
        parser.add_argument('--uploaded_only', action='store_true',
                            help='add this argument to output the data of publishers who uploaded data in the '
                                 'given year(s)')
        parser.add_argument('--not_uploaded_only', action='store_true',
                            help='add this argument to output the data of publishers who have not uploaded data '
                                 'in the given year(s)')

    def handle(self, *args, **options):
        if options.get('verbosity') is not None:
            self.verbosity = options.get('verbosity')

        csv_fieldnames = ['id', 'publisher', 'user name', 'email', 'role']
        # create dynamic file name depending on the arguments
        file_name = 'publishers'
        upload_years = options['upload_years']
        uploaded_only = options['uploaded_only']
        not_uploaded_only = options['not_uploaded_only']

        if uploaded_only:
            file_name += '_uploaded'
        elif not_uploaded_only:
            file_name += '_not_uploaded'

        # either one of the arguments can be used but not both.
        # If both cases are required, no need to pass these arguments
        if uploaded_only and not_uploaded_only:
            self.handle_error("Both --uploaded_only and --not_uploaded_only cannot be used at the same time. "
                              "Use only one option. To get both results, don't use any of them")
            exit(1)

        if upload_years is not None:
            years = upload_years.split(',')
            for year in years:
                file_name += '_' + year
                csv_fieldnames.append(year)
        else:
            years = None

        file_name += '.csv'

        with open(file_name, 'w', newline='') as csvfile:
            self.write(f'Started writing to file {file_name}')
            writer = csv.DictWriter(csvfile, fieldnames=csv_fieldnames)
            writer.writeheader()
            for p in PublisherAccount.objects.all():
                # Get only verified publishers
                if p.verified:
                    # There can be more than one user for a PublisherAccount. Add all these users in sequence so that the
                    # data will not split based on the arguments
                    publisher_rows = []
                    data_uploaded = False
                    for user in p.users.all():
                        if user.is_active:
                            row = {'id': p.id, 'publisher': p.publisher_name, 'user name': user.name, 'email': user.email,
                                   'role': user.groups.first().name}
                            if years:
                                for year in years:
                                    try:
                                        upload_file = UploadFile.objects.filter(publisher=p, data_year=year)
                                        if upload_file and upload_file.count() > 0:
                                            row[year] = 'FILE UPLOADED'
                                            data_uploaded = True

                                    except UploadFile.DoesNotExist:
                                        pass

                            publisher_rows.append(row)

                    if publisher_rows:
                        # write the data depending on the arguments
                        if uploaded_only:
                            if data_uploaded:
                                write_rows(publisher_rows, writer)
                        elif not_uploaded_only:
                            if not data_uploaded:
                                write_rows(publisher_rows, writer)
                        else:
                            write_rows(publisher_rows, writer)

            self.write("Completed.")

    def handle_error(self, message):
        self.stderr.write(self.style.ERROR('Error: {}.'.format(message)))

    def write(self, message):
        if self.verbosity > 0:
            self.stdout.write(message)
