from django.test import TestCase

from data.management.commands.generate_db_data import generate_price_breakdown
from upload.constants import frameworks

ip_breakdown = ['Price Breakdown: Journal Community Development',
                'Price Breakdown: Journal Submission On First Decision',
                'Price Breakdown: Peer Review', 'Price Breakdown: Services Acceptance Publication',
                'Price Breakdown: Services Post Publication', 'Price Breakdown: Platform Development Support',
                'Price Breakdown: Sales Marketing', 'Price Breakdown: Author Customer Support']
foaa_breakdown = ['Price Breakdown: Journal Operations',
                  'Price Breakdown: Publication', 'Price Breakdown: Fees', 'Price Breakdown: Communication',
                  'Price Breakdown: General', 'Price Breakdown: Surplus / Other Revenue',
                  'Price Breakdown: Discounts & Waivers']


def get_breakdown(framework, values):
    return {k: v for k, v in zip(framework, values)}


def get_ip_breakdown(values):
    return get_breakdown(ip_breakdown, values)


def get_foaa_breakdown(values):
    return get_breakdown(foaa_breakdown, values)


class TestInternalSum(TestCase):
    """Standard unit tests to test that the internal sum to calculate that the 7 "Price breakdown" fields in
    the FOAA framework and the 8 compatible fields in the IP framework add up to 100."""

    def test_ip_floats(self):
        journal = get_ip_breakdown(
            [19.6402910817673, 13.6744069062107, 9.45354183947053, 13.4337013607526, 7.34780990697273, 8.53556981347867,
             22.2512866831391, 5.66339240820831])

        self.assertEqual(100.00, frameworks['ip'].get_sum(journal))

    def test_ip_floats_incorrect(self):
        # First number has been changed by +0.009
        journal = get_ip_breakdown(
            [19.6492910817673, 13.6744069062107, 9.45354183947053, 13.4337013607526, 7.34780990697273, 8.53556981347867,
             22.2512866831391, 5.66339240820831])

        self.assertNotEquals(100.00, frameworks['ip'].get_sum(journal))

    def test_ip_ints(self):
        journal = get_ip_breakdown([10, 15, 6, 20, 13, 11, 18, 7])

        self.assertEqual(100.00, frameworks['ip'].get_sum(journal))

    def test_ip_generated(self):
        journal = get_ip_breakdown(generate_price_breakdown(8, 100))

        self.assertEqual(100.00, frameworks['ip'].get_sum(journal))

    def test_foaa_generated(self):
        journal = get_foaa_breakdown(generate_price_breakdown(7, 100))

        self.assertEqual(100.00, frameworks['foaa'].get_sum(journal))

    def test_foaa_ints(self):
        journal = get_foaa_breakdown([10, 26, 18, 5, 18, 9, 14])

        self.assertEqual(100.00, frameworks['foaa'].get_sum(journal))

    def test_foaa_floats(self):
        journal = get_foaa_breakdown([1 / 7 * 100] * 7)

        self.assertEqual(100.00, frameworks['foaa'].get_sum(journal))
