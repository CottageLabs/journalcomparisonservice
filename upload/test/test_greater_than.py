from upload.test.test_utils import UploadValidatorTestCase


class TestGreaterThan(UploadValidatorTestCase):
    """
    Subscription List Price Range Lower: K
    needs to be lower or equal to
    Subscription List Price Range Higher: L
    """

    def test_subscription_price_greater(self):
        data = ["1749-4001", "Represent", "", "4.1 agriculture, forestry, and fisheries", "", "", 300, 4999.00, "GBP",
                "", 110.00, 101, 30000.00, "USD", "", "", 1, 1.00, "90.22%", "Annual", 33, 5.00, 5.00, 4.00, 15, 1,
                90, 10, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, ""]

        vds = self.getValidator('ip', data)

        # make sure there are no other errors
        self.assertEquals(len(vds.errors), 1)
        self.assertIn('L', vds.errors)
        self.assertEquals(len(vds.errors['L']), 1)
        self.assertEquals(vds.errors['L'][0].comparative_column_id, 'K')

    def test_subscription_price_equal(self):
        data = ["1749-4001", "Represent", "", "4.1 agriculture, forestry, and fisheries", "", "", 300, 4999.00, "GBP",
                "", 110.00, 110, 30000.00, "USD", "", "", 1, 1.00, "90.22%", "Annual", 33, 5.00, 5.00, 4.00, 15, 1,
                90, 10, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, ""]

        vds = self.getValidator('ip', data)

        self.assertEquals({}, vds.errors)
