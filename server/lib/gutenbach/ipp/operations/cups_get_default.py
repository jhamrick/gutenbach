from . import verify_operations
from . import make_empty_response
from . import make_printer_attributes

import logging
logger = logging.getLogger(__name__)

def verify_cups_get_default_request(request):
    """CUPS-Get-Default Request
    
    The following groups of attributes are supplied as part of the
    CUPS-Get-Default request:

    Group 1: Operation Attributes
        Natural Language and Character Set:
            The 'attributes-charset' and
            'attributes-natural-language' attributes as described
            in section 3.1.4.1 of the IPP Model and Semantics
            document.
        'requested-attributes' (1setOf keyword):
            The client OPTIONALLY supplies a set of attribute
            names and/or attribute group names in whose values the
            requester is interested. If the client omits this
            attribute, the server responds as if this attribute
            had been supplied with a value of 'all'.

    (Source: http://www.cups.org/documentation.php/spec-ipp.html#CUPS_GET_DEFAULT )

    """

    return {}

def make_cups_get_default_response(attrs, request):
    """CUPS-Get-Default Response

    The following groups of attributes are send as part of the
    CUPS-Get-Default Response:

    Group 1: Operation Attributes
        Status Message:
            The standard response status message.
        Natural Language and Character Set:
            The 'attributes-charset' and
            'attributes-natural-language' attributes as described
            in section 3.1.4.2 of the IPP Model and Semantics
            document.

    Group 2: Printer Object Attributes
        The set of requested attributes and their current values.

    (Source: http://www.cups.org/documentation.php/spec-ipp.html#CUPS_GET_DEFAULT )

    """

    response = make_empty_response(request)
    make_printer_attributes(attrs, request, response)
    return response
