from upload.test.test_utils import UploadValidatorTestCase


class TestOptionalFields(UploadValidatorTestCase):

    def test_counter_5_unique_item_requests_included(self):
        data = ["1749-4001", "Represent", "", "4.1 agriculture, forestry, and fisheries", "", "", 300, 4999.00, "GBP",
                "", 100.00, 10110.00, 30000.00, "USD", "", "", 1, 1.00, "90.22%", "Annual", 33, 5.00, 5.00, 4.00, 15,
                1, 90, 10, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, ""]

        vds = self.getValidator('ip', data)

        self.assertEquals({}, vds.errors)
        # counter_5_unique_item_requests is an integer field but will return a string type
        # when accessed directly
        self.assertEquals(int(vds.objects[0].counter_5_unique_item_requests), 15)

    def test_counter_5_unique_item_requests_not_included(self):
        data = ["1749-4001", "Represent", "", "4.1 agriculture, forestry, and fisheries", "", "", 300, 4999.00, "GBP",
                "", 100.00, 10110.00, 30000.00, "USD", "", "", 1, 1.00, "90.22%", "Annual", 33, 5.00, 5.00, 4.00, "", 1,
                90, 10, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, ""]

        vds = self.getValidator('ip', data)

        self.assertEquals({}, vds.errors)
        self.assertEquals(vds.objects[0].counter_5_unique_item_requests, None)
