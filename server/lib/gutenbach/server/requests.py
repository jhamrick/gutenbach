from gutenbach.server.printer import GutenbachPrinter
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

class GutenbachRequestHandler(object):

    def __init__(self):
        self.printers = {
            "test": GutenbachPrinter(name="test")
            }
        self.default = "test"

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
        expected = ipp.AttributesCharset(charset_attr.values[0].value)
        if charset_attr != expected:
            raise ipp.errors.ClientErrorBadRequest(str(charset_attr))
        if charset_attr.values[0].value != 'utf-8':
            raise ipp.errors.ClientErrorAttributes(str(charset_attr))

        # check for attributes-natural-language
        natlang_attr = operation.attributes[1]
        expected = ipp.AttributesNaturalLanguage(natlang_attr.values[0].value)
        if natlang_attr != expected:
            raise ipp.errors.ClientErrorBadRequest(str(natlang_attr))
        if natlang_attr.values[0].value != 'en-us':
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
        logger.info("Handling request of type '%s'" % handler_name)

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
        logger.warning("Received unknown operation 0x%x" % request.operation_id)
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
        
        raise ipp.errors.ServerErrorOperationNotSupported

    @handler_for(ipp.OperationCodes.VALIDATE_JOB)
    def validate_job(self, request, response):

        raise ipp.errors.ServerErrorOperationNotSupported

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

        # requested printer uri
        if 'printer-uri' not in operation:
            raise ipp.errors.ClientErrorBadRequest("Missing 'printer-uri' attribute")
        uri_attr = operation['printer-uri']
        printer_name = uri_attr.values[0].value.split("/")[-1]
        if uri_attr != ipp.PrinterUri(uri_attr.values[0].value):
            raise ipp.errors.ClientErrorBadRequest(str(uri_attr))
        if printer_name not in self.printers:
            raise ipp.errors.ClientErrorAttributes(str(uri_attr), uri_attr)
        jobs = self.printers[printer_name].get_jobs()

        # requesting username
        if 'requesting-user-name' in operation:
            username_attr = operation['requesting-user-name']
            username = username_attr.values[0].value
            if username_attr != ipp.RequestingUserName(username):
                raise ipp.errors.ClientErrorBadRequest(str(username_attr))

        # get the job attributes and add them to the response
        for job in self.printers[printer_name].get_jobs():
            attrs = job.get_job_attributes(request)
            response.attribute_groups.append(ipp.AttributeGroup(
                ipp.AttributeTags.JOB, attrs))

    @handler_for(ipp.OperationCodes.PRINT_URI)
    def print_uri(self, request, response):
        raise ipp.errors.ServerErrorOperationNotSupported

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

        Group 1: Operation Attributes
        
        """

        raise ipp.errors.ServerErrorOperationNotSupported
    
    @handler_for(ipp.OperationCodes.PAUSE_PRINTER)
    def pause_printer(self, request, response):
        raise ipp.errors.ServerErrorOperationNotSupported

    @handler_for(ipp.OperationCodes.RESUME_PRINTER)
    def resume_printer(self, request, response):
        raise ipp.errors.ServerErrorOperationNotSupported

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
            OPTIONAL 'document-format' (mimeMediaType):

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

        # requested printer uri
        if 'printer-uri' not in operation:
            raise ipp.errors.ClientErrorBadRequest("Missing 'printer-uri' attribute")
        uri_attr = operation['printer-uri']
        printer_name = uri_attr.values[0].value.split("/")[-1]
        if uri_attr != ipp.PrinterUri(uri_attr.values[0].value):
            raise ipp.errors.ClientErrorBadRequest(str(uri_attr))
        if printer_name not in self.printers:
            raise ipp.errors.ClientErrorAttributes(str(uri_attr), uri_attr)
        printer = self.printers[printer_name]

        # requesting username
        if 'requesting-user-name' in operation:
            username_attr = operation['requesting-user-name']
            username = username_attr.values[0].value
            if username_attr != ipp.RequestingUserName(username):
                raise ipp.errors.ClientErrorBadRequest(str(username_attr))

        # get attributes from the printer and add to response
        response.attribute_groups.append(ipp.AttributeGroup(
            ipp.AttributeTags.PRINTER, printer.get_printer_attributes(request)))

    @handler_for(ipp.OperationCodes.SET_PRINTER_ATTRIBUTES)
    def set_printer_attributes(self, request, response):
        raise ipp.errors.ServerErrorOperationNotSupported

    ##### Job Commands

    @handler_for(ipp.OperationCodes.CANCEL_JOB)
    def cancel_job(self, request, response):
        raise ipp.errors.ServerErrorOperationNotSupported

    @handler_for(ipp.OperationCodes.SEND_DOCUMENT)
    def send_document(self, request, response):
        raise ipp.errors.ServerErrorOperationNotSupported

    @handler_for(ipp.OperationCodes.SEND_URI)
    def send_uri(self, request, response):
        raise ipp.errors.ServerErrorOperationNotSupported

    @handler_for(ipp.OperationCodes.GET_JOB_ATTRIBUTES)
    def get_job_attributes(self, request, response):
        
        operation = request.attribute_groups[0]

        # requested printer uri
        if 'printer-uri' not in operation:
            raise ipp.errors.ClientErrorBadRequest("Missing 'printer-uri' attribute")
        uri_attr = operation['printer-uri']
        printer_name = uri_attr.values[0].value.split("/")[-1]
        if uri_attr != ipp.PrinterUri(uri_attr.values[0].value):
            raise ipp.errors.ClientErrorBadRequest(str(uri_attr))
        if printer_name not in self.printers:
            raise ipp.errors.ClientErrorAttributes(str(uri_attr), uri_attr)
        printer = self.printers[printer_name]

        if 'job-id' not in operation:
            raise ipp.errors.ClientErrorBadRequest("Missing 'job-id' attribute")
        job_id_attr = operation['job-id']
        job_id = job_id_attr.values[0].value
        if job_id_attr != ipp.JobId(job_id_attr.values[0].value):
            raise ipp.errors.ClientErrorBadRequest(str(job_id_attr))
        if job_id not in printer.jobs:
            raise ipp.errors.ClientErrorAttributes(str(job_id_attr))
        job = printer.get_job(job_id)

        # requesting username
        if 'requesting-user-name' in operation:
            username_attr = operation['requesting-user-name']
            username = username_attr.values[0].value
            if username_attr != ipp.RequestingUserName(username):
                raise ipp.errors.ClientErrorBadRequest(str(username_attr))

        # get the job attributes and add them to the response
        attrs = job.get_job_attributes(request)
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
        printer = self.printers[self.default]

        # requesting username
        if 'requesting-user-name' in operation:
            username_attr = operation['requesting-user-name']
            username = username_attr.values[0].value
            if username_attr != ipp.RequestingUserName(username):
                raise ipp.errors.ClientErrorBadRequest(str(username_attr))

        # get attributes from the printer and add to response
        response.attribute_groups.append(ipp.AttributeGroup(
            ipp.AttributeTags.PRINTER, printer.get_printer_attributes(request)))

    @handler_for(ipp.OperationCodes.CUPS_GET_PRINTERS)
    def cups_get_printers(self, request, response):
        """The CUPS-Get-Printers operation (0x4002) returns the
        printer attributes for every printer known to the system. This
        may include printers that are not served directly by the
        server.

        (Source: http://www.cups.org/documentation.php/spec-ipp.html#CUPS_GET_PRINTERS )
            
        """

        operation = request.attribute_groups[0]

        # requesting username
        if 'requesting-user-name' in operation:
            username_attr = operation['requesting-user-name']
            username = username_attr.values[0].value
            if username_attr != ipp.RequestingUserName(username):
                raise ipp.errors.ClientErrorBadRequest(str(username_attr))

        # get attributes from the printer and add to response
        for printer in self.printers.values():
            response.attribute_groups.append(ipp.AttributeGroup(
                ipp.AttributeTags.PRINTER, printer.get_printer_attributes(request)))

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

