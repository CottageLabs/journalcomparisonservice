from upload.test.test_utils import UploadValidatorTestCase


class TestWhitespace(UploadValidatorTestCase):
    """
    IP: B, C, E, F, AI
    """
    def test_whitespace(self):
        title = " Represent"
        data = ["1749-4001", title, None, "all HSS disciplines", None, None, 300, 400, "GBP", "", 2,
                101, 1, "USD", "", "", 1, 1, "90.22%", "Annual", 33, 5.00, 5.00, 4.00, 15, 1,
                90, 10, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, ""]

        vds = self.getValidator('ip', data)

        # make sure there are no errors
        self.assertEquals({}, vds.errors)

        self.assertEquals(vds.objects[0].journal_title, title.strip())
