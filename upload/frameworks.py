import logging
import re
from decimal import Decimal, InvalidOperation
from typing import List, Tuple, Callable, Union

import pycountry
from django.core.exceptions import ValidationError
from django.core.validators import URLValidator
from openpyxl.cell import Cell

from pstf import constants
from pstf.utils import validate_issn

logger = logging.getLogger(__name__)


class FrameworkValidation:
    """
    A framework validation object is a generic object to validate a FrameworkField.
    It consists of a:
        method: a validation method that return a boolean value
        msg: a tuple, to give a singular(0) and a plural(1) error message
        extra: optional parameter for additional information printed with the error message
    """

    def __init__(self, method: Callable, msg: Tuple[str, str] = None, extra: str = None):
        self.method = method
        self.msg = msg
        self.extra = extra

    def __str__(self):
        return self.method.__name__ if self.method else self.__name__


def str_field(cell: Cell) -> str:
    """
    Strips whitespace from a string field.
    Does not perform any validation.
    :param cell:
    :return:
    """
    return str(cell.value).strip()


StrValidation = FrameworkValidation(str_field, constants.SPREADSHEET_TITLE_MSG)


def issn_field(cell: Cell) -> str:
    """
    Validates the structure of an ISSN and its checksum.
    :param cell:
    :return:
    """

    value = str(cell.value).strip()

    if validate_issn(value):
        return value

    raise FrameworkFieldError( _type='issn_field', value=value)


ISSNValidation = FrameworkValidation(issn_field, constants.SPREADSHEET_ISSN_MSG)


def int_field(cell: Cell) -> int:
    """
    Value needs to be a positive integer.
    :param cell:
    :return:
    """
    integer = cell.value

    if isinstance(integer, int) and integer >= 0:
        return integer
    elif isinstance(integer, float) and int(integer) == integer and integer >= 0:
        return int(integer)
    elif isinstance(integer, str):
        try:
            if float(integer) == int(float(integer)) and int(float(integer)) >= 0:
                return int(float(integer))
        except ValueError:
            pass

    raise FrameworkFieldError(_type='int_field', value=integer)


IntValidation = FrameworkValidation(int_field, constants.SPREADSHEET_INT_MSG)


def currency_field(cell: Cell) -> str:
    """
    Value must be a valid 3 letter ISO-4217 currency code.
    :param cell:
    :return:
    """
    try:
        pycountry.currencies.get(alpha_3=cell.value)

        return cell.value
    except LookupError:
        raise FrameworkFieldError(_type='currency_field', value=cell.value)


CurrencyValidation = FrameworkValidation(currency_field, constants.SPREADSHEET_CURRENCY_MSG)


def discipline_field(cell: Cell) -> str:
    """
    Validates a discipline as defined by the Fields of Research and Development (FORD)
    classification.

    See:
    https://read.oecd-ilibrary.org/science-and-technology/frascati-manual-2015_9789264239012-en#page61
    :param cell:
    :return:
    """

    discipline = cell.value

    if isinstance(discipline, str):
        discipline = discipline.strip().lower()
        discipline_pattern = re.compile(r'^([1-6]\.\d{0,2})\.?\s?(.*)$')

        if discipline in [d.lower() for d in constants.all_disciplines]:
            return discipline
        elif discipline_pattern.match(discipline):
            m = discipline_pattern.match(discipline)
            discipline_number = m.group(1)
            discipline_name = m.group(2)

            for d in constants.disciplines:
                if discipline_pattern.match(d).group(1) == discipline_number and \
                        discipline_pattern.match(d).group(2) == discipline_name:
                    return discipline

    raise FrameworkFieldError(_type='discipline_field', value=discipline)


DisciplineValidation = FrameworkValidation(discipline_field, constants.SPREADSHEET_DISCIPLINE_MSG,
                                           constants.SPREADSHEET_DISCIPLINE_EXTRA)


def is_int_or_float(value) -> bool:
    return isinstance(value, float) or isinstance(value, int)


def percentage_field(cell: Cell) -> Decimal:
    """
    Validates and normalises a passed value as a decimal between 0 and 100.
    :param cell:
    :return:
    """
    percentage = cell.value

    # If a cell is formatted in a percentage format the number_format property will have
    # a value of "0.00%" or similar and the type will be a float.
    if re.match(r'0*?\.?0*?%$', cell.number_format) and is_int_or_float(percentage):
        percentage = 100 * percentage

    if isinstance(percentage, str):
        percentage = percentage.replace(',', '.').replace('%', '')

    try:
        if 0 <= Decimal(percentage) <= 100:
            return Decimal(percentage)
    except Exception:
        pass

    raise FrameworkFieldError(_type='percentage_field', value=percentage)


PercentageValidation = FrameworkValidation(percentage_field, constants.SPREADSHEET_PERCENTAGE_MSG)


def frequency_field(cell: Cell) -> str:
    """
    Validation that value is found in the list of frequencies.
    :param cell:
    :return:
    """
    frequency = cell.value

    if isinstance(frequency, str):
        frequency = frequency.strip().lower()

        if frequency in constants.frequencies:
            return frequency

    raise FrameworkFieldError(_type='frequency_field', value=frequency)


FrequencyValidation = FrameworkValidation(frequency_field, constants.SPREADSHEET_FREQUENCY_MSG,
                                          constants.SPREADSHEET_FREQUENCY_EXTRA)


def decimal_field(cell: Cell):
    """
    Validation that value is a positive float or int.
    :param cell:
    :return:
    """
    try:
        if Decimal(cell.value) >= 0:
            return Decimal(cell.value)
    except InvalidOperation:
        raise FrameworkFieldError(_type='decimal_field', value=cell.value)


DecimalValidation = FrameworkValidation(decimal_field, constants.SPREADSHEET_DECIMAL_MSG,
                                        constants.SPREADSHEET_DECIMAL_EXTRA)


def operations_field(cell: Cell) -> str:
    """
    Validation that value is in the operations list.
    :param cell:
    :return:
    """
    operation = cell.value

    if isinstance(operation, str):
        operation = cell.value.strip().lower()

        if operation in constants.operations:
            return operation

    raise FrameworkFieldError(_type='operations_field', value=operation)


OperationsValidation = FrameworkValidation(operations_field, constants.SPREADSHEET_OPERATIONS_MSG,
                                           constants.SPREADSHEET_OPERATIONS_EXTRA)


def url_field(cell: Cell) -> str:
    url = cell.value

    if not isinstance(url, str) or len(url) > 500:
        raise FrameworkFieldError()

    url_validator = URLValidator(schemes=['http', 'https'])

    try:
        url_validator(url)
        return url
    except ValidationError:
        pass

    raise FrameworkFieldError(_type='url_field', value=url)


URLValidation = FrameworkValidation(url_field, constants.SPREADSHEET_URL_MSG, constants.SPREADSHEET_URL_EXTRA)


class FrameworkFieldError(Exception):
    """
    A FrameworkFieldError is a standard object containing information about
    how a field has failed validation.
    It consists of a:
        type: for which the name of the validation method is taken,
        value: the value for that field
        row: the row number
        column_id: the id of the column
        integral_check: whether the validation performed is limited to this field or a comparison with
            another field is necessary
        comparative_column_id: the column id of the column the comparative check was done
    """

    def __init__(self, _type: str = None, value=None, row: int = None, column_id: str = None,
                 integral_check: bool = True, comparative_column_id: str = None):
        # Call the base class constructor with the parameters it needs
        super().__init__(None)
        self.type = _type
        self.value = value
        self.row = row
        self.column_id = column_id
        self.integral_check = integral_check
        self.comparative_column_id = comparative_column_id


class FrameworkField:
    """
    A FrameworkField is a single field in a spreadsheet as defined in a Framework object.
    It consists of:
        name: example 'Price Transparency Context'
        column_id: the spreadsheet id mapped to that name, e.g. F
        required: a boolean indicating whether the field needs to have a value or is optional,
            this is checked in ValidateSpreadsheet.process_journal()
        validation: the FrameworkValidation object describing how the field is to be validated
        value: the field's entered value. Not passed to __init__ but to validate()
        summed: boolean, whether this field is to be included in the sum calculation for
            current row/journal, calculated using Framework.get_sum()
        greater_than: the field name of a field whose value must be less than this fields,
            like required, this is checked in ValidateSpreadsheet.process_journal()
        acronym: the acronym of the framework this field is part of, either IP or FOAA

    """

    def __init__(self, name: str = None, required: bool = True, validation: FrameworkValidation = None,
                 summed: bool = False, greater_than: str = None, acronym: str = None):
        self.name = name
        self.column_id = constants.column_names_to_fields_mapping[acronym][name] if name else None
        self.required = required
        self.validation = validation
        self.cell: Union[Cell, None] = None
        self.summed = summed
        self.greater_than = greater_than

    def validate(self, cell: Cell = None) -> FrameworkFieldError:
        """
        Like is_missing() above, this method is called in ValidateSpreadsheet.process_journal() for each field
        in each row. It validates a FrameworkField using the validation method defined in it's
        FrameworkFieldValidation and if the validation is unsuccessful returns a FrameworkFieldError describing
        the error.
        :param cell:
        :return:
        """
        if cell.value is not None:
            self.cell = cell

        if self.required and self.cell.value is None:
            raise FrameworkFieldError(_type=str(self.validation), value=self.cell.value, column_id=self.column_id)

        if self.validation:
            return self.validation.method(self.cell)

        return self.cell.value

    def __str__(self):
        if self.name and self.validation:
            return self.name + " " + str(self.validation)
        else:
            return self.name if self.name else 'Unnamed'


class Framework:
    """
    Class for the two reporting frameworks, Information Power and Fair Open Access Alliance.
    For the purpose of validating data submitted in spreadsheets in those formats.

    See: https://github.com/antleaf/journal_comparison_service_data_collection

    Currently using the 2 frameworks both version 1:
    * https://github.com/antleaf/journal_comparison_service_data_collection/blob/main/Journal_Comparison_Service_Data_Collection_FOAA_v1.0.xlsx
    * https://github.com/antleaf/journal_comparison_service_data_collection/blob/main/Journal_Comparison_Service_Data_Collection_Information_Power_v1.0.xlsx

    name: the framework name
    fields: all the framework's Frameworkfields, exhaustive list
    optional: optional fields repeated
    required: required fields, the inverse of optional compared to fields
    sums: list of fields that are to be summed using the get_sum() method below
    greater_than: list of fields whose value is to be compared using > against another field
    """

    def __init__(self, name: str, fields: List[dict]):
        self.name = name
        self.acronym = ''.join([n[0] for n in name.split(' ')]).lower()
        self.fields: List[FrameworkField] = [FrameworkField(**k, acronym=self.acronym) for k in fields]
        self.required: List[FrameworkField] = [f for f in self.fields if f.required]
        self.sums: List[FrameworkField] = [f for f in self.fields if f.summed]
        self.greater_than: List[FrameworkField] = [f for f in self.fields if f.greater_than]

    def get_field_by_name(self, field_name: str) -> FrameworkField:
        """
        Looks up a Frameworkfield by its name
        :param field_name:
        :return:
        """
        return [f for f in self.fields if f.name == field_name][0]

    def get_field_by_id(self, column_id: str) -> FrameworkField:
        """
        Looks up a FrameworkField by its id
        :param column_id:
        :return:
        """
        try:
            return [f for f in self.fields if f.column_id == column_id][0]
        except IndexError:
            pass

    def get_sum(self, journal: dict):
        """
        Adds together all the numbers in the fields/columns designated in sums.

        The sum is limited to 2 significant numbers.
        :param journal:
        :return:
        """
        try:
            price_breakdown_sum = sum([Decimal(journal[s.name]) for s in self.sums if s.name in journal])
            return Decimal(price_breakdown_sum).quantize(Decimal('.01'))
        except TypeError:
            return "not a number"
        except KeyError:
            return "missing one or more valid inputs"
        except InvalidOperation:
            return "not a number"
