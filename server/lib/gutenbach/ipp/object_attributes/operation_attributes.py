__all__ = [
    'PrinterUri',
    'RequestingUserName',
]

from ..attribute import Attribute
from ..value import Value
from ..exceptions import ClientErrorAttributes
from ..constants import *

class PrinterUri(Attribute):
    def __init__(self, val):
        super(type(self), self).__init__(
            'printer-uri',
            [Value(CharacterStringTags.URI, val)])

class RequestingUserName(Attribute):
    def __init__(self, val):
        super(type(self), self).__init__(
            'requesting-user-name',
            [Value(CharacterStringTags.NAME_WITHOUT_LANGUAGE, val)])
