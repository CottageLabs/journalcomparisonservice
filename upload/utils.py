from itertools import groupby
from operator import itemgetter
from typing import List

from upload.frameworks import FrameworkFieldError


def get_ranges(rows: List[FrameworkFieldError]) -> List[str]:
    """
    Borrowed function that detects continuous numeric patterns and returns a list
    of strings indicating sequences.
    :param rows:
    :return:
    """
    ranges = []
    for key, group in groupby(enumerate(rows), lambda index_item: index_item[0] - int(index_item[1].row)):
        group = list(map(itemgetter(1), group))

        if len(group) > 1:
            ranges.append('{}-{}'.format(group[0].row, group[-1].row))
        else:
            ranges.append(str(group[0].row))

    return ranges
