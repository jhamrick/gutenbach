from . import verify_operations
from . import verify_printer_uri
from . import verify_requesting_username
from . import make_empty_response

import logging
logger = logging.getLogger(__name__)

def verify_print_job_request(request):
    """3.2.1.1 Print-Job Request

    The following groups of attributes are supplied as part of the
    Print-Job Request:

    Group 1: Operation Attributes
        Natural Language and Character Set:
            The 'attributes-charset' and 'attributes-natural-language'
            attributes as described in section 3.1.4.1. The Printer
            object MUST copy these values to the corresponding Job
            Description attributes described in sections 4.3.19 and
            4.3.20.
        Target:
            The 'printer-uri' (uri) operation attribute which is the
            target for this operation as described in section 3.1.5.
        Requesting User Name:
            The 'requesting-user-name' (name(MAX)) attribute SHOULD be
            supplied by the client as described in section 8.3.
        'job-name' (name(MAX)):
            The client OPTIONALLY supplies this attribute. The Printer
            object MUST support this attribute. It contains the client
            supplied Job name. If this attribute is supplied by the
            client, its value is used for the 'job-name' attribute of
            the newly created Job object. The client MAY automatically
            include any information that will help the end-user
            distinguish amongst his/her jobs, such as the name of the
            application program along with information from the
            document, such as the document name, document subject, or
            source file name. If this attribute is not supplied by the
            client, the Printer generates a name to use in the
            'job-name' attribute of the newly created Job object (see
            Section 4.3.5).
        'ipp-attribute-fidelity' (boolean):
            The client OPTIONALLY supplies this attribute. The Printer
            object MUST support this attribute. The value 'true'
            indicates that total fidelity to client supplied Job
            Template attributes and values is required, else the
            Printer object MUST reject the Print-Job request. The
            value 'false' indicates that a reasonable attempt to print
            the Job object is acceptable and the Printer object MUST
            accept the Print-Job request. If not supplied, the Printer
            object assumes the value is 'false'. All Printer objects
            MUST support both types of job processing. See section 15
            for a full description of 'ipp-attribute-fidelity' and its
            relationship to other attributes, especially the Printer
            object's 'pdl-override-supported' attribute.
        'document-name' (name(MAX)):
            The client OPTIONALLY supplies this attribute. The Printer
            object MUST support this attribute.  It contains the
            client supplied document name. The document name MAY be
            different than the Job name. Typically, the client
            software automatically supplies the document name on
            behalf of the end user by using a file name or an
            application generated name. If this attribute is supplied,
            its value can be used in a manner defined by each
            implementation. Examples include: printed along with the
            Job (job start sheet, page adornments, etc.), used by
            accounting or resource tracking management tools, or even
            stored along with the document as a document level
            attribute. IPP/1.1 does not support the concept of
            document level attributes.
        'compression' (type3 keyword):
            The client OPTIONALLY supplies this attribute. The Printer
            object MUST support this attribute and the 'compression-
            supported' attribute (see section 4.4.32). The client
            supplied 'compression' operation attribute identifies the
            compression algorithm used on the document data. The
            following cases exist:
            a) If the client omits this attribute, the Printer object
               MUST assume that the data is not compressed (i.e. the
               Printer follows the rules below as if the client
               supplied the 'compression' attribute with a value of
               'none').
            b) If the client supplies this attribute, but the value is
               not supported by the Printer object, i.e., the value is
               not one of the values of the Printer object's
               'compression- supported' attribute, the Printer object
               MUST reject the request, and return the
               'client-error-compression-not- supported' status
               code. See section 3.1.7 for returning unsupported
               attributes and values.
            c) If the client supplies the attribute and the Printer
               object supports the attribute value, the Printer object
               uses the corresponding decompression algorithm on the
               document data.
            d) If the decompression algorithm fails before the Printer
               returns an operation response, the Printer object MUST
               reject the request and return the 'client-error-
               compression-error' status code.
            e) If the decompression algorithm fails after the Printer
               returns an operation response, the Printer object MUST
               abort the job and add the 'compression-error' value to
               the job's 'job-state-reasons' attribute.
            f) If the decompression algorithm succeeds, the document
               data MUST then have the format specified by the job's
               'document- format' attribute, if supplied (see
               'document-format' operation attribute definition
               below).
        'document-format' (mimeMediaType):
            The client OPTIONALLY supplies this attribute. The Printer
            object MUST support this attribute. The value of this
            attribute identifies the format of the supplied document
            data.  The following cases exist:
            a) If the client does not supply this attribute, the
               Printer object assumes that the document data is in the
               format defined by the Printer object's
               'document-format-default' attribute. (i.e. the Printer
               follows the rules below as if the client supplied the
               'document-format' attribute with a value equal to the
               printer's default value).
            b) If the client supplies this attribute, but the value is
               not supported by the Printer object, i.e., the value is
               not one of the values of the Printer object's
               'document-format- supported' attribute, the Printer
               object MUST reject the request and return the
               'client-error-document-format-not- supported' status
               code.
            c) If the client supplies this attribute and its value is
               'application/octet-stream' (i.e. to be auto-sensed, see
               Section 4.1.9.1), and the format is not one of the
               document-formats that the Printer can auto-sense, and
               this check occurs before the Printer returns an
               operation response, then the Printer MUST reject the
               request and return the
               'client-error-document-format-not-supported' status
               code.
            d) If the client supplies this attribute, and the value is
               supported by the Printer object, the Printer is capable
               of interpreting the document data.
            e) If interpreting of the document data fails before the
               Printer returns an operation response, the Printer
               object MUST reject the request and return the
               'client-error- document-format-error' status code.
            f) If interpreting of the document data fails after the
               Printer returns an operation response, the Printer
               object MUST abort the job and add the
               'document-format-error' value to the job's
               'job-state-reasons' attribute.
        'document-natural-language' (naturalLanguage):
            The client OPTIONALLY supplies this attribute. The Printer
            object OPTIONALLY supports this attribute. This attribute
            specifies the natural language of the document for those
            document-formats that require a specification of the
            natural language in order to image the document
            unambiguously. There are no particular values required for
            the Printer object to support.
        'job-k-octets' (integer(0:MAX)):
            The client OPTIONALLY supplies this attribute. The Printer
            object OPTIONALLY supports this attribute and the 'job-k-
            octets-supported' attribute (see section 4.4.33). The
            client supplied 'job-k-octets' operation attribute
            identifies the total size of the document(s) in K octets
            being submitted (see section 4.3.17.1 for the complete
            semantics). If the client supplies the attribute and the
            Printer object supports the attribute, the value of the
            attribute is used to populate the Job object's
            'job-k-octets' Job Description attribute.  For this
            attribute and the following two attributes ('job-
            impressions', and 'job-media-sheets'), if the client
            supplies the attribute, but the Printer object does not
            support the attribute, the Printer object ignores the
            client-supplied value. If the client supplies the
            attribute and the Printer supports the attribute, and the
            value is within the range of the corresponding Printer
            object's 'xxx-supported' attribute, the Printer object
            MUST use the value to populate the Job object's 'xxx'
            attribute. If the client supplies the attribute and the
            Printer supports the attribute, but the value is outside
            the range of the corresponding Printer object's 'xxx-
            supported' attribute, the Printer object MUST copy the
            attribute and its value to the Unsupported Attributes
            response group, reject the request, and return the
            'client-error- attributes-or-values-not-supported' status
            code. If the client does not supply the attribute, the
            Printer object MAY choose to populate the corresponding
            Job object attribute depending on whether the Printer
            object supports the attribute and is able to calculate or
            discern the correct value.
        'job-impressions' (integer(0:MAX)):
            The client OPTIONALLY supplies this attribute. The Printer
            object OPTIONALLY supports this attribute and the 'job-
            impressions-supported' attribute (see section 4.4.34). The
            client supplied 'job-impressions' operation attribute
            identifies the total size in number of impressions of the
            document(s) being submitted (see section 4.3.17.2 for the
            complete semantics).
            See last paragraph under 'job-k-octets'.
        'job-media-sheets' (integer(0:MAX)):
            The client OPTIONALLY supplies this attribute. The Printer
            object OPTIONALLY supports this attribute and the
            'job-media- sheets-supported' attribute (see section
            4.4.35). The client supplied 'job-media-sheets' operation
            attribute identifies the total number of media sheets to
            be produced for this job (see section 4.3.17.3 for the
            complete semantics).
            See last paragraph under 'job-k-octets'.

    Group 2: Job Template Attributes
        The client OPTIONALLY supplies a set of Job Template
        attributes as defined in section 4.2. If the client is not
        supplying any Job Template attributes in the request, the
        client SHOULD omit Group 2 rather than sending an empty
        group. However, a Printer object MUST be able to accept an
        empty group.

    Group 3: Document Content
        The client MUST supply the document data to be processed.  In
        addition to the MANDATORY parameters required for every
        operation request, the simplest Print-Job Request consists of
        just the 'attributes-charset' and
        'attributes-natural-language' operation attributes; the
        'printer-uri' target operation attribute; the Document Content
        and nothing else. In this simple case, the Printer object:
        - creates a new Job object (the Job object contains a single
          document),
        - stores a generated Job name in the 'job-name' attribute in
          the natural language and charset requested (see Section
          3.1.4.1) (if those are supported, otherwise using the
          Printer object's default natural language and charset), and
        - at job processing time, uses its corresponding default value
          attributes for the supported Job Template attributes that
          were not supplied by the client as IPP attribute or embedded
          instructions in the document data.

    """
    
    pass

def make_print_job_response(job, request):
    """3.2.1.2 Print-Job Response

    The Printer object MUST return to the client the following sets of
    attributes as part of the Print-Job Response:

    Group 1: Operation Attributes
        Status Message:
            In addition to the REQUIRED status code returned in every
            response, the response OPTIONALLY includes a
            'status-message' (text(255)) and/or a
            'detailed-status-message' (text(MAX)) operation attribute
            as described in sections 13 and 3.1.6. If the client
            supplies unsupported or conflicting Job Template
            attributes or values, the Printer object MUST reject or
            accept the Print-Job request depending on the whether the
            client supplied a 'true' or 'false' value for the
            'ipp-attribute- fidelity' operation attribute. See the
            Implementer's Guide [IPP-IIG] for a complete description
            of the suggested steps for processing a create request.
        Natural Language and Character Set:
            The 'attributes-charset' and 'attributes-natural-language'
            attributes as described in section 3.1.4.2.

    Group 2: Unsupported Attributes
        See section 3.1.7 for details on returning Unsupported
        Attributes.  The value of the 'ipp-attribute-fidelity'
        supplied by the client does not affect what attributes the
        Printer object returns in this group. The value of
        'ipp-attribute-fidelity' only affects whether the Print-Job
        operation is accepted or rejected. If the job is accepted, the
        client may query the job using the Get-Job- Attributes
        operation requesting the unsupported attributes that were
        returned in the create response to see which attributes were
        ignored (not stored on the Job object) and which attributes
        were stored with other (substituted) values.

    Group 3: Job Object Attributes
        'job-uri' (uri):
            The Printer object MUST return the Job object's URI by
            returning the contents of the REQUIRED 'job-uri' Job
            object attribute. The client uses the Job object's URI
            when directing operations at the Job object. The Printer
            object always uses its configured security policy when
            creating the new URI.  However, if the Printer object
            supports more than one URI, the Printer object also uses
            information about which URI was used in the Print-Job
            Request to generated the new URI so that the new URI
            references the correct access channel. In other words, if
            the Print-Job Request comes in over a secure channel, the
            Printer object MUST generate a Job URI that uses the
            secure channel as well.
        'job-id' (integer(1:MAX)):
            The Printer object MUST return the Job object's Job ID by
            returning the REQUIRED 'job-id' Job object attribute. The
            client uses this 'job-id' attribute in conjunction with
            the 'printer-uri' attribute used in the Print-Job Request
            when directing Job operations at the Printer object.
        'job-state' (type1 enum):
            The Printer object MUST return the Job object's REQUIRED
            'job- state' attribute. The value of this attribute (along
            with the value of the next attribute: 'job-state-reasons')
            is taken from a 'snapshot' of the new Job object at some
            meaningful point in time (implementation defined) between
            when the Printer object receives the Print-Job Request and
            when the Printer object returns the response.
        'job-state-reasons' (1setOf type2 keyword):
            The Printer object MUST return the Job object's REQUIRED
            'job- state-reasons' attribute.
        'job-state-message' (text(MAX)):
            The Printer object OPTIONALLY returns the Job object's
            OPTIONAL 'job-state-message' attribute. If the Printer
            object supports this attribute then it MUST be returned in
            the response. If this attribute is not returned in the
            response, the client can assume that the
            'job-state-message' attribute is not supported and will
            not be returned in a subsequent Job object query.
        'number-of-intervening-jobs' (integer(0:MAX)):
            The Printer object OPTIONALLY returns the Job object's
            OPTIONAL 'number-of-intervening-jobs' attribute. If the
            Printer object supports this attribute then it MUST be
            returned in the response. If this attribute is not
            returned in the response, the client can assume that the
            'number-of-intervening-jobs' attribute is not supported
            and will not be returned in a subsequent Job object query.

    Note: Since any printer state information which affects a job's
    state is reflected in the 'job-state' and 'job-state-reasons'
    attributes, it is sufficient to return only these attributes and
    no specific printer status attributes.

    Note: In addition to the MANDATORY parameters required for every
    operation response, the simplest response consists of the just the
    'attributes-charset' and 'attributes-natural-language' operation
    attributes and the 'job-uri', 'job-id', and 'job-state' Job Object
    Attributes. In this simplest case, the status code is 'successful-
    ok' and there is no 'status-message' or 'detailed-status-message'
    operation attribute.

    """

    pass
