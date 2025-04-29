
class MultipleRecordsPerISSNException(Exception):
    def __init__(self, issn, year=None):
        self.issn = issn
        self.year = year
        super(MultipleRecordsPerISSNException, self).__init__()