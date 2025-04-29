from upload.test.test_utils import UploadValidatorTestCase


class TestDuplicateISSNS(UploadValidatorTestCase):
    """

    """
    def test_duplicate_issn(self):
        data = [["1749-4001", "Represent", "", "all HSS disciplines", "", "", 300, 1, "GBP", "", 1,
                101, 1, "USD", "", "", 1, 1, "90.22%", "Annual", 33, 5.00, 5.00, 4.00, 15, 1,
                90, 10, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, ""],
                ["1749-4001", "Represent", "", "all HSS disciplines", "", "", 300, 1, "GBP", "", 1,
                 101, 1, "USD", "", "", 1, 1, "90.22%", "Annual", 33, 5.00, 5.00, 4.00, 15, 1,
                 90, 10, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, ""]
                ]

        with self.assertRaises(ValueError):
            self.getValidator('ip', data)
