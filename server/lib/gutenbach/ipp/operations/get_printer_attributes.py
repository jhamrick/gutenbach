from . import verify_operations
from . import verify_printer_uri
from . import verify_requesting_username
from . import make_empty_response
from . import make_printer_attributes

import logging
logger = logging.getLogger(__name__)

def verify_get_printer_attributes_request(request):
    """RFC 2911: 3.2.5.1 Get-Printer-Attributes Request

    The following sets of attributes are part of the Get-Printer-
    Attributes Request:

    Group 1: Operation Attributes
        Natural Language and Character Set:
            The 'attributes-charset' and 'attributes-natural-language'
            attributes as described in section 3.1.4.1.
        Target:
            The 'printer-uri' (uri) operation attribute which is the
            target for this operation as described in section 3.1.5.
        Requesting User Name:
            The 'requesting-user-name' (name(MAX)) attribute SHOULD be
            supplied by the client as described in section 8.3.
        'requested-attributes' (1setOf keyword):
            The client OPTIONALLY supplies a set of attribute names
            and/or attribute group names in whose values the requester
            is interested. The Printer object MUST support this
            attribute.  If the client omits this attribute, the
            Printer MUST respond as if this attribute had been
            supplied with a value of 'all'.
        'document-format' (mimeMediaType):
            The client OPTIONALLY supplies this attribute. The Printer
            object MUST support this attribute. This attribute is
            useful for a Printer object to determine the set of
            supported attribute values that relate to the requested
            document format.  The Printer object MUST return the
            attributes and values that it uses to validate a job on a
            create or Validate-Job operation in which this document
            format is supplied. The Printer object SHOULD return only
            (1) those attributes that are supported for the specified
            format and (2) the attribute values that are supported for
            the specified document format. By specifying the document
            format, the client can get the Printer object to eliminate
            the attributes and values that are not supported for a
            specific document format. For example, a Printer object
            might have multiple interpreters to support both
            'application/postscript' (for PostScript) and 'text/plain'
            (for text) documents. However, for only one of those
            interpreters might the Printer object be able to support
            'number-up' with values of '1', '2', and '4'. For the
            other interpreter it might be able to only support
            'number-up' with a value of '1'.  Thus a client can use
            the Get-Printer-Attributes operation to obtain the
            attributes and values that will be used to accept/reject a
            create job operation.

            If the Printer object does not distinguish between
            different sets of supported values for each different
            document format when validating jobs in the create and
            Validate-Job operations, it MUST NOT distinguish between
            different document formats in the Get-Printer-Attributes
            operation. If the Printer object does distinguish between
            different sets of supported values for each different
            document format specified by the client, this
            specialization applies only to the following Printer
            object attributes:

            - Printer attributes that are Job Template attributes
              ('xxx- default' 'xxx-supported', and 'xxx-ready' in the
              Table in Section 4.2),

            - 'pdl-override-supported',
            - 'compression-supported',
            - 'job-k-octets-supported',
            - 'job-impressions-supported',
            - 'job-media-sheets-supported',
            - 'printer-driver-installer',
            - 'color-supported', and
            - 'reference-uri-schemes-supported'

            The values of all other Printer object attributes
            (including 'document-format-supported') remain invariant
            with respect to the client supplied document format
            (except for new Printer description attribute as
            registered according to section 6.2).

            If the client omits this 'document-format' operation
            attribute, the Printer object MUST respond as if the
            attribute had been supplied with the value of the Printer
            object's 'document-format- default' attribute. It is
            RECOMMENDED that the client always supply a value for
            'document-format', since the Printer object's
            'document-format-default' may be
            'application/octet-stream', in which case the returned
            attributes and values are for the union of the document
            formats that the Printer can automatically sense.  For
            more details, see the description of the 'mimeMediaType'
            attribute syntax in section 4.1.9.

            If the client supplies a value for the 'document-format'
            Operation attribute that is not supported by the Printer,
            i.e., is not among the values of the Printer object's
            'document-format-supported' attribute, the Printer object
            MUST reject the operation and return the
            'client-error-document-format-not-supported' status code.

    """

    out = {}

    # generic operations verification
    attrs = verify_operations(request)

    # requested printer uri
    if 'printer-uri' not in attrs:
        raise err.BadRequest("Missing 'printer-uri' attribute")
    out['printer-uri']  = verify_printer_uri(attrs['printer-uri'])

    # requesting username
    if 'requesting-user-name' not in attrs:
        logger.warning("Missing 'requesting-user-name' attribute")
    else:
        out['requesting-user-name'] = verify_requesting_username(attrs['requesting-user-name'])

    if 'requested-attributes' in attrs:
        out['requested-attributes'] = None # XXX

    if 'document-format' in attrs:
        out['document-format'] = None # XXX

    return out

def make_get_printer_attributes_response(attrs, request):
    """3.2.5.2 Get-Printer-Attributes Response

    The Printer object returns the following sets of attributes as
    part of the Get-Printer-Attributes Response:

    Group 1: Operation Attributes
        Status Message:
            In addition to the REQUIRED status code returned in every
            response, the response OPTIONALLY includes a
            'status-message' (text(255)) and/or a
            'detailed-status-message' (text(MAX)) operation attribute
            as described in sections 13 and 3.1.6.
        Natural Language and Character Set:
            The 'attributes-charset' and 'attributes-natural-language'
            attributes as described in section 3.1.4.2.

    Group 2: Unsupported Attributes
        See section 3.1.7 for details on returning Unsupported
        Attributes.  The response NEED NOT contain the
        'requested-attributes' operation attribute with any supplied
        values (attribute keywords) that were requested by the client
        but are not supported by the IPP object.  If the Printer
        object does return unsupported attributes referenced in the
        'requested-attributes' operation attribute and that attribute
        included group names, such as 'all', the unsupported
        attributes MUST NOT include attributes described in the
        standard but not supported by the implementation.

    Group 3: Printer Object Attributes
        This is the set of requested attributes and their current
        values.  The Printer object ignores (does not respond with)
        any requested attribute which is not supported. The Printer
        object MAY respond with a subset of the supported attributes
        and values, depending on the security policy in
        force. However, the Printer object MUST respond with the
        'unknown' value for any supported attribute (including all
        REQUIRED attributes) for which the Printer object does not
        know the value. Also the Printer object MUST respond with the
        'no-value' for any supported attribute (including all REQUIRED
        attributes) for which the system administrator has not
        configured a value. See the description of the 'out-of-band'
        values in the beginning of Section 4.1.

    """

    response = make_empty_response(request)
    make_printer_attributes(attrs, request, response)
    return response
