from gutenbach.server.printer import GutenbachPrinter
import gutenbach.ipp as ipp
import gutenbach.ipp.constants as const
import logging

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
        response = handler(request)
        return response

    def unknown_operation(self, request):
        logger.warning("Received unknown operation 0x%x" % request.operation_id)
        response = ipp.ops.make_empty_response(request)
        response.operation_id = const.StatusCodes.OPERATION_NOT_SUPPORTED
        return response
        
    ##### Printer Commands

    def print_job(self, request):
        pass

    def validate_job(self, request):
        pass

    @handler_for(const.Operations.GET_JOBS)
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
        
        req_dict = ipp.ops.verify_get_jobs_request(request)
        printer_name = req_dict['printer-uri']
        if printer_name not in self.printers:
            raise ipp.errors.Attributes(
                "Invalid printer uri: %s" % printer_name,
                [request.attribute_groups[0].attributes[2]])

        # Each job will append a new job attribute group.
        jobs = [job.get_job_attributes(request) for job in \
                self.printers[printer_name].get_jobs()]
        response = ipp.ops.make_get_jobs_response(jobs, request)
        return response

    def print_uri(self, request):
        pass

    def create_job(self, request):
        pass

    def pause_printer(self, request):
        pass

    def resume_printer(self, request):
        pass

    @handler_for(const.Operations.GET_PRINTER_ATTRIBUTES)
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

        # this is just like cups_get_default, except the printer name
        # is given
        req_dict = ipp.ops.verify_get_printer_attributes_request(request)
        printer_name = req_dict['printer-uri']
        if printer_name not in self.printers:
            raise ipp.errors.Attributes(
                "Invalid printer uri: %s" % printer_name,
                [request.attribute_groups[0].attributes[2]])
        
        response = ipp.ops.make_get_printer_attributes_response(
            self.printers[printer_name].get_printer_attributes(request), request)
        return response

    def set_printer_attributes(self, request):
        pass

    ##### Job Commands

    def cancel_job(self, request):
        pass

    def send_document(self, request):
        pass

    def send_uri(self, request):
        pass

    def get_job_attributes(self, request):
        req_dict = ipp.ops.verify_get_jobs_request(request)
        printer_name = req_dict['printer-uri']
        job_id = req_dict['job-id']
        
        if printer_name not in self.printers:
            raise ipp.errors.Attributes(
                "Invalid printer uri: %s" % printer_name,
                [request.attribute_groups[0].attributes[2]])
        try:
            job = self.printers[printer_name].get_job(job_id)
        except InvalidJobException:
            raise ipp.errors.Attributes(
                "Invalid job id: %d" % job_id,
                [request.attribute_groups[0].attributes[2]]) # XXX: this is wrong

        # Each job will append a new job attribute group.
        # XXX: we need to honor the things that the request actually asks for
        response = ipp.ops.make_get_job_attributes_response(
            job.get_job_attributes(request), request)
        return response

    def set_job_attributes(self, request):
        pass

    def cups_get_document(self, request):
        pass

    def restart_job(self, request):
        pass

    def promote_job(self, request):
        pass

    ##### CUPS Specific Commands

    @handler_for(const.Operations.CUPS_GET_DEFAULT)
    def cups_get_default(self, request):
        """The CUPS-Get-Default operation (0x4001) returns the default
        printer URI and attributes.

        (Source: http://www.cups.org/documentation.php/spec-ipp.html#CUPS_GET_DEFAULT )

        """

        req_dict = ipp.ops.verify_cups_get_default_request(request)
        response = ipp.ops.make_get_printer_attributes_response(
            self.printers[self.default].get_printer_attributes(request), request)
        return response

    @handler_for(const.Operations.CUPS_GET_PRINTERS)
    def cups_get_printers(self, request):
        """The CUPS-Get-Printers operation (0x4002) returns the
        printer attributes for every printer known to the system. This
        may include printers that are not served directly by the
        server.

        (Source: http://www.cups.org/documentation.php/spec-ipp.html#CUPS_GET_PRINTERS )
            
        """

        req_dict = ipp.ops.verify_cups_get_printers_request(request)
        attrs = [self.printers[printer].get_printer_attributes(request) \
                 for printer in self.printers]
        response = ipp.ops.make_cups_get_printers_response(attrs, request)
        return response

    @handler_for(const.Operations.CUPS_GET_CLASSES)
    def cups_get_classes(self, request):
        """The CUPS-Get-Classes operation (0x4005) returns the printer
        attributes for every printer class known to the system. This
        may include printer classes that are not served directly by
        the server.
        
        (Source: http://www.cups.org/documentation.php/spec-ipp.html#CUPS_GET_CLASSES )

        """

        req_dict = ipp.ops.verify_cups_get_classes_request(request)
        response = ipp.ops.make_cups_get_classes_response(request)
        return response
