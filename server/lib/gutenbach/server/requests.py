from . import InvalidJobException, InvalidPrinterStateException, InvalidJobStateException
import gutenbach.ipp as ipp
import logging
import traceback
import sys

# initialize logger
logger = logging.getLogger(__name__)

def handler_for(operation):
    """A decorator method to mark a function with the operation id
    that it handles.  This value will be stored in
    'func.ipp_operation'.

    """
    
    def f(func):
        func.ipp_operation = operation
        return func
    return f

def make_empty_response(request):
    # Operation attributes -- typically the same for any request
    attribute_group = ipp.AttributeGroup(
        ipp.AttributeTags.OPERATION,
        [ipp.AttributesCharset('utf-8'),
         ipp.AttributesNaturalLanguage('en-us')])
    
    # Set up the default response -- handlers will override these
    # values if they need to
    response_kwargs = {}
    response_kwargs['version']          = request.version
    response_kwargs['operation_id']     = ipp.StatusCodes.OK
    response_kwargs['request_id']       = request.request_id
    response_kwargs['attribute_groups'] = [attribute_group]
    response = ipp.Request(**response_kwargs)
    
    return response

def verify_attribute(attr, cls, length=1):
    vals = [val.value for val in attr.values]
    if attr != cls(*vals):
        raise ipp.errors.ClientErrorBadRequest(str(attr))
    if length is not None and len(vals) != length:
        raise ipp.errors.ClientErrorBadRequest(str(attr))
    return vals

class GutenbachRequestHandler(object):

    def __init__(self, gutenbach_printer):
        self.printer = gutenbach_printer

    def generic_handle(self, request):
        # check the IPP version number
        if request.version != (1, 1):
            raise ipp.errors.ServerErrorVersionNotSupported(str(request.version))

        # make sure the operation attribute group has the correct tag
        operation = request.attribute_groups[0]
        if operation.tag != ipp.AttributeTags.OPERATION:
            raise ipp.errors.ClientErrorBadRequest(
                "Attribute group does not have OPERATION tag: 0x%x" % operation.tag)

        # check charset
        charset_attr = operation.attributes[0]
        charset = verify_attribute(charset_attr, ipp.AttributesCharset)[0]
        if charset != 'utf-8':
            raise ipp.errors.ClientErrorAttributes(str(charset_attr))

        # check for attributes-natural-language
        natlang_attr = operation.attributes[1]
        natlang = verify_attribute(natlang_attr, ipp.AttributesNaturalLanguage)[0]
        if natlang != 'en-us':
            raise ipp.errors.ClientErrorAttributes(str(natlang_attr))
    
    def handle(self, request):
        # look up the handler
        handler = None
        handler_name = None
        for d in dir(self):
            if getattr(getattr(self, d), "ipp_operation", None) == request.operation_id:
                handler_name = d
                break

        # we couldn't find a handler, so default to unknown operation
        if handler_name is None:
            handler_name = "unknown_operation"

        # actually get the handler
        handler = getattr(self, handler_name)
        logger.info("request is '%s'" % handler_name)

        # try to handle the request
        try:
            self.generic_handle(request)
            response = make_empty_response(request)
            handler(request, response)

        # Handle any errors that occur.  If an exception occurs that
        # is an IPP error, then we can get the error code from the
        # exception itself.
        except ipp.errors.IPPException:
            exctype, excval, exctb = sys.exc_info()
            logger.error("%s: %s" % (exctype.__name__, excval.message))
            response = make_empty_response(request)
            excval.update_response(response)

        # If it wasn't an IPP error, then it's our fault, so mark it
        # as an internal server error
        except Exception:
            logger.error(traceback.format_exc())
            response = make_empty_response(request)
            response.operation_id = ipp.StatusCodes.INTERNAL_ERROR

        return response

    def unknown_operation(self, request, response):
        logger.warning("unknown operation 0x%x" % request.operation_id)
        response = make_empty_response(request)
        response.operation_id = ipp.StatusCodes.OPERATION_NOT_SUPPORTED
        return response
        
    ##### Printer Commands

    @handler_for(ipp.OperationCodes.PRINT_JOB)
    def print_job(self, request, response):
        """RFC 2911: 3.2.1 Print-Job Operation

        This REQUIRED operation allows a client to submit a print job
        with only one document and supply the document data (rather
        than just a reference to the data). See Section 15 for the
        suggested steps for processing create operations and their
        Operation and Job Template attributes.

        Request
        -------
        Group 1: Operation Attributes
            REQUIRED 'attributes-charset' 
            REQUIRED 'attributes-natural-language' 
            REQUIRED 'printer-uri' (uri) 
            OPTIONAL 'requesting-user-name' (name(MAX))
            OPTIONAL 'job-name' (name(MAX))
            OPTIONAL 'ipp-attribute-fidelity' (boolean)
            OPTIONAL 'document-name' (name(MAX))
            OPTIONAL 'compression' (type3 keyword)
            OPTIONAL 'document-format' (mimeMediaType)
            OPTIONAL 'document-natural-language' (naturalLanguage)
            OPTIONAL 'job-k-octets' (integer(0:MAX))
            OPTIONAL 'job-impressions' (integer(0:MAX))
            OPTIONAL 'job-media-sheets' (integer(0:MAX))
        Group 2: Job Template Attributes
        Group 3: Document Content

        Response
        --------
        Group 1: Operation Attributes
            OPTIONAL 'status-message' (text(255))
            OPTIONAL 'detailed-status-message' (text(MAX))
            REQUIRED 'attributes-charset'
            REQUIRED 'attributes-natural-language'
        Group 2: Unsupported Attributes
        Group 3: Job Object Attributes
            REQUIRED 'job-uri' (uri)
            REQUIRED 'job-id' (integer(1:MAX))
            REQUIRED 'job-state' (type1 enum)
            REQUIRED 'job-state-reasons' (1setOf type2 keyword)
            OPTIONAL 'job-state-message' (text(MAX))
            OPTIONAL 'number-of-intervening-jobs' (integer(0:MAX))

        """

        operation = request.attribute_groups[0]
        document = request.data        
        user_name = None
        job_name = None
        job_k_octets = None
        document_format = None
        document_natural_language = None
        compression = None
        last_document = None
        # requested printer uri
        if 'printer-uri' not in operation:
            raise ipp.errors.ClientErrorBadRequest("Missing 'printer-uri' attribute")
        printer_uri = verify_attribute(operation['printer-uri'], ipp.PrinterUri)[0]
        if printer_uri not in self.printer.uris:
            raise ipp.errors.ClientErrorAttributes(
                str(operation['printer-uri']), operation['printer-uri'])

        if 'requesting-user-name' in operation:
            user_name = verify_attribute(
                operation['requesting-user-name'], ipp.RequestingUserName)[0]

        if 'job-name' in operation:
            job_name = verify_attribute(
                operation['job-name'], ipp.JobName)[0]

        if 'job-k-octets' in operation:
            job_k_octets = verify_attribute(
                operation['job-k-octets'], ipp.JobKOctets)[0]

        if 'ipp-attribute-fidelity' in operation:
            pass # don't care
        if 'job-impressions' in operation:
            pass # don't care
        if 'job-media-sheets' in operation:
            pass # don't care

        # get attributes from the printer and add to response
        try:
            job_id = self.printer.print_job(document,
                    document_name               = document_name,
                    document_format             = document_format,
                    document_natural_language   = document_natural_language,
                    requesting_user_name        = user_name,
                    compression                 = compression,
                    job_name                    = job_name,
                    job_k_octets                = job_k_octets)
        except InvalidJobException:
            raise ipp.errors.ClientErrorNotFound("bad job: %d" % job_id)


        attrs = self.printer.get_job_attributes(job_id)
     
        #Actually append the attributes we pulled
        response.attribute_groups.append(ipp.AttributeGroup(
            ipp.AttributeTags.JOB, attrs))

        
    @handler_for(ipp.OperationCodes.VALIDATE_JOB)
    def validate_job(self, request, response):
        """3.2.3 Validate-Job Operation

        This REQUIRED operation is similar to the Print-Job operation
        (section 3.2.1) except that a client supplies no document data and
        the Printer allocates no resources (i.e., it does not create a new
        Job object).  This operation is used only to verify capabilities of a
        printer object against whatever attributes are supplied by the client
        in the Validate-Job request.  By using the Validate-Job operation a
        client can validate that an identical Print-Job operation (with the
        document data) would be accepted. The Validate-Job operation also
        performs the same security negotiation as the Print-Job operation
        (see section 8), so that a client can check that the client and
        Printer object security requirements can be met before performing a
        Print-Job operation.

        The Validate-Job operation does not accept a 'document-uri' attribute
        in order to allow a client to check that the same Print-URI operation
        will be accepted, since the client doesn't send the data with the
        Print-URI operation.  The client SHOULD just issue the Print-URI
        request.

        The Printer object returns the same status codes, Operation
        Attributes (Group 1) and Unsupported Attributes (Group 2) as the
        Print-Job operation.  However, no Job Object Attributes (Group 3) are
        returned, since no Job object is created.
        """
        operation = request.attribute_groups[0]
        user_name = None
        job_name = None
        job_k_octets = None
        # requested printer uri
        if 'printer-uri' not in operation:
            raise ipp.errors.ClientErrorBadRequest("Missing 'printer-uri' attribute")
        printer_uri = verify_attribute(operation['printer-uri'], ipp.PrinterUri)[0]
        if printer_uri not in self.printer.uris:
            raise ipp.errors.ClientErrorAttributes(
                str(operation['printer-uri']), operation['printer-uri'])

        if 'requesting-user-name' in operation:
            user_name = verify_attribute(
                operation['requesting-user-name'], ipp.RequestingUserName)[0]

        if 'job-name' in operation:
            job_name = verify_attribute(
                operation['job-name'], ipp.JobName)[0]

        if 'job-k-octets' in operation:
            job_k_octets = verify_attribute(
                operation['job-k-octets'], ipp.JobKOctets)[0]
       
        self.printer.verify_job(requesting_user_name=user_name,
            job_name=job_name,
            job_k_octets = job_k_octets) 

        #raise ipp.errors.ServerErrorOperationNotSupported

    @handler_for(ipp.OperationCodes.GET_JOBS)
    def get_jobs(self, request, response):
        """3.2.6 Get-Jobs Operation
        
        This REQUIRED operation allows a client to retrieve the list
        of Job objects belonging to the target Printer object. The
        client may also supply a list of Job attribute names and/or
        attribute group names. A group of Job object attributes will
        be returned for each Job object that is returned.

        This operation is similar to the Get-Job-Attributes operation,
        except that this Get-Jobs operation returns attributes from
        possibly more than one object.

        Request
        -------
        Group 1: Operation Attributes
            REQUIRED 'attributes-charset' 
            REQUIRED 'attributes-natural-language' 
            REQUIRED 'printer-uri' (uri) 
            OPTIONAL 'requesting-user-name' (name(MAX))
            OPTIONAL 'limit' (integer(1:MAX)) 
            OPTIONAL 'requested-attributes' (1setOf type2 keyword) 
            OPTIONAL 'which-jobs' (type2 keyword) 
            OPTIONAL 'my-jobs' (boolean) 

        Response
        --------
        Group 1: Operation Attributes
            OPTIONAL 'status-message' (text(255))
            OPTIONAL 'detailed-status-message' (text(MAX))
            REQUIRED 'attributes-charset'
            REQUIRED 'attributes-natural-language'
        Group 2: Unsupported Attributes
        Groups 3 to N: Job Object Attributes

        """

        operation = request.attribute_groups[0]

        # initialize operation attribute variables
        printer_name = None
        user = None
        limit = None
        attributes = None
        which_jobs = None
        my_jobs = None

        # requested printer uri
        if 'printer-uri' not in operation:
            raise ipp.errors.ClientErrorBadRequest("Missing 'printer-uri' attribute")
        printer_uri = verify_attribute(operation['printer-uri'], ipp.PrinterUri)[0]
        if printer_uri not in self.printer.uris and printer_uri != "ipp://localhost/":
            raise ipp.errors.ClientErrorAttributes(
                str(operation['printer-uri']), operation['printer-uri'])

        # optional attributes
        if 'limit' in operation:
            limit = verify_attribute(
                operation['limit'], ipp.Limit)[0]
            
        if 'requested-attributes' in operation:
            attributes = verify_attribute(
                operation['requested-attributes'], ipp.RequestedAttributes, length=None)
            
        if 'which-jobs' in operation:
            which_jobs = verify_attribute(
                operation['which-jobs'], ipp.WhichJobs)[0]
            
        if 'my-jobs' in operation:
            my_jobs = verify_attribute(
                operation['my-jobs'], ipp.MyJobs)[0]

        if 'requesting-user-name' in operation:
            user = verify_attribute(
                operation['requesting-user-name'], ipp.RequestingUserName)[0]
            # ignore if we're not filtering jobs by user
            if not my_jobs:
                user = None
            
        # get the job attributes and add them to the response
        job_attrs = self.printer.get_jobs(
            which_jobs=which_jobs,
            requesting_user_name=user,
            requested_attributes=attributes)
        for attrs in job_attrs:
            response.attribute_groups.append(ipp.AttributeGroup(
                ipp.AttributeTags.JOB, attrs))

    @handler_for(ipp.OperationCodes.PRINT_URI)
    def print_uri(self, request, response):
        """3.2.2 Print-URI Operation

        This OPTIONAL operation is identical to the Print-Job operation
        (section 3.2.1) except that a client supplies a URI reference to the
        document data using the 'document-uri' (uri) operation attribute (in
        Group 1) rather than including the document data itself.  Before
        returning the response, the Printer MUST validate that the Printer
        supports the retrieval method (e.g., http, ftp, etc.) implied by the
        URI, and MUST check for valid URI syntax.  If the client-supplied URI
        scheme is not supported, i.e. the value is not in the Printer
        object's 'referenced-uri-scheme-supported' attribute, the Printer
        object MUST reject the request and return the 'client-error-uri-
        scheme-not-supported' status code.

        The IPP Printer MAY validate the accessibility of the document as
        part of the operation or subsequently.  If the Printer determines an
        accessibility problem before returning an operation response, it
        rejects the request and returns the 'client-error-document-access-
        error' status code.  The Printer MAY also return a specific document
        access error code using the 'document-access-error' operation
        attribute (see section 3.1.6.4).

        If the Printer determines this document accessibility problem after
        accepting the request and returning an operation response with one
        of the successful status codes, the Printer adds the
        'document-access- error' value to the job's 'job-state-reasons'
        attribute and MAY populate the job's 'job-document-access-errors'
        Job Description attribute (see section 4.3.11).  See The
        Implementer's Guide [IPP- IIG] for suggested additional checks.
                                                                              
        If the Printer object supports this operation, it MUST support the
        'reference-uri-schemes-supported' Printer attribute (see section 4.4.27).

        It is up to the IPP object to interpret the URI and subsequently
        'pull' the document from the source referenced by the URI string."""
        operation = request.attribute_groups[0]
        document = request.data        
        user_name = None
        job_name = None
        job_k_octets = None
        document_format = None
        document_natural_language = None
        compression = None
        last_document = None


        # requested printer uri
        if 'printer-uri' not in operation:
            raise ipp.errors.ClientErrorBadRequest("Missing 'printer-uri' attribute")
        printer_uri = verify_attribute(operation['printer-uri'], ipp.PrinterUri)[0]
        if printer_uri not in self.printer.uris:
            raise ipp.errors.ClientErrorAttributes(
                str(operation['printer-uri']), operation['printer-uri'])

        if 'requesting-user-name' in operation:
            user_name = verify_attribute(
                operation['requesting-user-name'], ipp.RequestingUserName)[0]

        if 'job-name' in operation:
            job_name = verify_attribute(
                operation['job-name'], ipp.JobName)[0]

        if 'job-k-octets' in operation:
            job_k_octets = verify_attribute(
                operation['job-k-octets'], ipp.JobKOctets)[0]

        if 'ipp-attribute-fidelity' in operation:
            pass # don't care
        if 'job-impressions' in operation:
            pass # don't care
        if 'job-media-sheets' in operation:
            pass # don't care

        # get attributes from the printer and add to response
        try:
            job_id = self.printer.print_uri(document,
                    document_name               = document_name,
                    document_format             = document_format,
                    document_natural_language   = document_natural_language,
                    requesting_user_name        = user_name,
                    compression                 = compression,
                    job_name                    = job_name,
                    job_k_octets                = job_k_octets)
        except InvalidJobException:
            raise ipp.errors.ClientErrorNotFound("bad job: %d" % job_id)


        attrs = self.printer.get_job_attributes(job_id)
     
        #Actually append the attributes we pulled
        response.attribute_groups.append(ipp.AttributeGroup(
            ipp.AttributeTags.JOB, attrs))

 
       #raise ipp.errors.ServerErrorOperationNotSupported

    @handler_for(ipp.OperationCodes.CREATE_JOB)
    def create_job(self, request, response):
        """RFC 2911: 3.2.4 Create-Job Operation

        This OPTIONAL operation is similar to the Print-Job operation
        (section 3.2.1) except that in the Create-Job request, a
        client does not supply document data or any reference to
        document data. Also, the client does not supply any of the
        'document-name', 'document- format', 'compression', or
        'document-natural-language' operation attributes. This
        operation is followed by one or more Send-Document or Send-URI
        operations. In each of those operation requests, the client
        OPTIONALLY supplies the 'document-name', 'document-format',
        and 'document-natural-language' attributes for each document
        in the multi-document Job object.

        Request
        -------
        Group 1: Operation Attributes
            REQUIRED 'attributes-charset' 
            REQUIRED 'attributes-natural-language' 
            REQUIRED 'printer-uri' (uri) 
            OPTIONAL 'requesting-user-name' (name(MAX))
            OPTIONAL 'job-name' (name(MAX))
            OPTIONAL 'ipp-attribute-fidelity' (boolean)
            OPTIONAL 'job-k-octets' (integer(0:MAX))
            OPTIONAL 'job-impressions' (integer(0:MAX))
            OPTIONAL 'job-media-sheets' (integer(0:MAX))
        Group 2: Job Template Attributes

        Response
        --------
        Group 1: Operation Attributes
            OPTIONAL 'status-message' (text(255))
            OPTIONAL 'detailed-status-message' (text(MAX))
            REQUIRED 'attributes-charset'
            REQUIRED 'attributes-natural-language'
        Group 2: Unsupported Attributes
        Group 3: Job Object Attributes
            REQUIRED 'job-uri' (uri)
            REQUIRED 'job-id' (integer(1:MAX))
            REQUIRED 'job-state' (type1 enum)
            REQUIRED 'job-state-reasons' (1setOf type2 keyword)
            OPTIONAL 'job-state-message' (text(MAX))
            OPTIONAL 'number-of-intervening-jobs' (integer(0:MAX))
        
        """

        operation = request.attribute_groups[0]

        printer_uri = None
        requesting_user_name = None
        job_name = None
        ipp_attribute_fidelity=None
        job_k_octets = None

        # requested printer uri
        if 'printer-uri' not in operation:
            raise ipp.errors.ClientErrorBadRequest("Missing 'printer-uri' attribute")
        printer_uri = verify_attribute(operation['printer-uri'], ipp.PrinterUri)[0]
        if printer_uri not in self.printer.uris:
            raise ipp.errors.ClientErrorAttributes(
                str(operation['printer-uri']), operation['printer-uri'])

        if 'requesting-user-name' in operation:
            user_name = verify_attribute(
                operation['requesting-user-name'], ipp.RequestingUserName)[0]

        if 'job-name' in operation:
            job_name = verify_attribute(
                operation['job-name'], ipp.JobName)[0]

        if 'job-k-octets' in operation:
            job_k_octets = verify_attribute(
                operation['job-k-octets'], ipp.JobKOctets)[0]

        if 'ipp-attribute-fidelity' in operation:
            pass # don't care
        if 'job-impressions' in operation:
            pass # don't care
        if 'job-media-sheets' in operation:
            pass # don't care

        # get attributes from the printer and add to response
        job_id = self.printer.create_job(
            requesting_user_name=requesting_user_name,
            job_name=job_name,
            job_k_octets=job_k_octets)
        attrs = self.printer.get_job_attributes(job_id)
        response.attribute_groups.append(ipp.AttributeGroup(
            ipp.AttributeTags.JOB, attrs))
    
    @handler_for(ipp.OperationCodes.PAUSE_PRINTER)
    def pause_printer(self, request, response):
        """
            3.2.7 Pause-Printer Operation

            This OPTIONAL operation allows a client to stop the Printer object
            from scheduling jobs on all its devices.  Depending on
            implementation, the Pause-Printer operation MAY also stop the Printer
            from processing the current job or jobs.  Any job that is currently
            being printed is either stopped as soon as the implementation permits
            or is completed, depending on implementation.  The Printer object
            MUST still accept create operations to create new jobs, but MUST
            prevent any jobs from entering the 'processing' state.

            If the Pause-Printer operation is supported, then the Resume-Printer
            operation MUST be supported, and vice-versa.

            The IPP Printer stops the current job(s) on its device(s) that were
            in the 'processing' or 'processing-stopped' states as soon as the
            implementation permits.  If the implementation will take appreciable
            time to stop, the IPP Printer adds the 'moving-to-paused' value to
            the Printer object's 'printer-state-reasons' attribute (see section
            4.4.12).  When the device(s) have all stopped, the IPP Printer
            transitions the Printer object to the 'stopped' state, removes the
            'moving-to-paused' value, if present, and adds the 'paused' value to
            the Printer object's 'printer-state-reasons' attribute.

            When the current job(s) complete that were in the 'processing' state,
            the IPP Printer transitions them to the 'completed' state.  When the
            current job(s) stop in mid processing that were in the 'processing'
            state, the IPP Printer transitions them to the 'processing-stopped'
            state and adds the 'printer-stopped' value to the job's 'job-state-
            reasons' attribute.

            For any jobs that are 'pending' or 'pending-held', the 'printer-
            stopped' value of the jobs' 'job-state-reasons' attribute also
            applies.  However, the IPP Printer NEED NOT update those jobs' 'job-
            state-reasons' attributes and only need return the 'printer-stopped'
            value when those jobs are queried (so-called 'lazy evaluation').

            Whether the Pause-Printer operation affects jobs that were submitted
            to the device from other sources than the IPP Printer object in the
            same way that the Pause-Printer operation affects jobs that were
            submitted to the IPP Printer object using IPP, depends on
            implementation, i.e., on whether the IPP protocol is being used as a
            universal management protocol or just to manage IPP jobs,
            respectively.

            The IPP Printer MUST accept the request in any state and transition
            the Printer to the indicated new 'printer-state' before returning as
            follows:

            Current        New      'printer   IPP Printer's response status
            'printer-    'printer-   -state-          code and action:
            state'       state'    reasons'

            'idle'       'stopped'    'paused'  'successful-ok'
            'processing' 'processing' 'moving-  OPTION 1: 'successful-ok';
                                                      to-       Later, when all output has
                                                      paused'   stopped, the 'printer-state'
                                                                            becomes 'stopped', and the
                                                                            'paused' value replaces the
                                                                            'moving-to-paused' value in the
                                                                            'printer-state-reasons'
                                                                            attribute
            'processing' 'stopped'    'paused'  OPTION 2: 'successful-ok';
                                                                            all device output stopped
                                                                            immediately
            'stopped'    'stopped'    'paused'  'successful-ok'

            Access Rights: The authenticated user (see section 8.3) performing
            this operation must be an operator or administrator of the Printer
            object (see Sections 1 and 8.5).   Otherwise, the IPP Printer MUST
            reject the operation and return:  'client-error-forbidden', 'client-
            error-not-authenticated', or 'client-error-not-authorized' as
            appropriate.

            3.2.7.1 Pause-Printer Request

            The following groups of attributes are part of the Pause-Printer
            Request:

            Group 1: Operation Attributes

            Natural Language and Character Set:
            The 'attributes-charset' and 'attributes-natural-language'
            attributes as described in section 3.1.4.1.

            Target:
            The 'printer-uri' (uri) operation attribute which is the target
            for this operation as described in section 3.1.5.

            Requesting User Name:
            The 'requesting-user-name' (name(MAX)) attribute SHOULD be
            supplied by the client as described in section 8.3.

            3.2.7.2 Pause-Printer Response

            The following groups of attributes are part of the Pause-Printer
            Response:

            Group 1: Operation Attributes

            Status Message:
            In addition to the REQUIRED status code returned in every
            response, the response OPTIONALLY includes a 'status-message'
            (text(255)) and/or a 'detailed-status-message' (text(MAX))
            operation attribute as described in sections 13 and  3.1.6.

            Natural Language and Character Set:
            The 'attributes-charset' and 'attributes-natural-language'
            attributes as described in section 3.1.4.2.

            Group 2: Unsupported Attributes

            See section 3.1.7 for details on returning Unsupported Attributes.

   
    """
    operation = request.attribute_groups[0]
    printer_uri = None
    user_name   = None
    if 'printer-uri' not in operation:
            raise ipp.errors.ClientErrorBadRequest("Missing 'printer-uri' attribute")
        printer_uri = verify_attribute(operation['printer-uri'], ipp.PrinterUri)[0]
        if printer_uri not in self.printer.uris:
            raise ipp.errors.ClientErrorAttributes(
                str(operation['printer-uri']), operation['printer-uri'])

    if 'requesting-user-name' in operation:
        user_name = verify_attribute(
            operation['requesting-user-name'], ipp.RequestingUserName)[0]
   self.printer.pause_printer()


    #    raise ipp.errors.ServerErrorOperationNotSupported

    @handler_for(ipp.OperationCodes.RESUME_PRINTER)
    def resume_printer(self, request, response):
        """
        3.2.8 Resume-Printer Operation

        This operation allows a client to resume the Printer object
        scheduling jobs on all its devices.  The Printer object MUST remove
        the 'paused' and 'moving-to-paused' values from the Printer object's
        'printer-state-reasons' attribute, if present.  If there are no other
        reasons to keep a device paused (such as media-jam), the IPP Printer
        is free to transition itself to the 'processing' or 'idle' states,
        depending on whether there are jobs to be processed or not,
        respectively, and the device(s) resume processing jobs.

        If the Pause-Printer operation is supported, then the Resume-Printer
        operation MUST be supported, and vice-versa.

        The IPP Printer removes the 'printer-stopped' value from any job's
        'job-state-reasons' attributes contained in that Printer.

        The IPP Printer MUST accept the request in any state, transition the
        Printer object to the indicated new state as follows:


        Current    New 'printer-  IPP Printer's response status code and
        'printer-      state'                     action:
        state'

        'idle'       'idle'         'successful-ok'
        'processing' 'processing'   'successful-ok'

        'stopped'    'processing'   'successful-ok';
                                                   when there are jobs to be processed
        'stopped'    'idle'         'successful-ok';
                                                   when there are no jobs to be processed.

        Access Rights: The authenticated user (see section 8.3) performing
        this operation must be an operator or administrator of the Printer
        object (see Sections 1 and 8.5).  Otherwise, the IPP Printer MUST
        reject the operation and return:  'client-error-forbidden', 'client-
        error-not-authenticated', or 'client-error-not-authorized' as
        appropriate.

        The Resume-Printer Request and Resume-Printer Response have the same
        attribute groups and attributes as the Pause-Printer operation (see
        sections 3.2.7.1 and 3.2.7.2).                 
        """
    operation = request.attribute_groups[0]
    printer_uri = None
    user_name   = None
    if 'printer-uri' not in operation:
            raise ipp.errors.ClientErrorBadRequest("Missing 'printer-uri' attribute")
        printer_uri = verify_attribute(operation['printer-uri'], ipp.PrinterUri)[0]
        if printer_uri not in self.printer.uris:
            raise ipp.errors.ClientErrorAttributes(
                str(operation['printer-uri']), operation['printer-uri'])

    if 'requesting-user-name' in operation:
        user_name = verify_attribute(
            operation['requesting-user-name'], ipp.RequestingUserName)[0]
   self.printer.resume_printer()


    @handler_for(ipp.OperationCodes.GET_PRINTER_ATTRIBUTES)
    def get_printer_attributes(self, request, response):
        """RFC 2911: 3.2.5 Get-Printer-Attributes Operation

        This REQUIRED operation allows a client to request the values
        of the attributes of a Printer object.
        
        In the request, the client supplies the set of Printer
        attribute names and/or attribute group names in which the
        requester is interested. In the response, the Printer object
        returns a corresponding attribute set with the appropriate
        attribute values filled in.

        Request
        -------

        Group 1: Operation Attributes
            REQUIRED 'attributes-charset' 
            REQUIRED 'attributes-natural-language' 
            REQUIRED 'printer-uri' (uri)
            OPTIONAL 'requesting-user-name' (name(MAX))
            OPTIONAL 'requested-attributes' (1setOf type2 keyword) 
            OPTIONAL 'document-format' (mimeMediaType)
            
        Response
        --------

        Group 1: Operation Attributes
            OPTIONAL 'status-message' (text(255))
            OPTIONAL 'detailed-status-message' (text(MAX))
            REQUIRED 'attributes-charset'
            REQUIRED 'attributes-natural-language'
        Group 2: Unsupported Attributes
        Group 3: Printer Object Attributes

        """

        operation = request.attribute_groups[0]

        printer_uri = None
        requesting_user_name = None
        requested_attributes = None
        document_format = None

        # requested printer uri
        if 'printer-uri' not in operation:
            raise ipp.errors.ClientErrorBadRequest("Missing 'printer-uri' attribute")
        printer_uri = verify_attribute(operation['printer-uri'], ipp.PrinterUri)[0]
        if printer_uri not in self.printer.uris:
            raise ipp.errors.ClientErrorAttributes(
                str(operation['printer-uri']), operation['printer-uri'])

        # optional attributes
        if 'requesting-user-name' in operation:
            user_name = verify_attribute(
                operation['requesting-user-name'], ipp.RequestingUserName)[0]
            
        if 'requested-attributes' in operation:
            requested_attributes = verify_attribute(
                operation['requested-attributes'], ipp.RequestedAttributes, length=None)

        if 'document-format' in operation:
            pass # XXX: todo

        # get attributes from the printer and add to response
        response.attribute_groups.append(ipp.AttributeGroup(
            ipp.AttributeTags.PRINTER,
            self.printer.get_printer_attributes(
                requested_attributes=requested_attributes)))

    @handler_for(ipp.OperationCodes.SET_PRINTER_ATTRIBUTES)
    def set_printer_attributes(self, request, response):

        raise ipp.errors.ServerErrorOperationNotSupported

    ##### Job Commands

    @handler_for(ipp.OperationCodes.CANCEL_JOB)
    def cancel_job(self, request, response):
        """3.3.3 Cancel-Job Operation

        This REQUIRED operation allows a client to cancel a Print Job from
        the time the job is created up to the time it is completed, canceled,
        or aborted. Since a Job might already be printing by the time a
        Cancel-Job is received, some media sheet pages might be printed
        before the job is actually terminated.

        The IPP object MUST accept or reject the request based on the job's
        current state and transition the job to the indicated new state as
        follows:

        Current State       New State           Response
        -----------------------------------------------------------------
        pending             canceled            successful-ok
        pending-held        canceled            successful-ok
        processing          canceled            successful-ok
        processing          processing          successful-ok               See Rule 1
        processing          processing          client-error-not-possible   See Rule 2
        processing-stopped  canceled            successful-ok
        processing-stopped  processing-stopped  successful-ok               See Rule 1
        processing-stopped  processing-stopped  client-error-not-possible   See Rule 2
        completed           completed           client-error-not-possible
        canceled            canceled            client-error-not-possible
        aborted             aborted             client-error-not-possible

        Rule 1: If the implementation requires some measurable time to
        cancel the job in the 'processing' or 'processing-stopped' job
        states, the IPP object MUST add the 'processing-to-stop-point'
        value to the job's 'job-state-reasons' attribute and then
        transition the job to the 'canceled' state when the processing
        ceases (see section 4.3.8).

        Rule 2: If the Job object already has the
        'processing-to-stop-point' value in its 'job-state-reasons'
        attribute, then the Printer object MUST reject a Cancel-Job
        operation.

        Access Rights: The authenticated user (see section 8.3)
        performing this operation must either be the job owner or an
        operator or administrator of the Printer object (see Sections
        1 and 8.5).  Otherwise, the IPP object MUST reject the
        operation and return: 'client-error-forbidden',
        'client-error-not-authenticated', or
        'client-error-not-authorized' as appropriate.

        Request
        -------

        Group 1: Operation Attributes
            REQUIRED 'attributes-charset' 
            REQUIRED 'attributes-natural-language' 
            REQUIRED 'job-id' (integer(1:MAX)) and 'printer-uri' (uri)
              -or-   'job-uri' (uri)
            OPTIONAL 'requesting-user-name' (name(MAX))
            OPTIONAL 'message' (text(127))
            
        Response
        --------

        Group 1: Operation Attributes
            OPTIONAL 'status-message' (text(255))
            OPTIONAL 'detailed-status-message' (text(MAX))
            REQUIRED 'attributes-charset'
            REQUIRED 'attributes-natural-language'
        Group 2: Unsupported Attributes

        """

        operation = request.attribute_groups[0]

        job_id = None
        printer_uri = None
        requesting_user_name = None
        message = None

        # required attributes
        if 'job-id' in operation and 'printer-uri' in operation:
            job_id = verify_attribute(operation['job-id'], ipp.JobId)[0]
            printer_uri = verify_attribute(operation['printer-uri'], ipp.PrinterUri)[0]
            if printer_uri not in self.printer.uris:
                raise ipp.errors.ClientErrorAttributes(
                    str(operation['printer-uri']), operation['printer-uri'])

        elif 'job-uri' in operation:
            job_uri = verify_attribute(operation['job-uri'], ipp.JobUri)[0]
            job_id = int(job_uri.split("/")[-1])

        if 'requesting-user-name' in operation:
            requesting_user_name = verify_attribute(
                operation['requesting-user-name'], ipp.RequestingUserName)[0]

        try:
            self.printer.cancel_job(job_id, requesting_user_name=requesting_user_name)
        except InvalidJobException:
            raise ipp.errors.ClientErrorNotFound("bad job: %d" % job_id)

    @handler_for(ipp.OperationCodes.SEND_DOCUMENT)
    def send_document(self, request, response):
        """3.3.1 Send-Document Operation
        
        This OPTIONAL operation allows a client to create a
        multi-document Job object that is initially 'empty' (contains
        no documents). In the Create-Job response, the Printer object
        returns the Job object's URI (the 'job-uri' attribute) and the
        Job object's 32-bit identifier (the 'job-id' attribute). For
        each new document that the client desires to add, the client
        uses a Send-Document operation. Each Send- Document Request
        contains the entire stream of document data for one document.

        If the Printer supports this operation but does not support
        multiple documents per job, the Printer MUST reject subsequent
        Send-Document operations supplied with data and return the
        'server-error-multiple- document-jobs-not-supported'. However,
        the Printer MUST accept the first document with a 'true' or
        'false' value for the 'last-document' operation attribute (see
        below), so that clients MAY always submit one document jobs
        with a 'false' value for 'last-document' in the first
        Send-Document and a 'true' for 'last-document' in the second
        Send-Document (with no data).
        
        Since the Create-Job and the send operations (Send-Document or
        Send- URI operations) that follow could occur over an
        arbitrarily long period of time for a particular job, a client
        MUST send another send operation within an IPP Printer defined
        minimum time interval after the receipt of the previous
        request for the job. If a Printer object supports the
        Create-Job and Send-Document operations, the Printer object
        MUST support the 'multiple-operation-time-out' attribute (see
        section 4.4.31). This attribute indicates the minimum number
        of seconds the Printer object will wait for the next send
        operation before taking some recovery action.

        An IPP object MUST recover from an errant client that does not
        supply a send operation, sometime after the minimum time
        interval specified by the Printer object's
        'multiple-operation-time-out' attribute.

        Access Rights: The authenticated user (see section 8.3)
        performing this operation must either be the job owner (as
        determined in the Create-Job operation) or an operator or
        administrator of the Printer object (see Sections 1 and
        8.5). Otherwise, the IPP object MUST reject the operation and
        return: 'client-error-forbidden', 'client-
        error-not-authenticated', or 'client-error-not-authorized' as
        appropriate.

        Request
        -------

        Group 1: Operation Attributes
            REQUIRED 'attributes-charset' 
            REQUIRED 'attributes-natural-language' 
            REQUIRED 'job-id' (integer(1:MAX)) and 'printer-uri' (uri)
              -or-   'job-uri' (uri)
            OPTIONAL 'requesting-user-name' (name(MAX))
            OPTIONAL 'document-name' (name(MAX))
            OPTIONAL 'compression' (type3 keyword)
            OPTIONAL 'document-format' (mimeMediaType)
            OPTIONAL 'document-natural-language' (naturalLanguage)
            OPTIONAL 'last-document' (boolean)
        Group 2: Document Content
            
        Response
        --------

        Group 1: Operation Attributes
            OPTIONAL 'status-message' (text(255))
            OPTIONAL 'detailed-status-message' (text(MAX))
            REQUIRED 'attributes-charset'
            REQUIRED 'attributes-natural-language'
        Group 2: Unsupported Attributes
        Group 3: Job Object Attributes
            REQUIRED 'job-uri' (uri)
            REQUIRED 'job-id' (integer(1:MAX))
            REQUIRED 'job-state' (type1 enum)
            REQUIRED 'job-state-reasons' (1setOf type2 keyword)
            OPTIONAL 'job-state-message' (text(MAX))
            OPTIONAL 'number-of-intervening-jobs' (integer(0:MAX))

        """
        
        operation = request.attribute_groups[0]

        job_id = None
        printer_uri = None
        requesting_user_name = None
        document_name = None
        compression = None
        document_format = None
        document_natural_language = None
        last_document = None

        # required attributes
        if 'job-id' not in operation:
            raise ipp.errors.ClientErrorBadRequest("Missing 'job-id' attribute")
        job_id = verify_attribute(operation['job-id'], ipp.JobId)[0]

        if 'last-document' not in operation:
            raise ipp.errors.ClientErrorBadRequest("Missing 'last-document' attribute")
        last_document = verify_attribute(operation['last-document'], ipp.LastDocument)[0]
        if not last_document:
            raise ipp.errors.ServerErrorMultipleJobsNotSupported

        # optional attributes
        if 'printer-uri' in operation:
            printer_uri = verify_attribute(operation['printer-uri'], ipp.PrinterUri)[0]
            if printer_uri not in self.printer.uris:
                raise ipp.errors.ClientErrorAttributes(
                    str(operation['printer-uri']), operation['printer-uri'])

        if 'requesting-user-name' in operation:
            user_name = verify_attribute(
                operation['requesting-user-name'], ipp.RequestingUserName)[0]

        if 'document-name' in operation:
            document_name = verify_attribute(
                operation['document-name'], ipp.DocumentName)[0]

        if 'compression' in operation:
            compression = verify_attribute(
                operation['compression'], ipp.Compression)[0]

        if 'document-format' in operation:
            document_format = verify_attribute(
                operation['document-format'], ipp.DocumentFormat)[0]

        if 'document-natural-language' in operation:
            document_natural_language = verify_attribute(
                operation['document_natural_language'],
                ipp.DocumentNaturalLanguage)[0]

        try:
            self.printer.send_document(
                job_id,
                request.data,
                document_name=document_name,
                document_format=document_format,
                document_natural_language=document_natural_language,
                requesting_user_name=user_name,
                compression=compression,
                last_document=last_document)
            attrs = self.printer.get_job_attributes(job_id)
        except InvalidJobException:
            raise ipp.errors.ClientErrorNotFound("bad job: %d" % job_id)

        response.attribute_groups.append(ipp.AttributeGroup(
            ipp.AttributeTags.JOB, attrs))

    @handler_for(ipp.OperationCodes.SEND_URI)
    def send_uri(self, request, response):

        """3.2.2 Send URI

        This OPTIONAL operation is identical to the Send-Document
        operation (see section 3.3.1) except that a client MUST supply
        a URI reference ('document-uri' operation attribute) rather
        than the document data itself.  If a Printer object supports
        this operation, clients can use both Send-URI or Send-Document
        operations to add new documents to an existing multi-document
        Job object.  However, if a client needs to indicate that the
        previous Send-URI or Send-Document was the last document, the
        client MUST use the Send-Document operation with no document
        data and the 'last-document' flag set to 'true' (rather than
        using a Send-URI operation with no 'document-uri' operation
        attribute).

        If a Printer object supports this operation, it MUST also
        support the Print-URI operation (see section 3.2.2).

        The Printer object MUST validate the syntax and URI scheme of
        the supplied URI before returning a response, just as in the
        Print-URI operation.  The IPP Printer MAY validate the
        accessibility of the document as part of the operation or
        subsequently (see section 3.2.2).

        Request
        -------

        Group 1: Operation Attributes
            REQUIRED 'attributes-charset' 
            REQUIRED 'attributes-natural-language' 
            REQUIRED 'job-id' (integer(1:MAX)) and 'printer-uri' (uri)
            REQUIRED 'document-uri' (uri)
            OPTIONAL 'job-uri' (uri)
            OPTIONAL 'requesting-user-name' (name(MAX))
            OPTIONAL 'document-name' (name(MAX))
            OPTIONAL 'compression' (type3 keyword)
            OPTIONAL 'document-format' (mimeMediaType)
            OPTIONAL 'document-natural-language' (naturalLanguage)
            
        Response
        --------

        Group 1: Operation Attributes
            OPTIONAL 'status-message' (text(255))
            OPTIONAL 'detailed-status-message' (text(MAX))
            REQUIRED 'attributes-charset'
            REQUIRED 'attributes-natural-language'
        Group 2: Unsupported Attributes
        Group 3: Job Object Attributes
            REQUIRED 'job-uri' (uri)
            REQUIRED 'job-id' (integer(1:MAX))
            REQUIRED 'job-state' (type1 enum)
            REQUIRED 'job-state-reasons' (1setOf type2 keyword)
            OPTIONAL 'job-state-message' (text(MAX))
            OPTIONAL 'number-of-intervening-jobs' (integer(0:MAX))

        """
        
        operation = request.attribute_groups[0]

        job_id = None
        printer_uri = None
        requesting_user_name = None
        document_name = None
        compression = None
        document_format = None
        document_natural_language = None
        last_document = None

        # required attributes
        if 'job-id' not in operation:
            raise ipp.errors.ClientErrorBadRequest("Missing 'job-id' attribute")
        job_id = verify_attribute(operation['job-id'], ipp.JobId)[0]

        if 'last-document' not in operation:
            raise ipp.errors.ClientErrorBadRequest("Missing 'last-document' attribute")
        last_document = verify_attribute(operation['last-document'], ipp.LastDocument)[0]

        if 'document-uri' not in operation:
            raise ipp.errors.ClientErrorBadRequest("Missing 'document-uri' attribute")
        document_uri = verify_attribute(operation['document-uri'], ipp.DocumentUri)[0]
        if not last_document:
            raise ipp.errors.ServerErrorMultipleJobsNotSupported

        # optional attributes
        if 'printer-uri' in operation:
            printer_uri = verify_attribute(operation['printer-uri'], ipp.PrinterUri)[0]
            if printer_uri not in self.printer.uris:
                raise ipp.errors.ClientErrorAttributes(
                    str(operation['printer-uri']), operation['printer-uri'])

        if 'requesting-user-name' in operation:
            user_name = verify_attribute(
                operation['requesting-user-name'], ipp.RequestingUserName)[0]

        if 'document-name' in operation:
            document_name = verify_attribute(
                operation['document-name'], ipp.DocumentName)[0]

        if 'compression' in operation:
            compression = verify_attribute(
                operation['compression'], ipp.Compression)[0]

        if 'document-format' in operation:
            document_format = verify_attribute(
                operation['document-format'], ipp.DocumentFormat)[0]

        if 'document-natural-language' in operation:
            document_natural_language = verify_attribute(
                operation['document_natural_language'],
                ipp.DocumentNaturalLanguage)[0]

        try:
            self.printer.send_uri(
                job_id,
                document_uri,
                document_name=document_name,
                document_format=document_format,
                document_natural_language=document_natural_language,
                requesting_user_name=user_name,
                compression=compression,
                last_document=last_document)
            attrs = self.printer.get_job_attributes(job_id)
        except InvalidJobException:
            raise ipp.errors.ClientErrorNotFound("bad job: %d" % job_id)

        response.attribute_groups.append(ipp.AttributeGroup(
            ipp.AttributeTags.JOB, attrs))

    @handler_for(ipp.OperationCodes.GET_JOB_ATTRIBUTES)
    def get_job_attributes(self, request, response):
        """3.3.4 Get-Job-Attributes Operation

        This REQUIRED operation allows a client to request the values
        of attributes of a Job object and it is almost identical to
        the Get- Printer-Attributes operation (see section 3.2.5). The
        only differences are that the operation is directed at a Job
        object rather than a Printer object, there is no
        'document-format' operation attribute used when querying a Job
        object, and the returned attribute group is a set of Job
        object attributes rather than a set of Printer object
        attributes.

        For Jobs, the possible names of attribute groups are:
          - 'job-template': the subset of the Job Template attributes
            that apply to a Job object (the first column of the table
            in Section 4.2) that the implementation supports for Job
            objects.
          - 'job-description': the subset of the Job Description
            attributes specified in Section 4.3 that the
            implementation supports for Job objects.
          - 'all': the special group 'all' that includes all
            attributes that the implementation supports for Job
            objects.

        Since a client MAY request specific attributes or named
        groups, there is a potential that there is some overlap. For
        example, if a client requests, 'job-name' and
        'job-description', the client is actually requesting the
        'job-name' attribute once by naming it explicitly, and once by
        inclusion in the 'job-description' group. In such cases, the
        Printer object NEED NOT return the attribute only once in the
        response even if it is requested multiple times. The client
        SHOULD NOT request the same attribute in multiple ways.

        It is NOT REQUIRED that a Job object support all attributes
        belonging to a group (since some attributes are
        OPTIONAL). However it is REQUIRED that each Job object support
        all these group names.

        Request
        -------

        Group 1: Operation Attributes
            REQUIRED 'attributes-charset' 
            REQUIRED 'attributes-natural-language' 
            REQUIRED 'job-id' (integer(1:MAX)) and 'printer-uri' (uri)
              -or-   'job-uri' (uri)
            OPTIONAL 'requesting-user-name' (name(MAX))
            OPTIONAL 'requested-attributes' (1setOf keyword)
            
        Response
        --------

        Group 1: Operation Attributes
            OPTIONAL 'status-message' (text(255))
            OPTIONAL 'detailed-status-message' (text(MAX))
            REQUIRED 'attributes-charset'
            REQUIRED 'attributes-natural-language'
        Group 2: Unsupported Attributes
        Group 3: Job Object Attributes

        """
        
        operation = request.attribute_groups[0]

        job_id = None
        printer_uri = None
        requesting_user_name = None
        requested_attributes = None

        # required attributes
        if 'job-id' not in operation:
            raise ipp.errors.ClientErrorBadRequest("Missing 'job-id' attribute")
        job_id = verify_attribute(operation['job-id'], ipp.JobId)[0]

        # optional attributes
        if 'printer-uri' in operation:
            printer_uri = verify_attribute(operation['printer-uri'], ipp.PrinterUri)[0]
            if printer_uri not in self.printer.uris:
                raise ipp.errors.ClientErrorAttributes(
                    str(operation['printer-uri']), operation['printer-uri'])

        # optional attributes
        if 'requesting-user-name' in operation:
            user_name = verify_attribute(
                operation['requesting-user-name'], ipp.RequestingUserName)[0]
            
        if 'requested-attributes' in operation:
            requested_attributes = verify_attribute(
                operation['requested-attributes'], ipp.RequestedAttributes, length=None)

        # get the job attributes and add them to the response
        try:
            attrs = self.printer.get_job_attributes(
                job_id,
                requested_attributes=requested_attributes)
        except InvalidJobException:
            raise ipp.errors.ClientErrorNotFound("bad job: %d" % job_id)

        response.attribute_groups.append(ipp.AttributeGroup(
            ipp.AttributeTags.JOB, attrs))

    @handler_for(ipp.OperationCodes.SET_JOB_ATTRIBUTES)
    def set_job_attributes(self, request, response):
        
        raise ipp.errors.ServerErrorOperationNotSupported

    @handler_for(ipp.OperationCodes.RESTART_JOB)
    def restart_job(self, request, response):
        raise ipp.errors.ServerErrorOperationNotSupported

    @handler_for(ipp.OperationCodes.PROMOTE_JOB)
    def promote_job(self, request, response):
        raise ipp.errors.ServerErrorOperationNotSupported

    ##### CUPS Specific Commands

    @handler_for(ipp.OperationCodes.CUPS_GET_DOCUMENT)
    def cups_get_document(self, request, response):
        raise ipp.errors.ServerErrorOperationNotSupported

    @handler_for(ipp.OperationCodes.CUPS_GET_DEFAULT)
    def cups_get_default(self, request, response):
        """The CUPS-Get-Default operation (0x4001) returns the default
        printer URI and attributes.

        Request
        -------

        Group 1: Operation Attributes
            REQUIRED 'attributes-charset' 
            REQUIRED 'attributes-natural-language' 
            OPTIONAL 'requested-attributes' (1setOf type2 keyword)

        Response
        --------

        Group 1: Operation Attributes
            OPTIONAL 'status-message' (text(255))
            REQUIRED 'attributes-charset'
            REQUIRED 'attributes-natural-language'
        Group 2: Printer Object Attributes

        (Source: http://www.cups.org/documentation.php/spec-ipp.html#CUPS_GET_DEFAULT )

        """

        operation = request.attribute_groups[0]
        requested_attributes = None
        
        if 'requested-attributes' in operation:
            requested_attributes = verify_attribute(
                operation['requested-attributes'], ipp.RequestedAttributes, length=None)

        # get attributes from the printer and add to response
        attrs = self.printer.get_printer_attributes(
            requested_attributes=requested_attributes)
        response.attribute_groups.append(ipp.AttributeGroup(
            ipp.AttributeTags.PRINTER, attrs))

    @handler_for(ipp.OperationCodes.CUPS_GET_PRINTERS)
    def cups_get_printers(self, request, response):
        """The CUPS-Get-Printers operation (0x4002) returns the
        printer attributes for every printer known to the system. This
        may include printers that are not served directly by the
        server.

        (Source: http://www.cups.org/documentation.php/spec-ipp.html#CUPS_GET_PRINTERS )
            
        """

        # get attributes from the printer and add to response
        response.attribute_groups.append(ipp.AttributeGroup(
            ipp.AttributeTags.PRINTER, self.printer.get_printer_attributes()))

    @handler_for(ipp.OperationCodes.CUPS_GET_CLASSES)
    def cups_get_classes(self, request, response):
        """The CUPS-Get-Classes operation (0x4005) returns the printer
        attributes for every printer class known to the system. This
        may include printer classes that are not served directly by
        the server.

        Request
        -------

        Group 1: Operation Attributes
            REQUIRED 'attributes-charset' 
            REQUIRED 'attributes-natural-language'
            OPTIONAL 'first-printer-name' (name(127)) CUPS 1.2/Mac OS X 10.5
            OPTIONAL 'limit' (integer (1:MAX))
            OPTIONAL 'printer-location' (text(127)) CUPS 1.1.7
            OPTIONAL 'printer-type' (type2 enum) CUPS 1.1.7
            OPTIONAL 'printer-type-mask' (type2 enum) CUPS 1.1.7
            OPTIONAL 'requested-attributes' (1setOf keyword)
            OPTOINAL 'requested-user-name' (name(127)) CUPS 1.2/Mac OS X 10.5
            OPTIONAL 'requested-attributes' (1setOf type2 keyword)

        Response
        --------

        Group 1: Operation Attributes
            OPTIONAL 'status-message' (text(255))
            REQUIRED 'attributes-charset'
            REQUIRED 'attributes-natural-language'
        Group 2: Printer Class Object Attributes

        (Source: http://www.cups.org/documentation.php/spec-ipp.html#CUPS_GET_CLASSES )

        """
        
        raise ipp.errors.ServerErrorOperationNotSupported

