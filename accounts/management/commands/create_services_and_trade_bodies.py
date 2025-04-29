from django.core.management.base import BaseCommand

from accounts.models import ServicesModel, TradeBodiesModel

services = [("DOAJ", 'Directory of Open Access Journals'), ("INASP", "INASP Journal online"), ("PUBMED", "PubMed"),
            ("SCP", "Scopus"), ("WOS", "Web of Science"), ("Other", "Other")]


trade_bodies = [("ALPSP", 'Association of Learned and Professional Society Publishers'),
                ("OASPA", 'Open Access Scholarly Publishing Association'), ("SOCPC", "Society Publishers' Coalition"),
                ("SSP", "Society for Scholarly Publishing"), ("STMA", "STM Association"), ("Other", "Other")]


class Command(BaseCommand):

    def handle(self, *args, **options):
        if not ServicesModel.objects.all():
            for service in services:
                s = ServicesModel(abbreviation=service[0], name=service[1])
                s.save()

        if not TradeBodiesModel.objects.all():
            for trade_body in trade_bodies:
                t = TradeBodiesModel(abbreviation=trade_body[0], name=trade_body[1])
                t.save()
