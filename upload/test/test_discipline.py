from upload.test.test_utils import UploadValidatorTestCase


class TestDiscipline(UploadValidatorTestCase):
    """
    Discipline: D
    needs to be one of the values defined in pstf.contstants.py in either all_disciplines or disciplines
    """
    def test_wrong_discipline(self):
        discipline = "4.1 agriculture forestry, and fisheries"
        data = ["1749-4001", "Represent", "", discipline, "", "", 300, 4999.00, "GBP",
                "", 11.00, 101, 30000.00, "USD", "", "", 1, 1.00, "90.22%", "Annual", 33, 5.00, 5.00, 4.00, 15, 1,
                90, 10, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, ""]

        vds = self.getValidator('ip', data)

        # make sure there are no other errors
        self.assertEquals(len(vds.errors), 1)
        self.assertIn('D', vds.errors)
        self.assertEquals(len(vds.errors['D']), 1)
        self.assertEquals(vds.errors['D'][0].value, discipline)

    def test_all_discipline(self):
        discipline = "all HSS disciplines"
        data = ["1749-4001", "Represent", "", discipline, "", "", 300, 4999.00, "GBP",
                "", 10.00, 101, 30000.00, "USD", "", "", 1, 1.00, "90.22%", "Annual", 33, 5.00, 5.00, 4.00, 15, 1,
                90, 10, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, ""]

        vds = self.getValidator('ip', data)

        self.assertEquals({}, vds.errors)
