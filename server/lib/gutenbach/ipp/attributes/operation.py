__all__ = [
    'PrinterUri',
    'RequestingUserName',
    'IppAttributeFidelity',
    'LastDocument',
    'Limit',
    'RequestedAttributes',
    'WhichJobs',
    'MyJobs',
    'DocumentName',
    'Compression',
    'DocumentFormat',
    'DocumentNaturalLanguage',
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

def Limit(val):
    return Attribute(
        'limit',
        [Value(IntegerTags.INTEGER, val)])

def RequestedAttributes(*vals):
    return Attribute(
        'requested-attributes',
        [Value(CharacterStringTags.KEYWORD, val) for val in vals])

def WhichJobs(val):
    return Attribute(
        'which-jobs',
        [Value(CharacterStringTags.KEYWORD, val)])

def MyJobs(val):
    return Attribute(
        'my-jobs',
        [Value(IntegerTags.BOOLEAN, val)])

def DocumentName(val):
    return Attribute(
        'document-name',
        [Value(CharacterStringTags.NAME_WITHOUT_LANGUAGE, val)])

def Compression(val):
    return Attribute(
        'compression',
        [Value(CharacterStringTags.KEYWORD, val)])

def DocumentFormat(val):
    return Attribute(
        'document-format',
        [Value(CharacterStringTags.MIME_MEDIA_TYPE, val)])

def DocumentNaturalLanguage(val):
    return Attribute(
        'document-natural-language',
        [Value(CharacterStringTags.NATURAL_LANGUAGE, val)])
