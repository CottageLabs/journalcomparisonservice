from django.core.files.storage import default_storage
from django.core.management import BaseCommand

from data.models import InformationPower, FairOpenAccessAlliance
from upload.models import UploadFile
from upload.spreadsheets import ValidateSpreadsheet


class Command(BaseCommand):

    def add_arguments(self, parser):
        parser.add_argument('--upload_id', type=int)
        parser.add_argument('--all', action='store_true')

    def handle(self, *args, **options):
        if not options['all']:
            upload_id = options['upload_id']

            if upload_id is None:
                print('You need to either specify an --upload_id or --all.')
                return

            try:
                upload_files = [UploadFile.objects.get(pk=upload_id)]
            except UploadFile.DoesNotExist:
                print(f'Upload with the id {upload_id} does not exist.')
                return
        else:
            upload_files = UploadFile.objects.all()

        for upload_file in upload_files:
            print(f'Processing: {upload_file.framework} framework from publisher {upload_file.publisher} '
                  f'for the year {upload_file.data_year}\n')
            if len(upload_files) > 1:
                print(f'Total of {len(upload_files)}\n')

            try:
                file = default_storage.open(upload_file.upload_file.name, 'rb')
            except FileNotFoundError:
                print(f'File not found: "{upload_file.upload_file.name}"')
                return

            try:
                vds = ValidateSpreadsheet(upload_file, file)
            except Exception as e:
                print(str(e))
                return

            if vds.errors:
                print('Could not import data because of spreadsheet error/s.')
                return

            if vds.framework.acronym == 'ip':
                c = InformationPower.objects.filter(upload_id=upload_file.id).count()
            elif vds.framework.acronym == 'foaa':
                c = FairOpenAccessAlliance.objects.filter(upload_id=upload_file.id).count()

            if c > 0:
                print(f'\nThere are already {c} objects from that upload in the database.\n\n')

            if input('Are you certain you want to import into the database all data from:\n'
                     f'"{vds.upload.name}", ({vds.journals} journal/s)? (y/N) ').lower() == 'y':

                if vds.framework.acronym == 'ip':
                    InformationPower.objects.filter(upload_id=upload_file.id).delete()
                    InformationPower.objects.bulk_create(vds.objects)
                    # This is to push the" document to elastic search
                    # TODO: Implement this when there is a requirement to push when upload is done
                    # create_ip_documents(vds.objects)

                elif vds.framework.acronym == 'foaa':
                    FairOpenAccessAlliance.objects.filter(upload_id=upload_file.id).delete()
                    FairOpenAccessAlliance.objects.bulk_create(vds.objects)

                print(f'{len(vds.objects)} {vds.framework.name} objects created')
            else:
                print('Aborted')
