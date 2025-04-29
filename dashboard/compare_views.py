import json
from django.shortcuts import render
from pstf.decorators import is_institutional_user

from data.utils import *
from pstf import utils
from data import audit_log


class DataKeys:
    def __init__(self):
        self.field_map = [
            {"key": "issn", "name": "ISSN", "selectable": False},
            {"key": "journal_title", "name": "Journal Title", "selectable": False},
            {"key": "cluster", "name": "Cluster"},
            {"key": "discipline", "name": "Discipline"},
            {"key": "owner_ror_id", "name": "Owner ROR ID"},
            {"key": "publisher_ror_id", "name": "Publisher ROR ID"},
            {"key": "apc_list_price_range_lower", "name": "APC List Price Range Lower"},
            {"key": "apc_list_price_range_higher", "name": "APC List Price Range Higher"},
            {"key": "apc_list_price_currency", "name": "APC List Price Currency"},
            {"key": "apc_waiver_discount_policy", "name": "APC Waiver Discount Policy"},
            {"key": "subscription_list_price_range_lower", "name": "Subscription List Price Range Lower"},
            {"key": "subscription_list_price_range_higher", "name": "Subscription List Price Range Higher"},
            {"key": "subscription_list_price_for_member_of_the_association_of_americ", "name": "Subscription List Price For Member of The Association of American Universities (in USD)"},
            {"key": "subscription_list_price_currency", "name": "Subscription List Price Currency"},
            {"key": "subscription_discount_policy", "name": "Subscription Discount Policy"},
            {"key": "rejection_rate", "name": "Rejection Rate"},
            {"key": "notes", "name": "Notes"},

            {"key": "price_transparency_context", "name": "Price Transparency Context", "framework" : "ip"},
            {"key": "research_articles_published", "name": "Research Articles Published", "framework" : "ip"},
            {"key": "acceptance_rate", "name": "Acceptance Rate", "framework" : "ip"},
            {"key": "issue_publication_frequency", "name": "Issue Publication Frequency", "framework" : "ip"},
            {"key": "median_number_reviews", "name": "Median Number Reviews", "framework" : "ip"},
            {"key": "median_time_submission_to_first_decision", "name": "Median Time Submission To First Decision", "framework" : "ip"},
            {"key": "median_time_peer_review", "name": "Median Time Peer Review", "framework" : "ip"},
            {"key": "median_time_acceptance_to_publication", "name": "Median Time Acceptance To Publication", "framework" : "ip"},
            {"key": "counter_5_unique_item_requests", "name": "Counter 5 Unique Item Requests", "framework" : "ip"},
            {"key": "counter_5_total_item_requests", "name": "Counter 5 Total Item Requests", "framework" : "ip"},
            {"key": "price_breakdown_journal_community_development", "name": "Price Breakdown: Journal Community Development", "framework" : "ip"},
            {"key": "price_breakdown_journal_submission_on_first_decision", "name": "Price Breakdown: Journal Submission On First Decision", "framework" : "ip"},
            {"key": "price_breakdown_peer_review", "name": "Price Breakdown: Peer Review", "framework" : "ip"},
            {"key": "price_breakdown_services_acceptance_publication", "name": "Price Breakdown: Services Acceptance Publication", "framework" : "ip"},
            {"key": "price_breakdown_services_post_publication", "name": "Price Breakdown: Services Post Publication", "framework" : "ip"},
            {"key": "price_breakdown_platform_development_support", "name": "Price Breakdown: Platform Development Support", "framework" : "ip"},
            {"key": "price_breakdown_sales_marketing", "name": "Price Breakdown: Sales Marketing", "framework" : "ip"},
            {"key": "price_breakdown_author_customer_support", "name": "Price Breakdown: Author Customer Support", "framework" : "ip"},

            {"key": "inhouse_or_outsourced_journal_operations", "name": "In-house or Outsourced Journal Operations?", "framework" : "foaa"},
            {"key": "discounts_and_waivers_policy", "name": "Discounts and Waivers Policy", "framework" : "foaa"},
            {"key": "price_breakdown_journal_operations", "name": "Price Breakdown: Journal Operations", "framework" : "foaa"},
            {"key": "price_breakdown_publication", "name": "Price Breakdown: Publication", "framework" : "foaa"},
            {"key": "price_breakdown_fees", "name": "Price Breakdown: Fees", "framework" : "foaa"},
            {"key": "price_breakdown_communication", "name": "Price Breakdown: Communication", "framework" : "foaa"},
            {"key": "price_breakdown_general", "name": "Price Breakdown: General", "framework" : "foaa"},
            {"key": "price_breakdown_surplus_other_revenue", "name": "Price Breakdown: Surplus / Other Revenue", "framework" : "foaa"},
            {"key": "price_breakdown_discounts_and_waivers", "name": "Price Breakdown: Discounts & Waivers", "framework" : "foaa"}
        ]

    @property
    def selectable_common_keys(self):
        return [obj for obj in self.field_map if "framework" not in obj and obj.get("selectable", True)]

    @property
    def selectable_ip_keys(self):
        return [obj for obj in self.field_map if obj.get("framework") == "ip" and obj.get("selectable", True)]

    @property
    def selectable_foaa_keys(self):
        return [obj for obj in self.field_map if obj.get("framework") == "foaa" and obj.get("selectable", True)]

    @property
    def present_common_keys(self):
        return [obj for obj in self.field_map if "framework" not in obj and obj.get("present", False)]

    @property
    def present_ip_keys(self):
        return [obj for obj in self.field_map if obj.get("framework") == "ip" and obj.get("present", False)]

    @property
    def present_foaa_keys(self):
        return [obj for obj in self.field_map if obj.get("framework") == "foaa" and obj.get("present", False)]

    @property
    def has_ip_keys(self):
        return len(self.present_ip_keys) > 0

    @property
    def has_foaa_keys(self):
        return len(self.present_foaa_keys) > 0

    @property
    def key_list_encoded(self):
        return ",".join([obj["key"] for obj in self.field_map])

    def add_ip_keys(self, keys_set):
        for key in keys_set:
            for obj in self.field_map:
                if key == obj["key"]:
                    obj["present"] = True

    def add_foaa_keys(self, keys_set):
        for key in keys_set:
            for obj in self.field_map:
                if key == obj["key"]:
                    obj["present"] = True


@is_institutional_user
def compare_data(request, issns):
    audit_log.log_compare(request, issns)
    template = "ins_user/compare_journals.html"
    context = {'role': utils.get_user_group(request.user)}
    data_keys = DataKeys()

    issn_list = json.loads(issns)
    context['issns'] = str(issn_list)

    ip_data: list = list(get_ip_data_for_issn_dict(issn_list))
    if len(ip_data) > 0:
        data_keys.add_ip_keys(ip_data[0].keys())

    foaa_data: list = list(get_foaa_data_for_issn_dict(issn_list))
    if len(foaa_data) > 0:
        data_keys.add_foaa_keys(foaa_data[0].keys())

    ip_data.extend(foaa_data)

    context['data'] = ip_data
    context['keys'] = data_keys

    return render(request, template, context)
