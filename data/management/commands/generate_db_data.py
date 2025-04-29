import time
from decimal import Decimal

from random import seed, randrange, choice
from typing import List

from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group

from data.models import *
from accounts.models import *

# Using time to see in order to get proper random
seed(time.time())


def generate_issn() -> str:
    return ''.join([str(randrange(10)) for i in range(4)]) + "-" + ''.join([str(randrange(10)) for i in range(4)])


latin_words = ['habeas', 'hinc', 'naturam', 'expellas', 'furca', 'tamen', 'usque', 'recurret', 'nemo', 'saltat',
               'sobrius', 'nil', 'sine', 'numine', 'deleo', 'eloquens', 'proluvier', 'adiuvo', 'aliquotiens']
publisher_ending = ['press', 'university press', 'books']

journal_prestart = ['new', 'international']
journal_start = ['journal of', ]
journal_ending = ['review', 'digest', 'communications', 'letters', 'studies']
journal_middle = ['applied', 'international', 'kinetic', 'atomic', 'natural', 'therapeutic', 'general', 'tectonic',
                  'mathematical', 'physiological', 'economical', 'geographical', 'religious', 'historical',
                  'lingual']
journal_main = ['mathematics', 'solar energy', 'psychology', 'sociology', 'ecology', 'fissures', 'literature',
                'natural', 'phenomenal', 'politics', 'physiology', 'physics', 'biology', 'electronics',
                'sports science', 'physiotherapy', 'oncology', 'philosophy', 'psychology', 'anthropology',
                'business', 'accountancy', 'geology', 'palaeontology', 'chemistry', 'genetics', 'zoology',
                'physiology', 'pathology', 'economics', 'law', 'criminology', 'geography', 'arts', 'history',
                'archeology', 'medicine', 'nano technology']


def generate_publisher() -> str:
    return ' '.join([choice(latin_words) for i in range(randrange(2, 3))] + [choice(publisher_ending)]).title()


def generate_discipline() -> str:
    return choice([d[0] for d in Discipline.choices])


def generate_issue_publication_frequency() -> str:
    return choice([d[0] for d in PublicationFrequency.choices])


def generate_operations() -> str:
    return choice([d[0] for d in Operations.choices])


def generate_title() -> str:
    title = [choice(journal_prestart)] if randrange(0, 10) > 8 else []
    title += [journal_start[0]] if randrange(0, 10) > 8 else []
    title += [choice(journal_middle)] if randrange(0, 10) > 5 else []
    title += [choice(journal_main), choice(journal_ending)]

    return ' '.join(title).title()


def generate_price_breakdown(length: int, target: int) -> List[Decimal]:
    weight = 100
    target_sum_total = target * weight
    breakdown = []
    proportion = Decimal(target_sum_total / length)

    for i in range(length - 1):
        if sum(breakdown) + (proportion * 2) > Decimal(target_sum_total * .9):
            max_price = Decimal((target_sum_total - sum(breakdown)) / 2)
        else:
            max_price = proportion * 2

        breakdown.append(Decimal(randrange(0, round(max_price))))

    breakdown.append(Decimal(target_sum_total - sum(breakdown)))

    return [b/weight for b in breakdown]


class Command(BaseCommand):

    def add_arguments(self, parser):
        parser.add_argument('journals', type=int)

    def handle(self, *args, **options):
        verbosity = options.get('verbosity') if options.get('verbosity') is not None else 1
        pub_admin_user_group = Group.objects.get(name=constants.SUPER_PUBLISHER_GROUP)
        pub1, created = PublisherAccount.objects.get_or_create(publisher_name="Jones Words Inc", country="GBR",
                                                               verified=True)
        pub_u1, created = PSTFUser.objects.get_or_create(email="puser1@publisher1.com")
        pub_u1.publisher = pub1
        pub_u1.groups.add(pub_admin_user_group)
        pub_u1.save()

        pub2, created = PublisherAccount.objects.get_or_create(publisher_name="Ramas Paragraphs Ltd", country="GBR",
                                                               verified=True)
        pub_u2, created = PSTFUser.objects.get_or_create(email="puser2@publisher2.com")
        pub_u2.publisher = pub2
        pub_u2.groups.add(pub_admin_user_group)
        pub_u2.save()

        ip_upload_file, created = UploadFile.objects.get_or_create(
            original_file_name="IWA_Information_Power_v1.1.xlsx",
            upload_file="elsevier_1/IWA_Information_Power_v1.1.xlsx",
            framework="ip",
            publisher=pub1,
            data_year=2022,
            journals=114,
            size=14,
        )

        foaa_upload_file, created = UploadFile.objects.get_or_create(
            original_file_name="foaa_data.xlsx",
            upload_file="frontiers_media_2/foaa_data.xlsx",
            framework="foaa",
            publisher=pub2,
            data_year=2022,
            journals=137,
            size=16,
        )

        i = 0
        ips = 0
        foaas = 0

        to_year = datetime.utcnow().year
        from_year = to_year - 5

        for i in range(options['journals']):
            if i % 2:
                price_breakdown = generate_price_breakdown(8, 1)

                # create and save an article
                ip = InformationPower()
                ip.year = randrange(from_year, to_year)
                ip.upload = ip_upload_file
                ip.journal_title = generate_title()
                ip.publisher = generate_publisher()
                ip.issn = generate_issn()
                ip.discipline = generate_discipline()
                ip.owner_ror_id = "Requested"
                ip.apc_list_price_range_lower = float(randrange(100) / 100)
                ip.apc_list_price_range_higher = float(randrange(100) / 100)
                ip.apc_list_price_currency = "USD"
                ip.subscription_list_price_range_lower = float(randrange(100) / 100)
                ip.subscription_list_price_range_higher = float(randrange(100) / 100)
                ip.subscription_list_price_for_member_of_the_association_of_americ = float(randrange(100) / 100)
                ip.subscription_list_price_currency = "GBP"
                ip.research_articles_published = randrange(500)
                ip.acceptance_rate = float(randrange(1000, 10000) / 100)
                ip.rejection_rate = float(randrange(1000, 10000) / 100)
                ip.issue_publication_frequency = generate_issue_publication_frequency()
                ip.median_number_reviews = randrange(10)
                ip.median_time_submission_to_first_decision = float(randrange(1000, 10000) / 100)
                ip.median_time_peer_review = float(randrange(1000, 10000) / 100)
                ip.median_time_acceptance_to_publication = float(randrange(1000, 10000) / 100)
                ip.counter_5_total_item_requests = randrange(10000, 100000)
                ip.price_breakdown_journal_community_development = price_breakdown[0]
                ip.price_breakdown_journal_submission_on_first_decision = price_breakdown[1]
                ip.price_breakdown_peer_review = price_breakdown[2]
                ip.price_breakdown_services_acceptance_publication = price_breakdown[3]
                ip.price_breakdown_services_post_publication = price_breakdown[4]
                ip.price_breakdown_platform_development_support = price_breakdown[5]
                ip.price_breakdown_sales_marketing = price_breakdown[6]
                ip.price_breakdown_author_customer_support = price_breakdown[7]
                ip.save()
                ips += 1
            else:
                price_breakdown = generate_price_breakdown(7, 1)

                foaa = FairOpenAccessAlliance()
                foaa.year = randrange(from_year, to_year)
                foaa.upload = foaa_upload_file
                foaa.journal_title = generate_title()
                foaa.publisher = generate_publisher()
                foaa.issn = generate_issn()
                foaa.discipline = generate_discipline()
                foaa.owner_ror_id = "Requested"
                foaa.apc_list_price_range_lower = float(randrange(100) / 100)
                foaa.apc_list_price_range_higher = float(randrange(100) / 100)
                foaa.apc_list_price_currency = "USD"
                foaa.subscription_list_price_range_lower = float(randrange(100) / 100)
                foaa.subscription_list_price_range_higher = float(randrange(100) / 100)
                foaa.subscription_list_price_for_member_of_the_association_of_americ = float(randrange(100) / 100)
                foaa.subscription_list_price_currency = "GBP"
                foaa.research_articles_published = randrange(500)
                foaa.acceptance_rate = float(randrange(1000, 10000) / 100)
                foaa.rejection_rate = float(randrange(1000, 10000) / 100)
                foaa.inhouse_or_outsourced_journal_operations = generate_operations()
                foaa.price_breakdown_journal_operations = price_breakdown[0]
                foaa.price_breakdown_publication = price_breakdown[1]
                foaa.price_breakdown_fees = price_breakdown[2]
                foaa.price_breakdown_communication = price_breakdown[3]
                foaa.price_breakdown_general = price_breakdown[4]
                foaa.price_breakdown_surplus_other_revenue = price_breakdown[5]
                foaa.price_breakdown_discounts_and_waivers = price_breakdown[6]
                foaa.save()
                foaas += 1

        if verbosity > 0:
            self.stdout.write(f'InformationPower journals added: {ips}')
            self.stdout.write(f'FairOpenAccessAlliance journals added: {foaas}')
            self.stdout.write(f'Total: {i + 1}')
