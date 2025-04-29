import traceback
from datetime import datetime
import logging

from django.core.management.base import BaseCommand
from elasticsearch import Elasticsearch

from apscheduler.schedulers.blocking import BlockingScheduler
from django_apscheduler.jobstores import DjangoJobStore

from django.conf import settings

from data.documents import InformationPowerDocument, FairOpenAccessAllianceDocument, JournalAutocompleteDocument, \
    PublisherAutocompleteDocument, DisciplineAutocompleteDocument
from data.models import InformationPower, FairOpenAccessAlliance
from data.utils import title_variants

from accounts.models import PublisherAccount

import re

from pstf.constants import ADMIN_EMAIL
from pstf.utils import send_email

logger = logging.getLogger(__name__)

DISCIPLINE_PREFIX_RX = "^(.+\. )"


def index_documents(**kwargs):
    ips = 0
    foaas = 0

    for ip in InformationPower.objects.all():
        ip_document = InformationPowerDocument(**{k: v for k, v in ip.__dict__.items() if not k.startswith('_')})

        publisher = ip.upload.publisher
        ip_document.framework = "ip"
        ip_document.publisher = publisher.publisher_name
        ip_document.publisher_id = publisher.id

        ip_document.save(**kwargs)
        ips += 1

    for foaa in FairOpenAccessAlliance.objects.all():
        foaa_document = FairOpenAccessAllianceDocument(
            **{k: v for k, v in foaa.__dict__.items() if not k.startswith('_')})

        publisher = foaa.upload.publisher
        foaa_document.framework = "foaa"
        foaa_document.publisher = publisher.publisher_name
        foaa_document.publisher_id = publisher.id

        foaa_document.save(**kwargs)
        foaas += 1


def journal_autocomplete(**kwargs):
    all_issns = []

    for ip in InformationPower.objects.values("issn", "journal_title").distinct():
        issn = ip.get("issn")
        if issn in all_issns:
            continue

        publishers = []
        for rec in InformationPower.objects.filter(issn=issn).all():
            pub = rec.upload.publisher
            publishers.append(pub.id)

        for rec in FairOpenAccessAlliance.objects.filter(issn=issn).all():
            pub = rec.upload.publisher
            publishers.append(pub.id)

        publishers = list(set(publishers))

        all_issns.append(issn)

        issns = [issn.lower(), issn.replace("-", "")]

        titles = title_variants(ip.get("journal_title"))

        acdoc = JournalAutocompleteDocument(issn=issn, title=ip.get("journal_title"), publisher_id=publishers,
                                            issn_ac=issns, title_ac=titles)
        acdoc.save(**kwargs)

    for foaa in FairOpenAccessAlliance.objects.values("issn", "journal_title").distinct():
        issn = foaa.get("issn")
        if issn in all_issns:
            continue

        publishers = []
        for rec in FairOpenAccessAlliance.objects.filter(issn=issn).all():
            pub = rec.upload.publisher
            publishers.append(pub.id)

        publishers = list(set(publishers))

        all_issns.append(issn)

        issns = [issn.lower(), issn.replace("-", "")]

        titles = title_variants(foaa.get("journal_title"))

        acdoc = JournalAutocompleteDocument(issn=issn, title=foaa.get("journal_title"), publisher_id=publishers,
                                            issn_ac=issns, title_ac=titles)
        acdoc.save(**kwargs)

    msg = f'Journal autocomplete records created: {len(all_issns)}'
    print(msg)
    logger.info(msg)


def publisher_autocomplete(**kwargs):
    idx = 0
    nidx = 0
    for p in PublisherAccount.objects.all():
        has_uploads = False
        for u in p.users.all():
            if u.uploadfile_set.count() > 0:
                has_uploads = True
                break
        if has_uploads:
            name_variants = title_variants(p.publisher_name)
            doc = PublisherAutocompleteDocument(name=p.publisher_name, publisher_id=p.id, country=p.country,
                                                name_ac=name_variants)
            doc.save(**kwargs)
            idx += 1
        else:
            nidx += 1

    msg = f'{idx} publishers indexed, {nidx} skipped with no journals'
    print(msg)
    logger.info(msg)


def discipline_autocomplete(**kwargs):
    all_discs = []

    for ip in InformationPower.objects.values("discipline").distinct():
        disc = ip.get("discipline")
        if disc in all_discs:
            continue

        all_discs.append(disc)
        variants = title_variants(disc)

        m = re.search(DISCIPLINE_PREFIX_RX, disc)
        if m:
            ex_number = disc[len(m.group(1)):]
            ex_number_variants = title_variants(ex_number)
            variants += ex_number_variants

        acdoc = DisciplineAutocompleteDocument(name=disc, name_ac=variants)
        acdoc.save(**kwargs)

    for foaa in FairOpenAccessAlliance.objects.values("discipline").distinct():
        disc = foaa.get("discipline")
        if disc in all_discs:
            continue

        all_discs.append(disc)
        variants = title_variants(disc)

        acdoc = DisciplineAutocompleteDocument(name=disc, name_ac=variants)
        acdoc.save(**kwargs)

    msg = f'Discipline autocomplete records created: {len(all_discs)}'
    print(msg)
    logger.info(msg)


def execute(**kwargs):
    try:
        BuildIndex().export(**kwargs)
    except KeyboardInterrupt as kbi:
        raise kbi
    except Exception as e:
        logger.exception(e)

        if settings.REPORT_SCHEDULED_JOB_FAILURES:
            send_email(None, 'PSTF PROD ES Indexing failed', ADMIN_EMAIL,
                       traceback.format_exc(), use_html=False)


class Command(BaseCommand):

    def add_arguments(self, parser):
        parser.add_argument(
            '-r', '--reset',
            action='store_true',
            help='Delete indices and create anew',
        )

    def handle(self, *args, **options):
        scheduler = BlockingScheduler(timezone=settings.TIME_ZONE)
        scheduler.add_jobstore(DjangoJobStore(), "default")

        scheduler.add_job(execute, trigger='cron', hour=23, minute=00,
                          next_run_time=datetime.now(),
                          id="build_index",
                          max_instances=1,
                          replace_existing=True,
                          kwargs=options)

        try:
            logger.info("Starting build_index scheduler...")
            scheduler.start()
        except KeyboardInterrupt:
            logger.info("Stopping build_index scheduler...")
            scheduler.shutdown()
            logger.info("Scheduler build_index shutdown successfully!")


class BuildIndex:

    def export(self, **options):
        """
        This command line command connects to an Elasticsearch server and indexes
        the contents of the database's two framework tables into an index.

        When using Elasticsearch, always use the alias endpoint ELASTICSEARCH_ALIAS
        defined in Django settings.

        When the command is run for the first time an index is created and the alias
        is linked to it. When the command is run consecutively, it creates a new index,
        the one not in use from ELASTICSEARCH_INDICES, points the alias to that index
        and deletes the old index.

        There is a reset option in the event something goes wrong that indiscriminately
        deletes all indices.
        :param options:
        :return:
        """
        es = Elasticsearch(settings.ELASTICSEARCH_DSL['default']['hosts'])

        if options['reset']:
            for prefix in settings.ES_RESET_PREFIXES:
                es.indices.delete(index=prefix)
                msg = f'{prefix} Indices deleted.'
                print(msg)
                logger.info(msg)

        self._index_objects(es,
                            settings.ELASTICSEARCH_ALIAS,
                            settings.ELASTICSEARCH_INDICES,
                            [InformationPowerDocument, FairOpenAccessAllianceDocument],
                            index_documents
                            )

        self._index_objects(es,
                            settings.ES_AUTOCOMPLETE_JOURNAL_ALIAS,
                            settings.ES_AUTOCOMPLETE_JOURNAL_INDICES,
                            JournalAutocompleteDocument,
                            journal_autocomplete
                            )

        self._index_objects(es,
                            settings.ES_AUTOCOMPLETE_PUBLISHER_ALIAS,
                            settings.ES_AUTOCOMPLETE_PUBLISHER_INDICES,
                            PublisherAutocompleteDocument,
                            publisher_autocomplete
                            )

        self._index_objects(es,
                            settings.ES_AUTOCOMPLETE_DISCIPLINE_ALIAS,
                            settings.ES_AUTOCOMPLETE_DISCIPLINE_INDICES,
                            DisciplineAutocompleteDocument,
                            discipline_autocomplete
                            )

    def _index_objects(self, es, alias_name, index_names, document_clazz, index_function):
        if not es.indices.exists_alias(name=alias_name):
            msg = f'Populating Elasticsearch index for alias {alias_name} for the first time'
            print(msg)
            logger.info(msg)

            # Create the mappings, using the first index
            if isinstance(document_clazz, list):
                for dc in document_clazz:
                    dc.init(using=es)
            else:
                document_clazz.init(using=es)

            # Index the documents
            index_function(using=es)

            # Associate alias with that index
            es.indices.update_aliases(
                body={
                    "actions": [
                        {"add": {"alias": alias_name,
                                 "index": index_names[0]}},
                    ]
                }
            )
        else:
            # Create new index and switch alias
            current_index = list(es.indices.get_alias(name=alias_name).keys())
            next_index = (set(index_names) - set(current_index)).pop()

            # Copy mappings from the aliased index
            mappings = es.indices.get_mapping(index=current_index[0])[current_index[0]]

            # Create the next of the two alternating indices
            es.indices.create(index=next_index, body={**mappings,
                                                      **{'settings': settings.ELASTICSEARCH_INDEX_SETTINGS}})
            msg = f'New index: {next_index} created'
            print(msg)
            logger.info(msg)

            # Index the documents
            index_function(using=es, index=next_index)

            # Repoint alias
            es.indices.update_aliases(
                body={
                    "actions": [
                        {"remove": {"alias": alias_name,
                                    "index": current_index[0]}},
                        {"add": {"alias": alias_name,
                                 "index": next_index}},
                    ]
                }
            )

            # Delete the old index
            es.indices.delete(index=current_index[0])
