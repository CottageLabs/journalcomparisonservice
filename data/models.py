from django.db import models

# Create your models here.
from upload.models import UploadFile


class Discipline(models.TextChoices):
    NATSCI = '1. natural sciences'
    MATH = '1.1. mathematics'
    IT = '1.2. computer and information sciences'
    PE = '1.3. physical sciences'
    CHEM = '1.4. chemical sciences'
    EARTH = '1.5. earth and related environmental sciences'
    BIO = '1.6. biological sciences'
    OTHERNAT = '1.7. other natural sciences'
    ENGTECH = '2. engineering and technology'
    CIVENG = '2.1. civil engineering'
    ELECENG = '2.2. electrical engineering, electronic engineering, information engineering'
    MECHENG = '2.3. mechanical engineering'
    CHEMENG = '2.4. chemical engineering'
    MATENG = '2.5. materials engineering'
    MEDENG = '2.6. medical engineering'
    ENVENG = '2.7. environmental engineering'
    ENVBIO = '2.8. environmental biotechnology'
    INDENG = '2.9. industrial biotechnology'
    NANOTECH = '2.10. nano-technology'
    OTHERENG = '2.11. other engineering and technologies'
    MEDHEALTH = '3. medical and health sciences'
    BASICMED = '3.1. basic medicine'
    CLINICMED = '3.2. clinical medicine'
    HEALTHSCI = '3.3. health sciences'
    MEDIBIO = '3.4. medical biotechnology'
    OTHERMED = '3.5. other medical sciences'
    AGRIVET = '4. agricultural and veterinary sciences'
    AGRIFOREST = '4.1. agriculture, forestry, and fisheries'
    ANIMALDAIRY = '4.2. animal and dairy science'
    VETSCI = '4.3. veterinary science'
    AGRIBIO = '4.4. agricultural biotechnology',
    OTHERAGRI = '4.5. other agricultural sciences'
    SOCIALSCI = '5. social sciences'
    PSYCHO = '5.1. psychology and cognitive sciences'
    ECONOMICS = '5.2. economics and business'
    EDU = '5.3. educational sciences'
    SOCIOLOGY = '5.4. sociology'
    LAW = '5.5. law'
    POLSCI = '5.6. political science'
    SOCGEO = '5.7. social and economic geography'
    MEDCOM = '5.8. media and communications'
    OTHERSOC = '5.9. other social sciences'
    HUMAN = '6. humanities'
    HIST = '6.1. history and archaeology'
    LANG = '6.2. languages and literature'
    PHIL = '6.3. philosophy, ethics and religion'
    ARTS = '6.4. arts (arts, history of arts, performing arts, music)'
    OTHERHUM = '6.5. other humanities'
    ALL = 'all disciplines'
    ALLSTEM = 'all stem disciplines'
    ALLHSS = 'all hss disciplines'


class Operations(models.TextChoices):
    INHOUSE = 'in-house'
    OUTSOURCED = 'out-sourced'
    BOTH = 'both'


class PublicationFrequency(models.TextChoices):
    ANNUAL = 'annual'
    BIMONTHLY = 'bimonthly'
    SEMIWEEKLY = 'semiweekly'
    DAILY = 'daily'
    BIWEEKLY = 'biweekly'
    SEMIANNUAL = 'semiannual'
    BIENNIAL = 'biennial'
    TRIENNIAL = 'triennial'
    THREE_A_WEEK = 'three times a week'
    THREE_A_MONTH = 'three times a month'
    MONTHLY = 'monthly'
    QUARTERLY = 'quarterly'
    SEMIMONTHLY = 'semimonthly',
    THREE_A_YEAR = 'three times a year'
    WEEKLY = 'weekly'
    CONT = 'continuously updated'
    OTHER = 'other'


class FrameworkModelInterface(models.Model):
    # created = models.DateTimeField(auto_now_add=True)
    publisher = models.TextField(null=True)
    publisher_id = models.IntegerField(default=0)
    upload = models.ForeignKey(UploadFile, on_delete=models.CASCADE)
    year = models.IntegerField()
    issn = models.CharField(max_length=9)
    journal_title = models.TextField()
    cluster = models.TextField(null=True)
    discipline = models.CharField(max_length=80, choices=Discipline.choices)
    owner_ror_id = models.TextField(null=True)
    publisher_ror_id = models.TextField(null=True)
    apc_list_price_range_lower = models.DecimalField(max_digits=10, decimal_places=2)
    apc_list_price_range_higher = models.DecimalField(max_digits=10, decimal_places=2)
    apc_list_price_currency = models.CharField(max_length=3)
    apc_waiver_discount_policy = models.URLField(null=True, max_length=500)
    subscription_list_price_range_lower = models.DecimalField(max_digits=10, decimal_places=2)
    subscription_list_price_range_higher = models.DecimalField(max_digits=10, decimal_places=2)
    subscription_list_price_for_member_of_the_association_of_americ =\
        models.DecimalField(max_digits=10, decimal_places=2, null=True)
    subscription_list_price_currency = models.CharField(max_length=3)
    subscription_discount_policy = models.URLField(null=True, max_length=500)
    # Note: "desk rejection rate" in IP but same metric
    rejection_rate = models.DecimalField(max_digits=5, decimal_places=2)
    notes = models.TextField(null=True)

    class Meta:
        abstract = True


class InformationPower(FrameworkModelInterface):
    """
    Model to store Information Power data as per version 1.0
    https://github.com/antleaf/journal_comparison_service_data_collection/blob/main/Information_Power_Framework.md

    Example:
        {
        'ISSN': '1996-9732',
        'Journal Title': 'Water Science and Technology',
        'Discipline': 'all STEM disciplines',
        'Publisher ROR ID': 'Requested',
        'APC List Price Range Lower': 0,
        'APC List Price Range Higher': 0,
        'APC List Price Currency': 'USD',
        'APC Waiver Discount Policy': 'all articles are open access without APCs because of S2O https://iwaponline.com/s2o',
        'Subscription List Price Range Lower': 6227,
        'Subscription List Price Range Higher': 6227,
        'Subscription List Price For Member of The Association of American Universities': 6227,
        'Subscription List Price Currency': 'GBP',
        'Subscription Discount Policy': 'Multiple journals discount: https://iwaponline.com/pages/Institutional_Subscription_Rates',
        'Price Transparency Context': 'Not yet completed',
        'Research Articles Published': 529,
        'Acceptance Rate': 19.22,
        'Desk Rejection Rate': 56.45,
        'Issue Publication Frequency': 'Biweekly',
        'Median Number Reviews': 3,
        'Median Time Submission To First Decision': 13.0,
        'Median Time Peer Review': 13.0,
        'Median Time Acceptance To Publication': 46.0,
        'Counter 5 Total Item Requests': 1439880}
    """

    price_transparency_context = models.URLField(null=True, max_length=500)
    research_articles_published = models.IntegerField()
    acceptance_rate = models.DecimalField(max_digits=5, decimal_places=2)
    issue_publication_frequency = models.CharField(max_length=20, choices=PublicationFrequency.choices)
    median_number_reviews = models.DecimalField(max_digits=10, decimal_places=2)
    median_time_submission_to_first_decision = models.DecimalField(max_digits=10, decimal_places=2)
    median_time_peer_review = models.DecimalField(max_digits=10, decimal_places=2)
    median_time_acceptance_to_publication = models.DecimalField(max_digits=10, decimal_places=2)
    counter_5_unique_item_requests = models.IntegerField(null=True)
    counter_5_total_item_requests = models.IntegerField()
    price_breakdown_journal_community_development = models.DecimalField(max_digits=5, decimal_places=2)
    price_breakdown_journal_submission_on_first_decision = models.DecimalField(max_digits=5, decimal_places=2)
    price_breakdown_peer_review = models.DecimalField(max_digits=5, decimal_places=2)
    price_breakdown_services_acceptance_publication = models.DecimalField(max_digits=5, decimal_places=2)
    price_breakdown_services_post_publication = models.DecimalField(max_digits=5, decimal_places=2)
    price_breakdown_platform_development_support = models.DecimalField(max_digits=5, decimal_places=2)
    price_breakdown_sales_marketing = models.DecimalField(max_digits=5, decimal_places=2)
    price_breakdown_author_customer_support = models.DecimalField(max_digits=5, decimal_places=2)


class FairOpenAccessAlliance(FrameworkModelInterface):
    """
    Model to store Fair Open Access Alliance data as per version 1.0
    https://github.com/antleaf/journal_comparison_service_data_collection/blob/main/FOAA_Framework.md
    """

    inhouse_or_outsourced_journal_operations = models.CharField(max_length=11, choices=Operations.choices)
    price_breakdown_journal_operations = models.DecimalField(max_digits=5, decimal_places=2)
    price_breakdown_publication = models.DecimalField(max_digits=5, decimal_places=2)
    price_breakdown_fees = models.DecimalField(max_digits=5, decimal_places=2)
    price_breakdown_communication = models.DecimalField(max_digits=5, decimal_places=2)
    price_breakdown_general = models.DecimalField(max_digits=5, decimal_places=2)
    price_breakdown_surplus_other_revenue = models.DecimalField(max_digits=5, decimal_places=2)
    price_breakdown_discounts_and_waivers = models.DecimalField(max_digits=5, decimal_places=2)
    discounts_and_waivers_policy = models.URLField(null=True, max_length=500)
