__all__ = [
    'JobUri',
    'JobId',
    'JobPrinterUri',
    'JobMoreInfo',
    'JobName',
    'JobOriginatingUserName',
    'JobState',
    'JobStateReasons',
    'JobStateMessage',
    'JobDetailedStatusMessages',
    'JobDocumentAccessErrors',
    'NumberOfDocuments',
    'OutputDeviceAssigned',
    'TimeAtCreation',
    'TimeAtProcessing',
    'TimeAtCompleted',
    'JobPrinterUpTime',
    'DateTimeAtCreation',
    'DateTimeAtProcessing',
    'DateTimeAtCompletion',
    'NumberOfInterveningJobs',
    'JobMessageFromOperator',
    'JobKOctets',
    'JobImpressions',
    'JobMediaSheets',
    'JobKOctetsProcessed',
    'JobImpressionsCompleted',
    'JobMediaSheetsCompleted',
    'AttributesCharset',
    'AttributesNaturalLanguage',
]

from ..attribute import Attribute
from ..value import Value
from ..exceptions import ClientErrorAttributes
from ..constants import *

class JobUri(Attribute):
    """4.3.1 job-uri (uri)

    This REQUIRED attribute contains the URI for the job. The Printer
    object, on receipt of a new job, generates a URI which identifies the
    new Job. The Printer object returns the value of the 'job-uri'
    attribute as part of the response to a create request. The precise
    format of a Job URI is implementation dependent. If the Printer
    object supports more than one URI and there is some relationship
    between the newly formed Job URI and the Printer object's URI, the
    Printer object uses the Printer URI supplied by the client in the
    create request. For example, if the create request comes in over a
    secure channel, the new Job URI MUST use the same secure channel.
    This can be guaranteed because the Printer object is responsible for
    generating the Job URI and the Printer object is aware of its
    security configuration and policy as well as the Printer URI used in
    the create request.

    For a description of this attribute and its relationship to 'job-id'
    and 'job-printer-uri' attribute, see the discussion in section 2.4 on
    'Object Identity'.

    """

    def __init__(self, val):
        super(type(self), self).__init__(
            'job-uri',
            [Value(CharacterStringTags.URI, val)])

class JobId(Attribute):
    """4.3.2 job-id (integer(1:MAX))

    This REQUIRED attribute contains the ID of the job. The Printer,
    on receipt of a new job, generates an ID which identifies the new
    Job on that Printer. The Printer returns the value of the 'job-id'
    attribute as part of the response to a create request. The 0 value
    is not included to allow for compatibility with SNMP index values
    which also cannot be 0.

    For a description of this attribute and its relationship to
    'job-uri' and 'job-printer-uri' attribute, see the discussion in
    section 2.4 on 'Object Identity'.

    """
    
    def __init__(self, val):
        super(type(self), self).__init__(
            'job-id',
            [Value(IntegerTags.INTEGER, val)])

class JobPrinterUri(Attribute):
    """4.3.3 job-printer-uri (uri)

    This REQUIRED attribute identifies the Printer object that created
    this Job object. When a Printer object creates a Job object, it
    populates this attribute with the Printer object URI that was used
    in the create request. This attribute permits a client to identify
    the Printer object that created this Job object when only the Job
    object's URI is available to the client. The client queries the
    creating Printer object to determine which languages, charsets,
    operations, are supported for this Job.

    For a description of this attribute and its relationship to
    'job-uri' and 'job-id' attribute, see the discussion in section
    2.4 on 'Object Identity'.

    """

    def __init__(self, val):
        super(type(self), self).__init__(
            'job-printer-uri',
            [Value(CharacterStringTags.URI, val)])

class JobMoreInfo(Attribute):
    """4.3.4 job-more-info (uri)

    """

    def __init__(self, val):
        raise ClientErrorAttributes, "job-more-info"

class JobName(Attribute):
    """4.3.5 job-name (name(MAX))
    
    This REQUIRED attribute is the name of the job. It is a name that
    is more user friendly than the 'job-uri' attribute value. It does
    not need to be unique between Jobs. The Job's 'job-name' attribute
    is set to the value supplied by the client in the 'job-name'
    operation attribute in the create request (see Section 3.2.1.1).
    If, however, the 'job-name' operation attribute is not supplied by
    the client in the create request, the Printer object, on creation
    of the Job, MUST generate a name. The printer SHOULD generate the
    value of the Job's 'job-name' attribute from the first of the
    following sources that produces a value: 1) the 'document-name'
    operation attribute of the first (or only) document, 2) the
    'document-URI' attribute of the first (or only) document, or 3)
    any other piece of Job specific and/or Document Content
    information.

    """
    
    def __init__(self, val):
        super(type(self), self).__init__(
            'job-name',
            [Value(CharacterStringTags.NAME_WITHOUT_LANGUAGE, val)])

class JobOriginatingUserName(Attribute):
    """4.3.6 job-originating-user-name (name(MAX))

    This REQUIRED attribute contains the name of the end user that
    submitted the print job. The Printer object sets this attribute to
    the most authenticated printable name that it can obtain from the
    authentication service over which the IPP operation was received.
    Only if such is not available, does the Printer object use the
    value supplied by the client in the 'requesting-user-name'
    operation attribute of the create operation (see Sections 4.4.2,
    4.4.3, and 8).  Note: The Printer object needs to keep an internal
    originating user id of some form, typically as a credential of a
    principal, with the Job object. Since such an internal attribute
    is implementation- dependent and not of interest to clients, it is
    not specified as a Job Description attribute. This originating
    user id is used for authorization checks (if any) on all
    subsequent operations.

    """
    
    def __init__(self, val):
        super(type(self), self).__init__(
            'job-originating-user-name',
            [Value(CharacterStringTags.NAME_WITHOUT_LANGUAGE, val)])

class JobState(Attribute):
    """4.3.7 job-state (type1 enum)

    This REQUIRED attribute identifies the current state of the job.
    Even though the IPP protocol defines seven values for job states
    (plus the out-of-band 'unknown' value - see Section 4.1),
    implementations only need to support those states which are
    appropriate for the particular implementation. In other words, a
    Printer supports only those job states implemented by the output
    device and available to the Printer object implementation.
    
    """
    
    def __init__(self, val):
        super(type(self), self).__init__(
            'job-state',
            [Value(IntegerTags.ENUM, val)])

class JobStateReasons(Attribute):
    """4.3.8 job-state-reasons (1setOf type2 keyword)

    This REQUIRED attribute provides additional information about the
    job's current state, i.e., information that augments the value of
    the job's 'job-state' attribute.

    These values MAY be used with any job state or states for which
    the reason makes sense. Some of these value definitions indicate
    conformance requirements; the rest are OPTIONAL. Furthermore, when
    implemented, the Printer MUST return these values when the reason
    applies and MUST NOT return them when the reason no longer applies
    whether the value of the Job's 'job-state' attribute changed or
    not.  When the Job does not have any reasons for being in its
    current state, the value of the Job's 'job-state-reasons'
    attribute MUST be 'none'.

    Note: While values cannot be added to the 'job-state' attribute
    without impacting deployed clients that take actions upon
    receiving 'job-state' values, it is the intent that additional
    'job-state- reasons' values can be defined and registered without
    impacting such deployed clients. In other words, the
    'job-state-reasons' attribute is intended to be extensible.

    """

    def __init__(self, *vals):
        super(type(self), self).__init__(
            'job-state-reasons',
            [Value(CharacterStringTags.KEYWORD, val) for val in vals])

class JobStateMessage(Attribute):
    """4.3.9 job-state-message (text(MAX))

    """

    def __init__(self, val):
        raise ClientErrorAttributes, "job-state-message"

class JobDetailedStatusMessages(Attribute):
    """4.3.10 job-detailed-status-messages (1setOf text(MAX))

    """

    def __init__(self, *vals):
        raise ClientErrorAttributes, "job-detailed-status-messages"

class JobDocumentAccessErrors(Attribute):
    """4.3.11 job-document-access-errors (1setOf text(MAX))

    """

    def __init__(self, *vals):
        raise ClientErrorAttributes, "job-document-access-errors"

class NumberOfDocuments(Attribute):
    """4.3.12 number-of-documents (integer(0:MAX))

    """

    def __init__(self, val):
        raise ClientErrorAttributes, "number-of-documents"

class OutputDeviceAssigned(Attribute):
    """4.3.13 output-device-assigned (name(127))

    """

    def __init__(self, val):
        raise ClientErrorAttributes, "output-device-assigned"

class TimeAtCreation(Attribute):
    """4.3.14.1 time-at-creation (integer(MIN:MAX))

    This REQUIRED attribute indicates the time at which the Job object
    was created.

    """
    
    def __init__(self, val):
        super(type(self), self).__init__(
            "time-at-creation",
            [Value(IntegerTags.INTEGER, val)])

class TimeAtProcessing(Attribute):
    """4.3.14.2 time-at-processing (integer(MIN:MAX))

    This REQUIRED attribute indicates the time at which the Job object
    first began processing after the create operation or the most
    recent Restart-Job operation. The out-of-band 'no-value' value is
    returned if the job has not yet been in the 'processing' state
    (see the beginning of Section 4.1).

    """

    def __init__(self, val):
        super(type(self), self).__init__(
            "time-at-processing",
            [Value(IntegerTags.INTEGER, val)])

class TimeAtCompleted(Attribute):
    """4.3.14.3 time-at-completed (integer(MIN:MAX))

    This REQUIRED attribute indicates the time at which the Job object
    completed (or was canceled or aborted). The out-of-band 'no-value'
    value is returned if the job has not yet completed, been canceled,
    or aborted (see the beginning of Section 4.1).

    """

    def __init__(self, val):
        super(type(self), self).__init__(
            "time-at-completed",
            [Value(IntegerTags.INTEGER, val)])

class JobPrinterUpTime(Attribute):
    """4.3.14.4 job-printer-up-time (integer(1:MAX))

    This REQUIRED Job Description attribute indicates the amount of
    time (in seconds) that the Printer implementation has been up and
    running.  This attribute is an alias for the 'printer-up-time'
    Printer Description attribute (see Section 4.4.29).

    A client MAY request this attribute in a Get-Job-Attributes or
    Get- Jobs request and use the value returned in combination with
    other requested Event Time Job Description Attributes in order to
    display time attributes to a user. The difference between this
    attribute and the 'integer' value of a 'time-at-xxx' attribute is
    the number of seconds ago that the 'time-at-xxx' event occurred. A
    client can compute the wall-clock time at which the 'time-at-xxx'
    event occurred by subtracting this difference from the client's
    wall-clock time.
    
    """

    def __init__(self, val):
        super(type(self), self).__init__(
            "job-printer-up-time",
            [Value(IntegerTags.INTEGER, val)])


class DateTimeAtCreation(Attribute):
    """4.3.14.5 date-time-at-creation (dateTime)

    """

    def __init__(self, val):
        raise ClientErrorAttributes, "date-time-at-creation"

class DateTimeAtProcessing(Attribute):
    """4.3.14.6 date-time-at-processing (dateTime)

    """

    def __init__(self, val):
        raise ClientErrorAttributes, "date-time-at-processing"

class DateTimeAtCompletion(Attribute):
    """4.3.14.7 date-time-at-completed (dateTime)

    """

    def __init__(self, val):
        raise ClientErrorAttributes, "date-time-at-completion"

class NumberOfInterveningJobs(Attribute):
    """4.3.15 number-of-intervening-jobs (integer(0:MAX))

    """

    def __init__(self, val):
        raise ClientErrorAttributes, "number-of-intervening-jobs"

class JobMessageFromOperator(Attribute):
    """4.3.16 job-message-from-operator (text(127))

    """

    def __init__(self, val):
        raise ClientErrorAttributes, "job-message-from-operator"

class JobKOctets(Attribute):
    """4.3.17.1 job-k-octets (integer(0:MAX))

    This attribute specifies the total size of the document(s) in K
    octets, i.e., in units of 1024 octets requested to be processed in
    the job. The value MUST be rounded up, so that a job between 1 and
    1024 octets MUST be indicated as being 1, 1025 to 2048 MUST be 2,
    etc.

    This value MUST NOT include the multiplicative factors contributed
    by the number of copies specified by the 'copies' attribute,
    independent of whether the device can process multiple copies
    without making multiple passes over the job or document data and
    independent of whether the output is collated or not. Thus the
    value is independent of the implementation and indicates the size
    of the document(s) measured in K octets independent of the number
    of copies.  This value MUST also not include the multiplicative
    factor due to a copies instruction embedded in the document
    data. If the document data actually includes replications of the
    document data, this value will include such replication. In other
    words, this value is always the size of the source document data,
    rather than a measure of the hardcopy output to be produced.

    """
    
    def __init__(self, val):
        super(type(self), self).__init__(
            'job-k-octets',
            [Value(IntegerTags.INTEGER, val)])

class JobImpressions(Attribute):
    """4.3.17.2 job-impressions (integer(0:MAX))

    """

    def __init__(self, val):
        raise ClientErrorAttributes, "job-impressions"

class JobMediaSheets(Attribute):
    """4.3.17.3 job-media-sheets (integer(0:MAX))

    """

    def __init__(self, val):
        raise ClientErrorAttributes, "job-media-sheets"

class JobKOctetsProcessed(Attribute):
    """4.3.18.1 job-k-octets-processed (integer(0:MAX))

    """

    def __init__(self, val):
        raise ClientErrorAttributes, "job-k-octets-processed"

class JobImpressionsCompleted(Attribute):
    """4.3.18.2 job-impressions-completed (integer(0:MAX))

    """

    def __init__(self, val):
        raise ClientErrorAttributes, "job-impressions-completed"

class JobMediaSheetsCompleted(Attribute):
    """4.3.18.3 job-media-sheets-completed (integer(0:MAX))

    """

    def __init__(self, val):
        raise ClientErrorAttributes, "job-media-sheets-completed"

class AttributesCharset(Attribute):
    """4.3.19 attributes-charset (charset)

    This REQUIRED attribute is populated using the value in the client
    supplied 'attributes-charset' attribute in the create request. It
    identifies the charset (coded character set and encoding method)
    used by any Job attributes with attribute syntax 'text' and 'name'
    that were supplied by the client in the create request. See
    Section 3.1.4 for a complete description of the
    'attributes-charset' operation attribute.

    This attribute does not indicate the charset in which the 'text'
    and 'name' values are stored internally in the Job object. The
    internal charset is implementation-defined. The IPP object MUST
    convert from whatever the internal charset is to that being
    requested in an operation as specified in Section 3.1.4.

    """
    
    def __init__(self, val):
        super(type(self), self).__init__(
            'attributes-charset',
            [Value(CharacterStringTags.CHARSET, val)])

class AttributesNaturalLanguage(Attribute):
    """4.3.20 attributes-natural-language (naturalLanguage)

    This REQUIRED attribute is populated using the value in the client
    supplied 'attributes-natural-language' attribute in the create
    request. It identifies the natural language used for any Job
    attributes with attribute syntax 'text' and 'name' that were
    supplied by the client in the create request. See Section 3.1.4
    for a complete description of the 'attributes-natural-language'
    operation attribute. See Sections 4.1.1.2 and 4.1.2.2 for how a
    Natural Language Override may be supplied explicitly for each
    'text' and 'name' attribute value that differs from the value
    identified by the 'attributes-natural-language' attribute.

    """
    
    def __init__(self, val):
        super(type(self), self).__init__(
            'attributes-natural-language',
            [Value(CharacterStringTags.NATURAL_LANGUAGE, val)])
