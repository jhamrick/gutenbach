from .value import Value
from .attribute import Attribute
from .attributegroup import AttributeGroup
from .request import Request
from .constants import AttributeTags, StatusCodes, operations_attribute_value_tags
import exceptions as err
import logging

logger = logging.getLogger(__name__)

def verify_operations(request):
    """Pretty much all requests have the first attribute group for
    operation attributes, and these all have 'attributes-charset' and
    'attributes-natural-language' as the first two attributes.  This
    method just generically verifies that these attributes are there.

    """

    # XXX: check version
    if False:
        raise err.VersionNotSupported(str(request.version))

    # check operation id
    if False:
        raise err.OperationNotSupported(str(request.operation_id))

    # check operation attributes tag
    op_attrs = request.attribute_groups[0]
    if op_attrs.tag != AttributeTags.OPERATION:
        raise err.BadRequest(
            "Attribute group does not have OPERATION tag: 0x%x" % op_attrs.tag)

    # # check compression
    # if False:
    #     raise err.CompressionNotSupported

    # # check document format
    # if False:
    #     raise err.DocumentFormatNotSupported

    # # check document uri
    # if False:
    #     raise err.UriSchemeNotSupported

    # check charset
    charset_attr = op_attrs.attributes[0]
    if charset_attr.name != 'attributes-charset':
        raise err.BadRequest(
            "Attribute is not attributes-charset: %s" % charset_attr.name)
    if len(charset_attr.values) != 1:
        raise err.BadRequest(
            "Too many values for attributes-charset: %d" % len(charset_attr.values))
    # check charset value
    charset_value = charset_attr.values[0]
    if charset_value.tag != operations_attribute_value_tags['attributes-charset']:
        raise err.BadRequest(
            "Wrong tag for charset value: 0x%x" % charset_value.tag)
    if charset_value.value != 'utf-8':
        raise err.CharsetNotSupported(str(charset_value.value))

    # check for attributes-natural-language
    natlang_attr = op_attrs.attributes[1]
    if natlang_attr.name != 'attributes-natural-language':
        raise err.BadRequest(
            "Attribute is not attributes-natural-language: %s" % natlang_attr.name)
    if len(charset_attr.values) != 1:
        raise err.BadRequest(
            "Too many values for attributes-natural-language: %s" % len(natlang_attr.values))
    # check natural language value
    natlang_value = natlang_attr.values[0]
    if natlang_value.tag != operations_attribute_value_tags['attributes-natural-language']:
        raise err.BadRequest(
            "Natural language value does not have NATURAL_LANGUAGE tag: 0x%x" % natlang_value.tag)
    if natlang_value.value != 'en-us':
        raise err.Attributes(
            "Invalid natural language value: %s" % natlang_value.value, [natlang_attr])

    return dict([(attr.name, attr.values) for attr in op_attrs.attributes])

def verify_printer_uri(values):
    if len(values) != 1:
        raise err.BadRequest(
            "Requesting printer uri attribute has too many values: %d" % len(values))
    uri_value = values[0]
    if uri_value.tag != operations_attribute_value_tags['printer-uri']:
        raise err.BadRequest(
            "Bad value tag (expected URI): 0x%x" % uri_value_tag)
    
    # actually get the printer name
    # XXX: hack -- CUPS will strip the port from the request, so
    # we can't do an exact comparison (also the hostname might be
    # different, depending on the CNAME or whether it's localhost)
    uri = uri_value.value.split("/")[-1]
    return uri

def verify_requesting_username(values):
    if len(values) != 1:
        raise err.BadRequest(
            "Requesting user name attribute has too many values: %d" % len(values))
    requser_value = values[0]
    if requser_value.tag != operations_attribute_value_tags['requesting-user-name']:
        raise err.BadRequest(
            "Bad value tag (expected NAME_WITHOUT_LANGUAGE): 0x%x" % requser_value.tag)
    
    return requser_value.value

def make_empty_response(request):
    # Operation attributes -- typically the same for any request
    attributes = [
        Attribute(
            'attributes-charset',
            [Value(operations_attribute_value_tags['attributes-charset'], 'utf-8')]),
        Attribute(
            'attributes-natural-language',
            [Value(operations_attribute_value_tags['attributes-natural-language'], 'en-us')])
        ]
    # Put the operation attributes in a group
    attribute_group = AttributeGroup(
        AttributeTags.OPERATION,
        attributes)

    # Set up the default response -- handlers will override these
    # values if they need to
    response_kwargs = {}
    response_kwargs['version']          = request.version
    response_kwargs['operation_id']     = StatusCodes.OK
    response_kwargs['request_id']       = request.request_id
    response_kwargs['attribute_groups'] = [attribute_group]
    response = Request(**response_kwargs)

    return response

#### GET-JOBS

def verify_get_jobs_request(request):
    """RFC 2911 3.2.6.1 Get-Jobs Request

    The client submits the Get-Jobs request to a Printer object.
    
    The following groups of attributes are part of the Get-Jobs
    Request:

    Group 1: Operation Attributes
        Natural Language and Character Set:
            The 'attributes-charset' and
            'attributes-natural-language' attributes as described
            in section 3.1.4.1.
        Target:
            The 'printer-uri' (uri) operation attribute which is
            the target for this operation as described in section
            3.1.5.
        Requesting User Name:
            The 'requesting-user-name' (name(MAX)) attribute
            SHOULD be supplied by the client as described in
            section 8.3.
        'limit' (integer(1:MAX)):
            The client OPTIONALLY supplies this attribute. The
            Printer object MUST support this attribute. It is an
            integer value that determines the maximum number of
            jobs that a client will receive from the Printer even
            if 'which-jobs' or 'my-jobs' constrain which jobs are
            returned. The limit is a 'stateless limit' in that if
            the value supplied by the client is 'N', then only the
            first 'N' jobs are returned in the Get-Jobs Response.
            There is no mechanism to allow for the next 'M' jobs
            after the first 'N' jobs. If the client does not
            supply this attribute, the Printer object responds
            with all applicable jobs.
        'requested-attributes' (1setOf type2 keyword):
            The client OPTIONALLY supplies this attribute. The
            Printer object MUST support this attribute. It is a
            set of Job attribute names and/or attribute groups
            names in whose values the requester is
            interested. This set of attributes is returned for
            each Job object that is returned. The allowed
            attribute group names are the same as those defined in
            the Get-Job-Attributes operation in section 3.3.4. If
            the client does not supply this attribute, the Printer
            MUST respond as if the client had supplied this
            attribute with two values: 'job-uri' and 'job-id'.
        'which-jobs' (type2 keyword):
            The client OPTIONALLY supplies this attribute. The
            Printer object MUST support this attribute. It
            indicates which Job objects MUST be returned by the
            Printer object. The values for this attribute are:
             - 'completed': This includes any Job object whose
               state is 'completed', 'canceled', or 'aborted'.
             - 'not-completed': This includes any Job object whose
               state is 'pending', 'processing',
               'processing-stopped', or 'pending-held'.
            A Printer object MUST support both values. However, if
            the implementation does not keep jobs in the
            'completed', 'canceled', and 'aborted' states, then it
            returns no jobs when the 'completed' value is
            supplied.  If a client supplies some other value, the
            Printer object MUST copy the attribute and the
            unsupported value to the Unsupported Attributes
            response group, reject the request, and return the
            'client-error-attributes-or-values-not-supported'
            status code.  If the client does not supply this
            attribute, the Printer object MUST respond as if the
            client had supplied the attribute with a value of
            'not-completed'.
        'my-jobs' (boolean):
            The client OPTIONALLY supplies this attribute. The
            Printer object MUST support this attribute. It
            indicates whether jobs from all users or just the jobs
            submitted by the requesting user of this request MUST
            be considered as candidate jobs to be returned by the
            Printer object. If the client does not supply this
            attribute, the Printer object MUST respond as if the
            client had supplied the attribute with a value of
            'false', i.e., jobs from all users. The means for
            authenticating the requesting user and matching the
            jobs is described in section 8.

    """

    out = {}

    # generic operations verification
    attrs = verify_operations(request)

    # requested printer uri
    if 'printer-uri' not in attrs:
        raise err.BadRequest("Missing 'printer-uri' attribute")
    out['printer-uri'] = verify_printer_uri(attrs['printer-uri'])
    
    # requesting username
    if 'requesting-user-name' not in attrs:
        logger.warning("Missing 'requesting-user-name' attribute")
    else:
        out['requesting-user-name'] = verify_requesting_username(attrs['requesting-user-name'])

    if 'limit' in attrs:
        out['limit'] = None # XXX

    if 'requested-attributes' in attrs:
        out['requested-attributes'] = None # XXX

    if 'which-jobs' in attrs:
        out['which-jobs'] = None # XXX

    if 'my-jobs' in attrs:
        out['my-jobs'] = None # XXX

    return out

def make_get_jobs_response(self, request):
    """RFC 2911: 3.2.6.2 Get-Jobs Response
        
    The Printer object returns all of the Job objects up to the number
    specified by the 'limit' attribute that match the criteria as
    defined by the attribute values supplied by the client in the
    request. It is possible that no Job objects are returned since
    there may literally be no Job objects at the Printer, or there may
    be no Job objects that match the criteria supplied by the
    client. If the client requests any Job attributes at all, there is
    a set of Job Object Attributes returned for each Job object.

    It is not an error for the Printer to return 0 jobs. If the
    response returns 0 jobs because there are no jobs matching the
    criteria, and the request would have returned 1 or more jobs
    with a status code of 'successful-ok' if there had been jobs
    matching the criteria, then the status code for 0 jobs MUST be
    'successful-ok'.

    Group 1: Operation Attributes
        Status Message:
            In addition to the REQUIRED status code returned in
            every response, the response OPTIONALLY includes a
            'status-message' (text(255)) and/or a
            'detailed-status-message' (text(MAX)) operation
            attribute as described in sections 13 and 3.1.6.
        Natural Language and Character Set:
            The 'attributes-charset' and
            'attributes-natural-language' attributes as described
            in section 3.1.4.2.

    Group 2: Unsupported Attributes
        See section 3.1.7 for details on returning Unsupported
        Attributes.  The response NEED NOT contain the
        'requested-attributes' operation attribute with any
        supplied values (attribute keywords) that were requested
        by the client but are not supported by the IPP object.  If
        the Printer object does return unsupported attributes
        referenced in the 'requested-attributes' operation
        attribute and that attribute included group names, such as
        'all', the unsupported attributes MUST NOT include
        attributes described in the standard but not supported by
        the implementation.

    Groups 3 to N: Job Object Attributes
        The Printer object responds with one set of Job Object
        Attributes for each returned Job object. The Printer
        object ignores (does not respond with) any requested
        attribute or value which is not supported or which is
        restricted by the security policy in force, including
        whether the requesting user is the user that submitted the
        job (job originating user) or not (see section
        8). However, the Printer object MUST respond with the
        'unknown' value for any supported attribute (including all
        REQUIRED attributes) for which the Printer object does not
        know the value, unless it would violate the security
        policy. See the description of the 'out-of- band' values
        in the beginning of Section 4.1.

        Jobs are returned in the following order:
        - If the client requests all 'completed' Jobs (Jobs in the
          'completed', 'aborted', or 'canceled' states), then the
          Jobs are returned newest to oldest (with respect to
          actual completion time)
        - If the client requests all 'not-completed' Jobs (Jobs in
          the 'pending', 'processing', 'pending-held', and
          'processing- stopped' states), then Jobs are returned in
          relative chronological order of expected time to
          complete (based on whatever scheduling algorithm is
          configured for the Printer object).

    """

    pass

## GET-PRINTER-ATTRIBUTES

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


def make_get_printer_attributes_response(self, request):
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
    pass
