import six
import re
from django.utils.encoding import force_text
from unidecode import unidecode

ALPHA_REGEXP = re.compile('[\W_]+', re.UNICODE)


def to_ascii(value):
    if not six.PY3 and isinstance(value, str):
        value = force_text(value)

    return unidecode(value)


def to_search(value):
    """
    Convert a string value into a string that is usable against
    City.search_names.

    For example, 'Paris Texas' would become 'paristexas'.
    """

    return ALPHA_REGEXP.sub('', to_ascii(value)).lower()


# http://snipperize.todayclose.com/snippet/py/Converting-Bytes-to-Tb/Gb/Mb/Kb--14257/
def convert_bytes(bytes):
    bytes = float(bytes)
    if bytes >= 1099511627776:
        terabytes = bytes / 1099511627776
        size = '%.2fTb' % terabytes
    elif bytes >= 1073741824:
        gigabytes = bytes / 1073741824
        size = '%.2fGb' % gigabytes
    elif bytes >= 1048576:
        megabytes = bytes / 1048576
        size = '%.2fMb' % megabytes
    elif bytes >= 1024:
        kilobytes = bytes / 1024
        size = '%.2fKb' % kilobytes
    else:
        size = '%.2fb' % bytes
    return size
