from upload.test.test_utils import UploadValidatorTestCase


class TestDecimal(UploadValidatorTestCase):
    """
    G, H, K, L, M, R, V, W, X
    """
    def test_non_decimal(self):
        non_decimal = 'l'
        data = ["1749-4001", "Represent", "", "all HSS disciplines", "", "", 300, non_decimal, "GBP", "", non_decimal,
                101, non_decimal, "USD", "", "", 1, non_decimal, "90.22%", "Annual", 33, 5.00, 5.00, 4.00, 15, 1,
                90, 10, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, ""]

        vds = self.getValidator('ip', data)

        # make sure there are no other errors
        self.assertEquals(len(vds.errors), 4)

        for letter in ['H', 'K', 'M', 'R']:
            self.assertIn(letter, vds.errors)
