from upload.test.test_utils import UploadValidatorTestCase


class TestFrequency(UploadValidatorTestCase):
    """
    Publication frequency: T
    needs to be one of the values defined in pstf.contstants.py in frequencies
    """
    def test_wrong_frequency(self):
        frequency = 'monthl'
        data = ["1749-4001", "Represent", "", "all HSS disciplines", "", "", 300, 4999.00, "GBP",
                "", 11.00, 101, 30000.00, "USD", "", "", 1, 1.00, "90.22%", frequency, 33, 5.00, 5.00, 4.00, 15, 1,
                90, 10, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, ""]

        vds = self.getValidator('ip', data)

        # make sure there are no other errors
        self.assertEquals(len(vds.errors), 1)
        self.assertIn('T', vds.errors)
        self.assertEquals(len(vds.errors['T']), 1)
        self.assertEquals(vds.errors['T'][0].value, frequency)

    def test_right_frequencye(self):
        data = ["1749-4001", "Represent", "", "all HSS disciplines", "", "", 300, 4999.00, "GBP",
                "", 10.00, 101, 30000.00, "USD", "", "", 1, 1.00, "90.22%", "Annual", 33, 5.00, 5.00, 4.00, 15, 1,
                90, 10, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, ""]

        vds = self.getValidator('ip', data)

        self.assertEquals({}, vds.errors)
