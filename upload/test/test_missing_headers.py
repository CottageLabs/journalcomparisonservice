from upload.constants import frameworks
from upload.models import UploadFile
from upload.spreadsheets import ValidateSpreadsheet

from openpyxl import Workbook

from upload.test.test_utils import UploadValidatorTestCase


class TestMissingHeaders(UploadValidatorTestCase):
    
    def test_only_first_six_headers(self):
        new_upload = UploadFile()
        new_upload.framework = 'ip'
        new_upload.publisher = self.pub1
        new_upload.save()

        wb = Workbook()
        ws = wb.active

        # header row
        ws.append([f.name for f in frameworks[new_upload.framework].fields][:6])

        # data values
        ws.append(
            ["1749-4001", "Represent", "", "4.1 agriculture, forestry, and fisheries", "", "", 300, 4999.00, "GBP", "",
             100.00, 10110.00, 30000.00, "USD", "", "", 1, 1.00, "90.22%", "Annual", 33, 5.00, 5.00, 4.00, 15, 1,
             90, 10, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, ""])

        # Save the file
        wb.save(self.filepath)

        with open(self.filepath, 'rb') as file:
            vds = ValidateSpreadsheet(new_upload, file)

        self.assertEquals({}, vds.errors)
        self.assertEquals(len(vds.missing_headers), len(frameworks[new_upload.framework].fields) - 6)
