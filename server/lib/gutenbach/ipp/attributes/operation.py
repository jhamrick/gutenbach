__all__ = [
    'PrinterUri',
    'RequestingUserName',
    'IppAttributeFidelity',
    'LastDocument'
]

from .. import Attribute
from .. import Value
from .. import errors
from .. import CharacterStringTags, IntegerTags

def PrinterUri(val):
    return Attribute(
        'printer-uri',
        [Value(CharacterStringTags.URI, val)])

def RequestingUserName(val):
    return Attribute(
        'requesting-user-name',
        [Value(CharacterStringTags.NAME_WITHOUT_LANGUAGE, val)])

def IppAttributeFidelity(val):
    raise errors.ClientErrorAttributes, 'ipp-attribute-fidelity'

def LastDocument(val):
    return Attribute(
        'last-document',
        [Value(IntegerTags.BOOLEAN, val)])
