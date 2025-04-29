from openpyxl.cell import Cell
from openpyxl.workbook import Workbook
from openpyxl.worksheet.worksheet import Worksheet

from upload.frameworks import url_field, FrameworkFieldError
from upload.test.test_utils import UploadValidatorTestCase


class TestURLFields(UploadValidatorTestCase):
    """
    Url fields in IP: J, O, P. All optional.
    Url fields in FOAA: J, O, R. All optional.
    """

    def test_urls(self):
        wb = Workbook()
        sheet = Worksheet(wb)

        # Valid url
        valid_url = 'https://www.bbc.co.uk/weather/2640526'
        self.assertEquals(url_field(Cell(sheet, value=valid_url)), valid_url)

        # Invalid scheme
        with self.assertRaises(FrameworkFieldError):
            url_field(Cell(sheet, value='htts://www.bbc.co.uk/weather/2640526'))

        # Invalid scheme
        with self.assertRaises(FrameworkFieldError):
            url_field(Cell(sheet, value='ftps://www.bbc.co.uk/weather/2640526'))

        # Too long string
        with self.assertRaises(FrameworkFieldError):
            url_field(Cell(sheet, value='https://www.bbc.co.uk/weather/2640526' + (80 * '2640526')))

        # Integer
        with self.assertRaises(FrameworkFieldError):
            self.assertFalse(url_field(Cell(sheet, value=1112)))

    def test_ip_passing(self):
        data = ["1749-4001", "Represent", "", "4.1 agriculture, forestry, and fisheries", "", "", 300, 4999.00, "GBP",
                "https://journalcomparisonservice.com/", 100.00, 10110.00, 30000.00, "USD",
                "https://journalcomparisonservice.com/", "https://journalcomparisonservice.com/", 1, 1.00, "90.22%",
                "Annual", 33, 5.00, 5.00, 4.00, None, 1, 90, 10, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, ""]

        vds = self.getValidator('ip', data)

        self.assertEquals({}, vds.errors)

    def test_ip_failing_col_o(self):
        malformed_url = "htt://journalcomparisonservice.com/"
        data = ["1749-4001", "Represent", "", "4.1 agriculture, forestry, and fisheries", "", "", 300, 4999.00, "GBP",
                malformed_url, 100.00, 10110.00, 30000.00, "USD",
                "https://journalcomparisonservice.com/", "https://journalcomparisonservice.com/", 1, 1.00, "90.22%",
                "Annual", 33, 5.00, 5.00, 4.00, None, 1, 90, 10, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, ""]

        vds = self.getValidator('ip', data)

        self.assertIn('J', vds.errors)
        self.assertEquals(len(vds.errors), 1)
        self.assertEquals(len(vds.errors['J']), 1)
        self.assertEquals(vds.errors['J'][0].value, malformed_url)

    def test_ip_failing_all(self):
        malformed_url = "htt://journalcomparisonservice.com/"
        data = ["1749-4001", "Represent", "", "4.1 agriculture, forestry, and fisheries", "", "", 300, 4999.00, "GBP",
                malformed_url, 100.00, 10110.00, 30000.00, "USD",
                malformed_url, malformed_url, 1, 1.00, "90.22%",
                "Annual", 33, 5.00, 5.00, 4.00, None, 1, 90, 10, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, ""]

        vds = self.getValidator('ip', data)

        self.assertIn('J', vds.errors)
        self.assertEquals(len(vds.errors), 3)

        for column_letter in vds.errors:
            self.assertEquals(len(vds.errors[column_letter]), 1)
            self.assertEquals(vds.errors[column_letter][0].value, malformed_url)

    def test_foaa_passing(self):
        data = ["1137-5019", "Some journal", None, "2.6 Medical engineering", None, None, 200, 300, "ISK",
                "https://journalcomparisonservice.com/", 4000, 15000, 1000, "GBP",
                "https://journalcomparisonservice.com/", "both", 30, "https://journalcomparisonservice.com/", 10, 10,
                10, 20, 10, 30, 10]

        vds = self.getValidator('foaa', data)

        self.assertEquals({}, vds.errors)

    def test_foaa_failing_col_r(self):
        malformed_url = "https:/journalcomparisonservice.com/"
        data = ["1137-5019", "Some journal", None, "2.6 Medical engineering", None, None, 200, 300, "ISK",
                "https://journalcomparisonservice.com/", 4000, 15000, 1000, "GBP",
                "https://journalcomparisonservice.com/", "both", 30, malformed_url, 10, 10,
                10, 20, 10, 30, 10]

        vds = self.getValidator('foaa', data)

        self.assertIn('R', vds.errors)
        self.assertEquals(len(vds.errors), 1)
        self.assertEquals(len(vds.errors['R']), 1)
        self.assertEquals(vds.errors['R'][0].value, malformed_url)

    def test_foaa_failing_all(self):
        malformed_url = "https:/journalcomparisonservice.com/"
        data = ["1137-5019", "Some journal", None, "2.6 Medical engineering", None, None, 200, 300, "ISK",
                malformed_url, 4000, 15000, 1000, "GBP",
                malformed_url, "both", 30, malformed_url, 10, 10,
                10, 20, 10, 30, 10]

        vds = self.getValidator('foaa', data)

        self.assertIn('R', vds.errors)
        self.assertEquals(len(vds.errors), 3)

        for column_letter in vds.errors:
            self.assertEquals(len(vds.errors[column_letter]), 1)
            self.assertEquals(vds.errors[column_letter][0].value, malformed_url)
