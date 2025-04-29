from elasticsearch_dsl import Document, Integer, Keyword, Text, Double

from django.conf import settings


class FrameworkDocument(Document):
    journal_title = Text(fields={'raw': Keyword()})
    publisher = Text(fields={'raw': Keyword()})
    publisher_id = Integer()
    issn = Text(fields={'raw': Keyword()})
    discipline = Text(fields={'raw': Keyword()})
    framework = Text(fields={'raw': Keyword()})
    year = Integer()
    owner_ror_id = Text(fields={'raw': Keyword()})
    publisher_ror_id = Text(fields={'raw': Keyword()})
    apc_list_price_range_lower = Double()
    apc_list_price_range_higher = Double()
    apc_list_price_currency = Text(fields={'raw': Keyword()})
    apc_waiver_discount_policy = Text(fields={'raw': Keyword()})
    subscription_list_price_range_lower = Double()
    subscription_list_price_range_higher = Double()
    subscription_list_price_for_member_of_the_association_of_americ = Double()
    subscription_list_price_currency = Text(fields={'raw': Keyword()})
    rejection_rate = Double()
    notes = Text(fields={'raw': Keyword()})

    class Index:
        name = settings.ELASTICSEARCH_INDICES[0]
        settings = settings.ELASTICSEARCH_INDEX_SETTINGS


class InformationPowerDocument(FrameworkDocument):
    research_articles_published = Integer()
    acceptance_rate = Double()
    issue_publication_frequency = Text(fields={'raw': Keyword()})
    median_number_reviews = Double()
    median_time_submission_to_first_decision = Double()
    median_time_peer_review = Double()
    median_time_acceptance_to_publication = Double()
    counter_5_unique_item_requests = Integer()
    counter_5_total_item_requests = Integer()
    price_breakdown_journal_community_development = Double()
    price_breakdown_journal_submission_on_first_decision = Double()
    price_breakdown_peer_review = Double()
    price_breakdown_services_acceptance_publication = Double()
    price_breakdown_services_post_publication = Double()
    price_breakdown_platform_development_support = Double()
    price_breakdown_sales_marketing = Double()
    price_breakdown_author_customer_support = Double()


class FairOpenAccessAllianceDocument(FrameworkDocument):
    inhouse_or_outsourced_journal_operations = Text(fields={'raw': Keyword()})
    price_breakdown_journal_operations = Double()
    price_breakdown_publication = Double()
    price_breakdown_fees = Double()
    price_breakdown_communication = Double()
    price_breakdown_general = Double()
    price_breakdown_surplus_other_revenue = Double()
    price_breakdown_discounts_and_waivers = Double()


class JournalAutocompleteDocument(Document):
    title = Text(fields={"raw": Keyword()})
    issn = Text(fields={"raw": Keyword()})
    title_ac = Text(fields={"raw": Keyword()})
    issn_ac = Text(fields={"raw": Keyword()})
    publisher_id = Integer()

    class Index:
        name = settings.ES_AUTOCOMPLETE_JOURNAL_INDICES[0]
        settings = settings.ELASTICSEARCH_INDEX_SETTINGS


class PublisherAutocompleteDocument(Document):
    name = Text(fields={"raw": Keyword()})
    publisher_id = Integer()
    country = Text(fields={"raw": Keyword()})
    name_ac = Text(fields={"raw": Keyword()})

    class Index:
        name = settings.ES_AUTOCOMPLETE_PUBLISHER_INDICES[0]
        settings = settings.ELASTICSEARCH_INDEX_SETTINGS


class DisciplineAutocompleteDocument(Document):
    name = Text(fields={"raw": Keyword()})
    name_ac = Text(fields={"raw": Keyword()})

    class Index:
        name = settings.ES_AUTOCOMPLETE_DISCIPLINE_INDICES[0]
        settings = settings.ELASTICSEARCH_INDEX_SETTINGS