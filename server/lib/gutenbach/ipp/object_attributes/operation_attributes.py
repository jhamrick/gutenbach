__all__ = [
    'PrinterUri',
    'RequestingUserName',
]

from ..attribute import Attribute
from ..value import Value
from ..exceptions import ClientErrorAttributes
from ..constants import *

def PrinterUri(val):
    return Attribute(
        'printer-uri',
        [Value(CharacterStringTags.URI, val)])

def RequestingUserName(val):
    return Attribute(
        'requesting-user-name',
        [Value(CharacterStringTags.NAME_WITHOUT_LANGUAGE, val)])
