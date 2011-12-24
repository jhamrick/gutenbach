__all__ = [
    'PrinterUri',
    'RequestingUserName',
]

from .. import Attribute
from .. import Value
from .. import errors
from .. import CharacterStringTags

def PrinterUri(val):
    return Attribute(
        'printer-uri',
        [Value(CharacterStringTags.URI, val)])

def RequestingUserName(val):
    return Attribute(
        'requesting-user-name',
        [Value(CharacterStringTags.NAME_WITHOUT_LANGUAGE, val)])
