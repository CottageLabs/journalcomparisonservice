from decimal import Decimal

from openpyxl.workbook import Workbook
from openpyxl.worksheet.worksheet import Worksheet

from upload.constants import frameworks
from upload.frameworks import percentage_field, FrameworkFieldError
from upload.models import UploadFile
from upload.spreadsheets import ValidateSpreadsheet
from upload.test.test_utils import UploadValidatorTestCase, get_cell


class TestPercentages(UploadValidatorTestCase):
    """
    Solo percentage fields in IP: R and S. Both required
    """

    def test_percentage(self):

        self.assertEquals(percentage_field(get_cell(0)), Decimal(0))
        self.assertEquals(percentage_field(get_cell(10)), Decimal(10))

        cell = get_cell(.10)
        cell.number_format = '0.00%'
        self.assertEquals(percentage_field(cell), Decimal(10))

        with self.assertRaises(FrameworkFieldError):
            percentage_field(get_cell(101))

    def test_ip_passing(self):
        data = ["1749-4001", "Represent", "", "4.1 agriculture, forestry, and fisheries", "", "", 300, 4999.00, "GBP",
                "https://journalcomparisonservice.com/", 100.00, 10110.00, 30000.00, "USD",
                "https://journalcomparisonservice.com/", "https://journalcomparisonservice.com/", 1, 1.00, "90.22%",
                "Annual", 33, 5.00, 5.00, 4.00, None, 1, 90, 10, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, ""]

        vds = self.getValidator('ip', data)

        self.assertEquals({}, vds.errors)

    def test_ip_r_and_s(self):
        upload = UploadFile(framework='ip', publisher=self.pub1)
        upload.save()

        wb = Workbook()
        ws: Worksheet = wb.active

        # keep the first row empty
        ws['A1'] = ''

        # header row
        ws.append([f.name for f in frameworks[upload.framework].fields])

        r_value = 0.311053984575836
        s_value = "90.22%"

        data = ["1749-4001", "Represent", "", "4.1 agriculture, forestry, and fisheries", "", "", 300, 4999.00,
                "GBP", "https://journalcomparisonservice.com/", 100.00, 10110.00, 30000.00, "USD",
                "https://journalcomparisonservice.com/", "https://journalcomparisonservice.com/", 1, r_value,
                s_value,  "Annual", 33, 5.00, 5.00, 4.00, None, 1, 90, 10, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, ""]

        # data values
        ws.append(data)

        # get cell R
        r = list(ws.rows)[2][-18]
        r.number_format = "0.00%"

        # Save the file
        wb.save(self.filepath)

        with open(self.filepath, 'rb') as file:
            vds = ValidateSpreadsheet(upload, file)

        self.assertEquals({}, vds.errors)
        self.assertEquals(vds.journals, 1)
        self.assertEquals(vds.objects[0].acceptance_rate, r_value * 100)
        self.assertEquals(vds.objects[0].rejection_rate, Decimal(s_value.replace('%', '')))
