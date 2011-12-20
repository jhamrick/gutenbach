from . import verify_operations
from . import make_empty_response

import logging
logger = logging.getLogger(__name__)

def verify_cups_get_classes_request(request):
    """CUPS-Get-Classes Request

    The following groups of attributes are supplied as part of the
    CUPS-Get-Classes request:

    Group 1: Operation Attributes
        Natural Language and Character Set:
            The 'attributes-charset' and
            'attributes-natural-language' attributes as described
            in section 3.1.4.1 of the IPP Model and Semantics
            document.
        'first-printer-name' (name(127)):CUPS 1.2/Mac OS X 10.5
            The client OPTIONALLY supplies this attribute to
            select the first printer that is returned.
        'limit' (integer (1:MAX)):
            The client OPTIONALLY supplies this attribute limiting
            the number of printer classes that are returned.
        'printer-location' (text(127)): CUPS 1.1.7
            The client OPTIONALLY supplies this attribute to
            select which printer classes are returned.
        'printer-type' (type2 enum): CUPS 1.1.7
            The client OPTIONALLY supplies a printer type
            enumeration to select which printer classes are
            returned.
        'printer-type-mask' (type2 enum): CUPS 1.1.7
            The client OPTIONALLY supplies a printer type mask
            enumeration to select which bits are used in the
            'printer-type' attribute.
        'requested-attributes' (1setOf keyword) :
            The client OPTIONALLY supplies a set of attribute
            names and/or attribute group names in whose values the
            requester is interested. If the client omits this
            attribute, the server responds as if this attribute
            had been supplied with a value of 'all'.
        'requested-user-name' (name(127)) : CUPS 1.2/Mac OS X 10.5
            The client OPTIONALLY supplies a user name that is
            used to filter the returned printers.

    (Source: http://www.cups.org/documentation.php/spec-ipp.html#CUPS_GET_CLASSES )

    """

    # XXX: actually do something here
    return {}

def make_cups_get_classes_response(request):
    """CUPS-Get-Classes Response

    The following groups of attributes are send as part of the
    CUPS-Get-Classes Response:

    Group 1: Operation Attributes
        Status Message:
            The standard response status message.
        Natural Language and Character Set:
            The 'attributes-charset' and
            'attributes-natural-language' attributes as described
            in section 3.1.4.2 of the IPP Model and Semantics
            document.

    Group 2: Printer Class Object Attributes
        The set of requested attributes and their current values
        for each printer class.

    (Source: http://www.cups.org/documentation.php/spec-ipp.html#CUPS_GET_CLASSES )

    """

    response = make_empty_response(request)
    return response
