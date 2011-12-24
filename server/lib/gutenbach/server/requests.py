from gutenbach.server.printer import GutenbachPrinter
import gutenbach.ipp as ipp
import gutenbach.ipp.constants as consts
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

class GutenbachRequestHandler(object):

    def __init__(self):
        self.printers = {
            "test": GutenbachPrinter(name="test")
            }
        self.default = "test"
    
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
        # call the handler
        handler = getattr(self, handler_name)
        logger.info("Handling request of type '%s'" % handler_name)

        # Try to handle the request
        try:
            response = handler(request)

        # Handle any errors that occur.  If an exception occurs that
        # is an IPP error, then we can get the error code from the
        # exception itself.
        except ipp.errors.IPPException:
            exctype, excval, exctb = sys.exc_info()
            logger.error("%s: %s" % (exctype.__name__, excval.message))
            response = ipp.ops.make_empty_response(request)
            excval.update_response(response)

        # If it wasn't an IPP error, then it's our fault, so mark it
        # as an internal server error
        except Exception:
            logger.error(traceback.format_exc())
            response = ipp.ops.make_empty_response(request)
            response.operation_id = ipp.StatusCodes.INTERNAL_ERROR

        return response

    def unknown_operation(self, request):
        logger.warning("Received unknown operation 0x%x" % request.operation_id)
        response = ipp.ops.make_empty_response(request)
        response.operation_id = consts.StatusCodes.OPERATION_NOT_SUPPORTED
        return response
        
    ##### Printer Commands

    @handler_for(consts.Operations.PRINT_JOB)
    def print_job(self, request):
        """RFC 2911: 3.2.1 Print-Job Operation

        This REQUIRED operation allows a client to submit a print job
        with only one document and supply the document data (rather
        than just a reference to the data). See Section 15 for the
        suggested steps for processing create operations and their
        Operation and Job Template attributes.

        """
        
        raise ipp.errors.ServerErrorOperationNotSupported

    @handler_for(consts.Operations.VALIDATE_JOB)
    def validate_job(self, request):

        raise ipp.errors.ServerErrorOperationNotSupported

    @handler_for(consts.Operations.GET_JOBS)
    def get_jobs(self, request):
        """RFC 2911: 3.2.6 Get-Jobs Operation
        
        This REQUIRED operation allows a client to retrieve the list
        of Job objects belonging to the target Printer object. The
        client may also supply a list of Job attribute names and/or
        attribute group names. A group of Job object attributes will
        be returned for each Job object that is returned.

        This operation is similar to the Get-Job-Attributes operation,
        except that this Get-Jobs operation returns attributes from
        possibly more than one object.

        """

        # verify the request and get an attribute dictionary
        req_dict = ipp.ops.verify_get_jobs_request(request)

        # lookup printer name
        printer_name = req_dict['printer-uri']
        if printer_name not in self.printers:
            raise ipp.errors.ClientErrorAttributes(
                "Invalid printer uri: %s" % printer_name,
                [request.attribute_groups[0].attributes[2]])

        # get the job attributes
        jobs = [job.get_job_attributes(request) for job in \
                self.printers[printer_name].get_jobs()]

        # build the response
        response = ipp.ops.make_get_jobs_response(jobs, request)
        return response

    @handler_for(consts.Operations.PRINT_URI)
    def print_uri(self, request):
        raise ipp.errors.ServerErrorOperationNotSupported

    @handler_for(consts.Operations.CREATE_JOB)
    def create_job(self, request):
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

        If a Printer object supports the Create-Job operation, it MUST
        also support the Send-Document operation and also MAY support
        the Send-URI operation.
        
        If the Printer object supports this operation, it MUST support
        the 'multiple-operation-time-out' Printer attribute (see
        section 4.4.31).  If the Printer object supports this
        operation, then it MUST support the
        'multiple-document-jobs-supported' Printer Description
        attribute (see section 4.4.16) and indicate whether or not it
        supports multiple-document jobs.
        
        If the Printer object supports this operation and supports
        multiple documents in a job, then it MUST support the
        'multiple-document- handling' Job Template job attribute with
        at least one value (see section 4.2.4) and the associated
        'multiple-document-handling- default' and
        'multiple-document-handling-supported' Job Template Printer
        attributes (see section 4.2).
        
        After the Create-Job operation has completed, the value of the
        'job- state' attribute is similar to the 'job-state' after a
        Print-Job, even though no document-data has arrived. A Printer
        MAY set the 'job-data-insufficient' value of the job's
        'job-state-reason' attribute to indicate that processing
        cannot begin until sufficient data has arrived and set the
        'job-state' to either 'pending' or 'pending-held'. A
        non-spooling printer that doesn't implement the 'pending' job
        state may even set the 'job-state' to 'processing', even
        though there is not yet any data to process. See sections
        4.3.7 and 4.3.8.
        
        """

        raise ipp.errors.ServerErrorOperationNotSupported
    
    @handler_for(consts.Operations.PAUSE_PRINTER)
    def pause_printer(self, request):
        raise ipp.errors.ServerErrorOperationNotSupported

    @handler_for(consts.Operations.RESUME_PRINTER)
    def resume_printer(self, request):
        raise ipp.errors.ServerErrorOperationNotSupported

    @handler_for(consts.Operations.GET_PRINTER_ATTRIBUTES)
    def get_printer_attributes(self, request):
        """RFC 2911: 3.2.5 Get-Printer-Attributes Operation

        This REQUIRED operation allows a client to request the values
        of the attributes of a Printer object.
        
        In the request, the client supplies the set of Printer
        attribute names and/or attribute group names in which the
        requester is interested. In the response, the Printer object
        returns a corresponding attribute set with the appropriate
        attribute values filled in.

        For Printer objects, the possible names of attribute groups are:
        
        - 'job-template': the subset of the Job Template attributes
          that apply to a Printer object (the last two columns of the
          table in Section 4.2) that the implementation supports for
          Printer objects.

        - 'printer-description': the subset of the attributes
          specified in Section 4.4 that the implementation supports
          for Printer objects.

        - 'all': the special group 'all' that includes all attributes
          that the implementation supports for Printer objects.
        
        Since a client MAY request specific attributes or named
        groups, there is a potential that there is some overlap. For
        example, if a client requests, 'printer-name' and 'all', the
        client is actually requesting the 'printer-name' attribute
        twice: once by naming it explicitly, and once by inclusion in
        the 'all' group. In such cases, the Printer object NEED NOT
        return each attribute only once in the response even if it is
        requested multiple times. The client SHOULD NOT request the
        same attribute in multiple ways.

        It is NOT REQUIRED that a Printer object support all
        attributes belonging to a group (since some attributes are
        OPTIONAL). However, it is REQUIRED that each Printer object
        support all group names.

        """

        # verify the request and get the attributes dictionary
        req_dict = ipp.ops.verify_get_printer_attributes_request(request)

        # lookup the printer name
        printer_name = req_dict['printer-uri']
        if printer_name not in self.printers:
            raise ipp.errors.ClientErrorAttributes(
                "Invalid printer uri: %s" % printer_name,
                [request.attribute_groups[0].attributes[2]])

        # bulid response
        response = ipp.ops.make_get_printer_attributes_response(
            self.printers[printer_name].get_printer_attributes(request), request)
        return response

    @handler_for(consts.Operations.SET_PRINTER_ATTRIBUTES)
    def set_printer_attributes(self, request):
        raise ipp.errors.ServerErrorOperationNotSupported

    ##### Job Commands

    @handler_for(consts.Operations.CANCEL_JOB)
    def cancel_job(self, request):
        raise ipp.errors.ServerErrorOperationNotSupported

    @handler_for(consts.Operations.SEND_DOCUMENT)
    def send_document(self, request):
        raise ipp.errors.ServerErrorOperationNotSupported

    @handler_for(consts.Operations.SEND_URI)
    def send_uri(self, request):
        raise ipp.errors.ServerErrorOperationNotSupported

    @handler_for(consts.Operations.GET_JOB_ATTRIBUTES)
    def get_job_attributes(self, request):
        
        # verify the request and get the attributes dictionary
        req_dict = ipp.ops.verify_get_jobs_request(request)
        
        # lookup the printer name
        printer_name = req_dict['printer-uri']
        if printer_name not in self.printers:
            raise ipp.errors.ClientErrorAttributes(
                "Invalid printer uri: %s" % printer_name,
                [request.attribute_groups[0].attributes[2]])

        # lookup the job id
        job_id = req_dict['job-id']
        try: job = self.printers[printer_name].get_job(job_id)
        except InvalidJobException:
            raise ipp.errors.ClientErrorAttributes(
                "Invalid job id: %d" % job_id,
                [request.attribute_groups[0].attributes[2]]) # XXX: this is wrong

        # XXX: we need to honor the things that the request actually asks for
        # build the response
        response = ipp.ops.make_get_job_attributes_response(
            job.get_job_attributes(request), request)
        return response

    @handler_for(consts.Operations.SET_JOB_ATTRIBUTES)
    def set_job_attributes(self, request):
        raise ipp.errors.ServerErrorOperationNotSupported

    @handler_for(consts.Operations.RESTART_JOB)
    def restart_job(self, request):
        raise ipp.errors.ServerErrorOperationNotSupported

    @handler_for(consts.Operations.PROMOTE_JOB)
    def promote_job(self, request):
        raise ipp.errors.ServerErrorOperationNotSupported

    ##### CUPS Specific Commands

    @handler_for(consts.Operations.CUPS_GET_DOCUMENT)
    def cups_get_document(self, request):
        raise ipp.errors.ServerErrorOperationNotSupported

    @handler_for(consts.Operations.CUPS_GET_DEFAULT)
    def cups_get_default(self, request):
        """The CUPS-Get-Default operation (0x4001) returns the default
        printer URI and attributes.

        (Source: http://www.cups.org/documentation.php/spec-ipp.html#CUPS_GET_DEFAULT )

        """

        # verify the request and get the attributes dictionary
        req_dict = ipp.ops.verify_cups_get_default_request(request)
        # build the response
        response = ipp.ops.make_get_printer_attributes_response(
            self.printers[self.default].get_printer_attributes(request), request)
        return response

    @handler_for(consts.Operations.CUPS_GET_PRINTERS)
    def cups_get_printers(self, request):
        """The CUPS-Get-Printers operation (0x4002) returns the
        printer attributes for every printer known to the system. This
        may include printers that are not served directly by the
        server.

        (Source: http://www.cups.org/documentation.php/spec-ipp.html#CUPS_GET_PRINTERS )
            
        """

        # verify the request and get the attributes dictionary
        req_dict = ipp.ops.verify_cups_get_printers_request(request)
        # get the printer attributes
        attrs = [self.printers[printer].get_printer_attributes(request) \
                 for printer in self.printers]
        # build the response
        response = ipp.ops.make_cups_get_printers_response(attrs, request)
        return response

    @handler_for(consts.Operations.CUPS_GET_CLASSES)
    def cups_get_classes(self, request):
        """The CUPS-Get-Classes operation (0x4005) returns the printer
        attributes for every printer class known to the system. This
        may include printer classes that are not served directly by
        the server.
        
        (Source: http://www.cups.org/documentation.php/spec-ipp.html#CUPS_GET_CLASSES )

        """

        # verify the request and get the attributes dictionaryu
        req_dict = ipp.ops.verify_cups_get_classes_request(request)
        # build the response
        response = ipp.ops.make_cups_get_classes_response(request)
        return response
