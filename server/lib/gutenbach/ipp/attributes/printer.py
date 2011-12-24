__all__ = [
    'PrinterUriSupported',
    'UriAuthenticationSupported',
    'UriSecuritySupported',
    'PrinterName',
    'PrinterLocation',
    'PrinterInfo',
    'PrinterMoreInfo',
    'PrinterDriverInstaller',
    'PrinterMakeAndModel',
    'PrinterMoreInfoManufacturer',
    'PrinterState',
    'PrinterStateReasons',
    'PrinterStateMessage',
    'IppVersionsSupported',
    'OperationsSupported',
    'MultipleDocumentJobsSupported',
    'CharsetConfigured',
    'CharsetSupported',
    'NaturalLanguageConfigured',
    'GeneratedNaturalLanguageSupported',
    'DocumentFormatDefault',
    'DocumentFormatSupported',
    'PrinterIsAcceptingJobs',
    'QueuedJobCount',
    'PrinterMessageFromOperator',
    'ColorSupported',
    'ReferenceUriSchemeSupported',
    'PdlOverrideSupported',
    'PrinterUpTime',
    'PrinterCurrentTime',
    'MultipleOperationTimeOut',
    'CompressionSupported',
    'JobKOctetsSupported',
    'JobImpressionsSupported',
    'JobMediaSheetsSupported',
    'PagesPerMinute',
    'PagesPerMinuteColor'
]

from .. import Attribute
from .. import Value
from .. import errors
from .. import IntegerTags, CharacterStringTags

def PrinterUriSupported(*vals):
    """4.4.1 printer-uri-supported (1setOf uri)

    This REQUIRED Printer attribute contains at least one URI for the
    Printer object. It OPTIONALLY contains more than one URI for the
    Printer object.

    An administrator determines a Printer object's URI(s) and
    configures this attribute to contain those URIs by some means
    outside the scope of this IPP/1.1 document. The precise format of
    this URI is implementation dependent and depends on the protocol.
    See the next two sections for a description of the 'uri-security-
    supported' and 'uri-authentication-supported' attributes, both of
    which are the REQUIRED companion attributes to this 'printer-uri-
    supported' attribute. See section 2.4 on Printer object identity
    and section 8.2 on security and URIs for more information.
    
    """
    
    return Attribute(
        'printer-uri-supported',
        [Value(CharacterStringTags.URI, val) for val in vals])


def UriAuthenticationSupported(*vals):
    """4.4.2 uri-authentication-supported (1setOf type2 keyword)

    This REQUIRED Printer attribute MUST have the same cardinality
    (contain the same number of values) as the 'printer-uri-supported'
    attribute. This attribute identifies the Client Authentication
    mechanism associated with each URI listed in the 'printer-uri-
    supported' attribute. The Printer object uses the specified
    mechanism to identify the authenticated user (see section
    8.3). The 'i th' value in 'uri-authentication-supported'
    corresponds to the 'i th' value in 'printer-uri-supported' and it
    describes the authentication mechanisms used by the Printer when
    accessed via that URI. See [RFC2910] for more details on Client
    Authentication.

    """
    
    return Attribute(
        'uri-authentication-supported',
        [Value(CharacterStringTags.KEYWORD, val) for val in vals])

def UriSecuritySupported(*vals):
    """4.4.3 uri-security-supported (1setOf type2 keyword)

    This REQUIRED Printer attribute MUST have the same cardinality
    (contain the same number of values) as the 'printer-uri-supported'
    attribute. This attribute identifies the security mechanisms used
    for each URI listed in the 'printer-uri-supported' attribute. The
    'i th' value in 'uri-security-supported' corresponds to the 'i th'
    value in 'printer-uri-supported' and it describes the security
    mechanisms used for accessing the Printer object via that URI. See
    [RFC2910] for more details on security mechanisms.

    The following standard keyword values are defined:
        'none': There are no secure communication channel protocols in
                use for the given URI.
        'ssl3': SSL3 [SSL] is the secure communications channel
                protocol in use for the given URI.
        'tls':  TLS [RFC2246] is the secure communications channel
                protocol in use for the given URI.

    This attribute is orthogonal to the definition of a Client
    Authentication mechanism. Specifically, 'none' does not exclude
    Client Authentication. See section 4.4.2.

    """
    
    return Attribute(
        'uri-security-supported',
        [Value(CharacterStringTags.KEYWORD, val) for val in vals])

def PrinterName(val):
    """4.4.4 printer-name (name(127))

    This REQUIRED Printer attribute contains the name of the Printer
    object. It is a name that is more end-user friendly than a URI. An
    administrator determines a printer's name and sets this attribute
    to that name. This name may be the last part of the printer's URI
    or it may be unrelated. In non-US-English locales, a name may
    contain characters that are not allowed in a URI.

    """
    
    return Attribute(
        'printer-name',
        [Value(CharacterStringTags.NAME_WITHOUT_LANGUAGE, val)])

def PrinterLocation(val):
    """4.4.5 printer-location (text(127))

    """

    raise errors.ClientErrorAttributes, "printer-location"

def PrinterInfo(val):
    """4.4.6 printer-info (text(127))

    """

    raise errors.ClientErrorAttributes, "printer-info"

def PrinterMoreInfo(val):
    """4.4.7 printer-more-info (uri)

    """

    raise errors.ClientErrorAttributes, "printer-more-info"

def PrinterDriverInstaller(val):
    """4.4.8 printer-driver-installer (uri)

    """

    raise errors.ClientErrorAttributes, "printer-driver-installer"

def PrinterMakeAndModel(val):
    """4.4.9 printer-make-and-model (text(127))

    """

    raise errors.ClientErrorAttributes, "printer-make-and-model"

def PrinterMoreInfoManufacturer(val):
    """4.4.10 printer-more-info-manufacturer (uri)

    """

    raise errors.ClientErrorAttributes, "printer-more-info-manufacturer"

def PrinterState(val):
    """4.4.11 printer-state (type1 enum)

    This REQUIRED Printer attribute identifies the current state of
    the device. The 'printer-state reasons' attribute augments the
    'printer-state' attribute to give more detailed information about
    the Printer in the given printer state.

    A Printer object need only update this attribute before responding
    to an operation which requests the attribute; the Printer object
    NEED NOT update this attribute continually, since asynchronous
    event notification is not part of IPP/1.1. A Printer NEED NOT
    implement

    """
    
    return Attribute(
        'printer-state',
        [Value(IntegerTags.ENUM, val)])

def PrinterStateReasons(*vals):
    """4.4.12 printer-state-reasons (1setOf type2 keyword)

    This REQUIRED Printer attribute supplies additional detail about
    the device's state. Some of the these value definitions indicate
    conformance requirements; the rest are OPTIONAL.

    Each keyword value MAY have a suffix to indicate its level of
    severity. The three levels are: report (least severe), warning,
    and error (most severe).

    """
    
    return Attribute(
        'printer-state-reasons',
        [Value(CharacterStringTags.KEYWORD, val) for val in vals])

def PrinterStateMessage(val):
    """4.4.13 printer-state-message (text(MAX))

    """

    raise errors.ClientErrorAttributes, "printer-state-message"

def IppVersionsSupported(*vals):
    """4.4.14 ipp-versions-supported (1setOf type2 keyword)

    This REQUIRED attribute identifies the IPP protocol version(s)
    that this Printer supports, including major and minor versions,
    i.e., the version numbers for which this Printer implementation
    meets the conformance requirements. For version number validation,
    the Printer matches the (two-octet binary) 'version-number'
    parameter supplied by the client in each request (see sections
    3.1.1 and 3.1.8) with the (US-ASCII) keyword values of this
    attribute.

    The following standard keyword values are defined:

    '1.0': Meets the conformance requirement of IPP version 1.0 as
           specified in RFC 2566 [RFC2566] and RFC 2565 [RFC2565]
           including any extensions registered according to Section 6
           and any extension defined in this version or any future
           version of the IPP 'Model and Semantics' document or the
           IPP 'Encoding and Transport' document following the rules,
           if any, when the 'version-number' parameter is '1.0'.

    '1.1': Meets the conformance requirement of IPP version 1.1 as
           specified in this document and [RFC2910] including any
           extensions registered according to Section 6 and any
           extension defined in any future versions of the IPP 'Model
           and Semantics' document or the IPP Encoding and Transport
           document following the rules, if any, when the
           'version-number' parameter is '1.1'.

    """
    
    return Attribute(
        'ipp-versions-supported',
        [Value(CharacterStringTags.KEYWORD, val) for val in vals])

def OperationsSupported(*vals):
    """4.4.15 operations-supported (1setOf type2 enum)

    This REQUIRED Printer attribute specifies the set of supported
    operations for this Printer object and contained Job objects.
    This attribute is encoded as any other enum attribute syntax
    according to [RFC2910] as 32-bits. However, all 32-bit enum values
    for this attribute MUST NOT exceed 0x00008FFF, since these same
    values are also passed in two octets in the 'operation-id'
    parameter (see section 3.1.1) in each Protocol request with the
    two high order octets omitted in order to indicate the operation
    being performed [RFC2910].

    """
    
    return Attribute(
        'operations-supported',
        [Value(IntegerTags.ENUM, val) for val in vals])

def MultipleDocumentJobsSupported(val):
    """4.4.16 multiple-document-jobs-supported (boolean)

    This Printer attribute indicates whether or not the Printer
    supports more than one document per job, i.e., more than one
    Send-Document or Send-Data operation with document data. If the
    Printer supports the Create-Job and Send-Document operations (see
    section 3.2.4 and 3.3.1), it MUST support this attribute.

    """
    
    return Attribute(
        'multiple-document-jobs-supported',
        [Value(IntegerTags.BOOLEAN, val)])

def CharsetConfigured(val):
    """4.4.17 charset-configured (charset)

    This REQUIRED Printer attribute identifies the charset that the
    Printer object has been configured to represent 'text' and 'name'
    Printer attributes that are set by the operator, system
    administrator, or manufacturer, i.e., for 'printer-name' (name),
    'printer-location' (text), 'printer-info' (text), and
    'printer-make- and-model' (text). Therefore, the value of the
    Printer object's 'charset-configured' attribute MUST also be among
    the values of the Printer object's 'charset-supported' attribute.

    """
    
    return Attribute(
        'charset-configured',
        [Value(CharacterStringTags.CHARSET, val)])

def CharsetSupported(*vals):
    """4.4.18 charset-supported (1setOf charset)

    This REQUIRED Printer attribute identifies the set of charsets
    that the Printer and contained Job objects support in attributes
    with attribute syntax 'text' and 'name'. At least the value
    'utf-8' MUST be present, since IPP objects MUST support the UTF-8
    [RFC2279] charset. If a Printer object supports a charset, it
    means that for all attributes of syntax 'text' and 'name' the IPP
    object MUST (1) accept the charset in requests and return the
    charset in responses as needed.

    If more charsets than UTF-8 are supported, the IPP object MUST
    perform charset conversion between the charsets as described in
    Section 3.1.4.2.

    """
    
    return Attribute(
        'charset-supported',
        [Value(CharacterStringTags.CHARSET, val) for val in vals])

def NaturalLanguageConfigured(val):
    """4.4.19 natural-language-configured (naturalLanguage)

    This REQUIRED Printer attribute identifies the natural language
    that the Printer object has been configured to represent 'text'
    and 'name' Printer attributes that are set by the operator, system
    administrator, or manufacturer, i.e., for 'printer-name' (name),
    'printer-location' (text), 'printer-info' (text), and
    'printer-make- and-model' (text). When returning these Printer
    attributes, the Printer object MAY return them in the configured
    natural language specified by this attribute, instead of the
    natural language requested by the client in the
    'attributes-natural-language' operation attribute. See Section
    3.1.4.1 for the specification of the OPTIONAL multiple natural
    language support. Therefore, the value of the Printer object's
    'natural-language-configured' attribute MUST also be among the
    values of the Printer object's 'generated-natural-
    language-supported' attribute.

    """
    
    return Attribute(
        'natural-language-configured',
        [Value(CharacterStringTags.NATURAL_LANGUAGE, val)])

def GeneratedNaturalLanguageSupported(*vals):
    """4.4.20 generated-natural-language-supported (1setOf naturalLanguage)

    This REQUIRED Printer attribute identifies the natural language(s)
    that the Printer object and contained Job objects support in
    attributes with attribute syntax 'text' and 'name'. The natural
    language(s) supported depends on implementation and/or
    configuration.  Unlike charsets, IPP objects MUST accept requests
    with any natural language or any Natural Language Override whether
    the natural language is supported or not.

    If a Printer object supports a natural language, it means that for
    any of the attributes for which the Printer or Job object
    generates messages, i.e., for the 'job-state-message' and
    'printer-state- message' attributes and Operation Messages (see
    Section 3.1.5) in operation responses, the Printer and Job objects
    MUST be able to generate messages in any of the Printer's
    supported natural languages. See section 3.1.4 for the definition
    of 'text' and 'name' attributes in operation requests and
    responses.

    Note: A Printer object that supports multiple natural languages,
    often has separate catalogs of messages, one for each natural
    language supported.

    """
    
    return Attribute(
        'generated-natural-language-supported',
        [Value(CharacterStringTags.NATURAL_LANGUAGE, val) for val in vals])

def DocumentFormatDefault(val):
    """4.4.21 document-format-default (mimeMediaType)

    This REQUIRED Printer attribute identifies the document format
    that the Printer object has been configured to assume if the
    client does not supply a 'document-format' operation attribute in
    any of the operation requests that supply document data. The
    standard values for this attribute are Internet Media types
    (sometimes called MIME types). For further details see the
    description of the 'mimeMediaType' attribute syntax in Section
    4.1.9.

    """
    
    return Attribute(
        'document-format-default',
        [Value(CharacterStringTags.MIME_MEDIA_TYPE, val)])

def DocumentFormatSupported(*vals):
    """4.4.22 document-format-supported (1setOf mimeMediaType)

    This REQUIRED Printer attribute identifies the set of document
    formats that the Printer object and contained Job objects can
    support. For further details see the description of the
    'mimeMediaType' attribute syntax in Section 4.1.9.

    """
    
    return Attribute(
        'document-format-supported',
        [Value(CharacterStringTags.MIME_MEDIA_TYPE, val) for val in vals])

def PrinterIsAcceptingJobs(val):
    """4.4.23 printer-is-accepting-jobs (boolean)

    This REQUIRED Printer attribute indicates whether the printer is
    currently able to accept jobs, i.e., is accepting Print-Job,
    Print- URI, and Create-Job requests. If the value is 'true', the
    printer is accepting jobs. If the value is 'false', the Printer
    object is currently rejecting any jobs submitted to it. In this
    case, the Printer object returns the
    'server-error-not-accepting-jobs' status code.

    This value is independent of the 'printer-state' and
    'printer-state- reasons' attributes because its value does not
    affect the current job; rather it affects future jobs. This
    attribute, when 'false', causes the Printer to reject jobs even
    when the 'printer-state' is 'idle' or, when 'true', causes the
    Printer object to accepts jobs even when the 'printer-state' is
    'stopped'.

    """
    
    return Attribute(
        'printer-is-accepting-jobs',
        [Value(IntegerTags.BOOLEAN, val)])

def QueuedJobCount(val):
    """4.4.24 queued-job-count (integer(0:MAX))

    This REQUIRED Printer attribute contains a count of the number of
    jobs that are either 'pending', 'processing', 'pending-held', or
    'processing-stopped' and is set by the Printer object.

    """
    
    return Attribute(
        'queued-job-count',
        [Value(IntegerTags.INTEGER, val)])

def PrinterMessageFromOperator(val):
    """4.4.25 printer-message-from-operator (text(127))

    """

    raise errors.ClientErrorAttributes, "printer-message-from-operator"

def ColorSupported(val):
    """4.4.26 color-supported (boolean)

    """

    raise errors.ClientErrorAttributes, "color-supported"
    
def ReferenceUriSchemeSupported(val):
    """4.4.27 reference-uri-schemes-supported (1setOf uriScheme)

    """

    raise errors.ClientErrorAttributes, "reference-uri-scheme-supported"

def PdlOverrideSupported(val):
    """4.4.28 pdl-override-supported (type2 keyword)

    This REQUIRED Printer attribute expresses the ability for a
    particular Printer implementation to either attempt to override
    document data instructions with IPP attributes or not.  This
    attribute takes on the following keyword values:

    - 'attempted': This value indicates that the Printer object
      attempts to make the IPP attribute values take precedence over
      embedded instructions in the document data, however there is no
      guarantee.

    - 'not-attempted': This value indicates that the Printer object
      makes no attempt to make the IPP attribute values take
      precedence over embedded instructions in the document data.

    Section 15 contains a full description of how this attribute
    interacts with and affects other IPP attributes, especially the
    'ipp-attribute-fidelity' attribute.

    """
    
    return Attribute(
        'pdl-override-supported',
        [Value(CharacterStringTags.KEYWORD, val)])

def PrinterUpTime(val):
    """4.4.29 printer-up-time (integer(1:MAX))

    This REQUIRED Printer attribute indicates the amount of time (in
    seconds) that this Printer instance has been up and running. The
    value is a monotonically increasing value starting from 1 when the
    Printer object is started-up (initialized, booted, etc.). This
    value is used to populate the Event Time Job Description Job
    attributes 'time-at-creation', 'time-at-processing', and
    'time-at-completed' (see section 4.3.14).

    If the Printer object goes down at some value 'n', and comes back
    up, the implementation MAY:

        1. Know how long it has been down, and resume at some value
           greater than 'n', or

        2. Restart from 1.

    In other words, if the device or devices that the Printer object
    is representing are restarted or power cycled, the Printer object
    MAY continue counting this value or MAY reset this value to 1
    depending on implementation. However, if the Printer object
    software ceases running, and restarts without knowing the last
    value for 'printer- up-time', the implementation MUST reset this
    value to 1. If this value is reset and the Printer has persistent
    jobs, the Printer MUST reset the 'time-at-xxx(integer) Event Time
    Job Description attributes according to Section 4.3.14. An
    implementation MAY use both implementation alternatives, depending
    on warm versus cold start, respectively.

    """
    
    return Attribute(
        'printer-up-time',
        [Value(IntegerTags.INTEGER, val)])

def PrinterCurrentTime(val):
    """4.4.30 printer-current-time (dateTime)

    """

    raise errors.ClientErrorAttributes, "printer-current-time"

def MultipleOperationTimeOut(val):
    """4.4.31 multiple-operation-time-out (integer(1:MAX))

    This Printer attributes identifies the minimum time (in seconds)
    that the Printer object waits for additional Send-Document or
    Send-URI operations to follow a still-open Job object before
    taking any recovery actions, such as the ones indicated in section
    3.3.1. If the Printer object supports the Create-Job and
    Send-Document operations (see section 3.2.4 and 3.3.1), it MUST
    support this attribute.

    It is RECOMMENDED that vendors supply a value for this attribute
    that is between 60 and 240 seconds. An implementation MAY allow a
    system administrator to set this attribute (by means outside this
    IPP/1.1 document). If so, the system administrator MAY be able to
    set values outside this range.

    """
    
    return Attribute(
        'multiple-operation-time-out',
        [Value(IntegerTags.INTEGER, val)])

def CompressionSupported(*vals):
    """4.4.32 compression-supported (1setOf type3 keyword)

    This REQUIRED Printer attribute identifies the set of supported
    compression algorithms for document data. Compression only applies
    to the document data; compression does not apply to the encoding
    of the IPP operation itself. The supported values are used to
    validate the client supplied 'compression' operation attributes in
    Print-Job, Send-Document, and Send-URI requests.

    Standard keyword values are :
        'none': no compression is used.
        'deflate': ZIP public domain inflate/deflate) compression
            technology in RFC 1951 [RFC1951]
        'gzip' GNU zip compression technology described in RFC 1952
            [RFC1952].
        'compress': UNIX compression technology in RFC 1977 [RFC1977]

    """
    
    return Attribute(
        'compression-supported',
        [Value(CharacterStringTags.KEYWORD, val) for val in vals])

def JobKOctetsSupported(val):
    """4.4.33 job-k-octets-supported (rangeOfInteger(0:MAX))

    """

    raise errors.ClientErrorAttributes, "job-k-octets-supported"

def JobImpressionsSupported(val):
    """4.4.34 job-impressions-supported (rangeOfInteger(0:MAX))

    """

    raise errors.ClientErrorAttributes, "job-impressions-supported"

def JobMediaSheetsSupported(val):
    """4.4.35 job-media-sheets-supported (rangeOfInteger(0:MAX))

    """

    raise errors.ClientErrorAttributes, "job-media-sheets-supported"

def PagesPerMinute(val):
    """4.4.36 pages-per-minute (integer(0:MAX))

    """

    raise errors.ClientErrorAttributes, "pages-per-minute"

def PagesPerMinuteColor(val):
    """4.4.37 pages-per-minute-color (integer(0:MAX))

    """

    raise errors.ClientErrorAttributes, "pages-per-minute-color"
    
