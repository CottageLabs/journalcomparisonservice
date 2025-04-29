import collections
import logging
import re
from _decimal import InvalidOperation
from decimal import Decimal
from itertools import groupby
from multiprocessing import Process
from typing import List, Dict, Union, Tuple

from django.conf import settings
from django.contrib import messages
from django.db.models import Q
from openpyxl.cell import Cell
from openpyxl.reader.excel import load_workbook
from openpyxl.workbook import Workbook
from openpyxl.worksheet.worksheet import Worksheet
from storages.backends.s3boto3 import S3Boto3StorageFile

from data.models import InformationPower, FairOpenAccessAlliance, FrameworkModelInterface
from pstf import constants, utils
from pstf.settings import SPREADSHEET
from pstf.utils import send_email

from upload.constants import frameworks
from upload.frameworks import FrameworkFieldError

from upload.models import UploadFile
from upload.utils import get_ranges

logger = logging.getLogger(__name__)


def normalize(cell: Cell):
    if isinstance(cell.value, str):
        return cell.value.strip()

    return cell.value


def is_empty_header_row(cell_values: List) -> bool:
    pre_header_text = r'The values in these [7,8] columns must add up to .*?100.00 or 0.00'
    return any([re.match(pre_header_text, cell_value) for cell_value in cell_values if isinstance(cell_value, str)])


class ValidateSpreadsheet:

    def __init__(self, upload: UploadFile, file: S3Boto3StorageFile, request=None):
        self.upload: UploadFile = upload
        self.framework: Dict = frameworks[upload.framework]
        self.request = request

        self.row: int = 0
        self.year = upload.data_year
        self.headers: List[str] = []
        self.journals: int = 0  # Count number of journals
        self.errors: Dict[str: List[FrameworkFieldError]] = {}
        self.issns: List[str] = []
        self.objects = []
        self.valid_object: Union[Dict, None] = None
        self.publisher = upload.publisher.publisher_name
        self.publisher_id = upload.publisher.id
        self.missing_headers = []
        self.framework = frameworks[upload.framework]

        # Data only flag ensures formulas are evaluated
        # see https://openpyxl.readthedocs.io/en/stable/tutorial.html?highlight=load_workbook#loading-from-a-file
        self.workbook: Workbook = load_workbook(filename=file, data_only=True)
        self.sheet: Worksheet = self.workbook.active
        self.max_rows = 10000

        for row in self.sheet.rows:
            self.row = self.row + 1

            if self.row >= self.max_rows:
                # OpenPyXL has difficulty in determining how much data is in a spreadsheet and
                # has reported over a million in a spreadsheet that actually contained only 6 rows of data
                # a manual cutoff at ten thousand should be safe
                msg = (f'Max rows exceeded for {self.upload.original_file_name}'
                       f' (max rows: {self.sheet.max_row}, dimensions: {self.sheet.calculate_dimension()})')
                logger.error(msg)
                break

            cell_values = [normalize(cell) for cell in row]

            # The row does not need to be processed if this is either a pre-header row
            # or, this is an empty row
            if (not self.headers and is_empty_header_row(cell_values)) or not any(cell_values):
                continue

            if not self.headers:
                # The first valid row has to contain all the headers
                self.headers = cell_values
                self.missing_headers = list(set([f.name for f in self.framework.fields]) - set(self.headers))
                missing_count = len(self.missing_headers)

                if missing_count and request is not None:
                    if missing_count > 1:
                        msg = (f'There are {missing_count} columns missing: "<i>' +
                               '", "'.join(self.missing_headers)) + '</i>".'

                        # Disable FOAA TODO: Remove all FOAA code. Issue#650
                        if not utils.disable_foaa_functionality():
                            msg += '<br/><br/>Perhaps you chose the wrong framework for this data?'

                        messages.add_message(request, SPREADSHEET, msg)
                    else:
                        msg = f'The column "<i>{self.missing_headers[0]}</i>" is missing.'
                        messages.add_message(request, SPREADSHEET, msg)
            else:
                # Headers have been processed, now processing data
                self.process_journal(row)

        duplicate_issns = [issn for issn, count in collections.Counter(self.issns).items() if count > 1]

        if not self.objects:
            raise ValueError(f'The file "{upload.original_file_name}" contains no data.')
        elif duplicate_issns:
            issns = ", ".join(duplicate_issns)
            raise ValueError(f'The file contains duplicate ISSNs: {issns}.')
        else:
            self.journals = len(self.objects)

    def add_error(self, error):
        if error.column_id not in self.errors:
            self.errors[error.column_id] = []

        self.errors[error.column_id].append(error)

    def report_errors(self, request):
        """
        Aggregates and creates errors as Django messages.
        Called in dashboard.views.process_upload()
        :param request:
        :return:
        """

        # Ensure we go through the fields in correct order
        fields = [e.column_id for e in self.framework.fields if e.column_id in self.errors]

        # Starting iterating through the columns
        for column_id in fields:
            # Only do integral checks at this stage
            errors = [e for e in self.errors[column_id] if e.integral_check]
            for validation_type, group in groupby(errors, lambda x: str(x.type)):
                column = self.framework.get_field_by_id(column_id)
                rows = get_ranges(group)
                count = 'Rows' if len(rows) > 1 or rows[0].find('-') > -1 else 'Row'

                if column.validation:
                    if len(rows) == 1 and rows[0].find('-') == -1:
                        msg = column.validation.msg[0]
                    else:
                        msg = column.validation.msg[1]
                else:
                    msg = 'This field is required'

                err = 'Column {column_id} ({column_name}), {count} {rows}: {msg}.{extra} {correct}'.format(
                    column_id=column.column_id,
                    column_name=column.name,
                    count=count,
                    rows=', '.join(rows),
                    msg=msg,
                    extra=column.validation.extra if column.validation and column.validation.extra else '',
                    correct=constants.SPREADSHEET_CORRECT)
                messages.add_message(request, SPREADSHEET, err)

        # Now do contextual checks, between fields
        for additional in [a for a in self.errors if len([cont for cont in self.errors[a] if not cont.integral_check])]:
            for validation_type, group in groupby(self.errors[additional], lambda x: str(x.type)):
                rows = get_ranges(group)

                if additional == 'sums':
                    fields = ', '.join([s.name for s in self.framework.sums])

                    if len(rows) > 1 or rows[0].find('-') > -1:
                        rows_msg = ', '.join(rows)
                        msg = f'Rows {rows_msg}: The total sum of the fields \'<i>{fields}</i>\' should' \
                              f' be either <i>0%</i> or <i>100%</i>.'
                    else:
                        row_msg = rows[0]
                        v = self.errors[additional][0].value
                        msg = f'Row {row_msg}: The total sum of the fields \'<i>{fields}</i> is \'<i>{v}</i>\'' \
                              f' but should be either <i>0%</i> or <i>100%</i>.'
                else:

                    if len(rows) > 1 or rows[0].find('-') > -1:
                        for column_duo, errors in groupby([e for e in self.errors[additional] if not e.integral_check],
                                                          lambda x: str(x.column_id) + '-' + str(
                                                              x.comparative_column_id)):
                            duo_rows = get_ranges(errors)
                            f1_id = str(column_duo).split('-')[0]
                            f2_id = str(column_duo).split('-')[1]
                            try:
                                f1 = self.framework.get_field_by_id(f1_id).name
                                f2 = self.framework.get_field_by_id(f2_id).name
                            except AttributeError:
                                return

                            rows_msg = ', '.join(duo_rows)
                            msg = f'Rows {rows_msg}: the column {f1_id} ({f1}) contains a lower value than' \
                                  f' the corresponding column {f2_id} ({f2}).'
                    else:
                        gt = [e for e in self.errors[additional] if not e.integral_check][0]
                        try:
                            f1 = self.framework.get_field_by_id(gt.column_id).name
                            f2 = self.framework.get_field_by_id(gt.comparative_column_id).name
                        except AttributeError:
                            return

                        msg = f'Row: {rows[0]}: the column {gt.column_id} ({f1}) contains a lower value than' \
                              f' the corresponding column {gt.comparative_column_id} ({f2}).'

                messages.add_message(request, SPREADSHEET, msg)

    def is_valid(self) -> bool:
        """
        Checks if there are any validation errors.
        :return:
        """
        return not bool(self.errors)

    def process_journal(self, row: Tuple[Cell, ...]):
        """
        Taking the row number as a parameter, this functions actually validates the data.
        Each row represents the full data for one journal.
        Error categories are defined in the init method for the class.
        Mapping between columns and error categories is done in constants.py.
        :param row:
        :return:
        """
        self.valid_object = {'publisher': self.publisher, 'publisher_id': self.publisher_id}
        journal = {k: v for k, v in zip(self.headers, row) if v.value is not None}

        # Iterating through each field in entered order
        for column in [f for f in self.framework.fields if f.name not in self.missing_headers]:
            try:
                self.valid_object[column.name] = column.validate(cell=journal[column.name])

                # Save validated ISSN value which will be cross-referenced just
                # before spreadsheet data is ingested
                if column.name.lower() == 'issn':
                    self.issns.append(self.valid_object[column.name])

            except KeyError as ke:
                # An exception will be raised here for any field with a None value
                # it is an issue if it is a required field
                if column.required:
                    value = column.cell.value if column.cell else None
                    self.add_error(FrameworkFieldError(_type=str(column.validation),
                                                       value=value,
                                                       row=self.row,
                                                       column_id=column.column_id))
            except FrameworkFieldError as ffe:
                ffe.row = self.row
                ffe.column_id = column.column_id
                self.add_error(ffe)

        internal_sum = self.framework.get_sum(self.valid_object)

        if not isinstance(internal_sum, Decimal) or (internal_sum != 0 and internal_sum != 100):
            self.add_error(FrameworkFieldError(_type='sums',
                                               value=internal_sum,
                                               row=self.row,
                                               column_id='sums',
                                               integral_check=False))

        for greater_than in [g for g in self.framework.greater_than if g.greater_than in journal]:
            try:
                less_than = self.framework.get_field_by_name(greater_than.greater_than)

                if less_than.cell.value > greater_than.cell.value:
                    self.add_error(FrameworkFieldError(_type='greater_than',
                                                       column_id=greater_than.column_id,
                                                       row=self.row,
                                                       integral_check=False,
                                                       comparative_column_id=less_than.column_id))
            except TypeError:
                pass
            except InvalidOperation:
                pass

        self.objects.append(self.get_db_object(journal=self.valid_object))

    @staticmethod
    def map_sheet_name_to_db_column(sheet_name: str) -> str:
        """
        Database field names in Django have a maximum limit of 63 bytes, or 63 ASCII chars
        see: https://www.postgresql.org/docs/current/sql-syntax-lexical.html#SQL-SYNTAX-IDENTIFIERS

        Bring the key to lower and replace spaces with underscores to eliminate any possible mismatch.

        Finally, there is a field called Desk rejection rate in IP equivalent to Rejection rate in FOAA.
        :param sheet_name:
        :return:
        """
        return sheet_name[:63] \
            .lower() \
            .replace(' / ', '_') \
            .replace(' ', '_') \
            .replace(':', '') \
            .replace('?', '') \
            .replace('-', '') \
            .replace('&', 'and') \
            .replace('desk_rejection_rate', 'rejection_rate')

    def get_db_object(self, journal: dict) -> FrameworkModelInterface:
        """
        Receives a sanitized dict representing the current journal being processed and creates a
        DAO.

        This DAO is stored in ValidateSpreadsheet.objects until bulk created
        in dashboard.views.process_upload()

        :param journal:
        :return:
        """
        obj = {self.map_sheet_name_to_db_column(k): v for k, v in journal.items()}
        obj['upload'] = self.upload
        obj["year"] = self.year

        if self.framework.acronym == 'ip':
            return InformationPower(**obj)
        elif self.framework.acronym == 'foaa':
            return FairOpenAccessAlliance(**obj)

    def check_for_issn_duplicates(self):
        """
        Iterates through ISSN values that have been put aside for each row and checks if there
        is an internal data clash. If so, sends an email notification.
        :return:
        """

        if self.upload.framework == 'ip':
            fw = InformationPower
        else:
            fw = FairOpenAccessAlliance

        duplicates = fw.objects. \
            filter(Q(issn__in=self.issns) & Q(year=self.year) & ~Q(publisher=self.upload.publisher))

        if duplicates:
            msg = constants.SPREADSHEET_ISSN_DUPLICATES.format(user=self.request.user,
                                                               publisher=self.upload.publisher,
                                                               issn=len(self.issns),
                                                               other_publisher=duplicates[0].publisher,
                                                               other_issn_year=duplicates[0].year,
                                                               issn_list=', '.join([issn.issn for issn in duplicates]))
            logger.info(msg)

            def _fn():
                try:
                    send_email(request=self.request,
                               subject='[JCS] Duplicate ISSN\\s uploaded',
                               message=msg,
                               _from=settings.SENDER_ADDRESS,
                               to=settings.FEEDBACK_EMAIL,
                               use_html=False)
                except Exception as e:
                    logger.error('Sending a duplicate ISSN alert email failed')
                    logger.exception(e)

            # send email in separate process
            Process(target=_fn).run()
