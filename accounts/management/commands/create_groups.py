from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group
from pstf import constants


class Command(BaseCommand):

    def handle(self, *args, **options):
        verbosity = options.get('verbosity') if options.get('verbosity') is not None else 1

        for group in constants.ALL_GROUPS:
            group_obj, created = Group.objects.get_or_create(name=group)
            if verbosity > 0 and created:
                self.stdout.write(f"Created {group} group")

        if verbosity > 0:
            self.stdout.write("Completed creation of groups")
