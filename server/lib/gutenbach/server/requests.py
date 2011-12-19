import BaseHTTPServer
import gutenbach.ipp as ipp
import gutenbach.ipp.constants as const
from gutenbach.server.printer import GutenbachPrinter
from gutenbach.server.exceptions import MalformedIPPRequestException
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
    
    def handle(self, request, response):
        # look up the handler
        handler = None
        for d in dir(self):
            if getattr(getattr(self, d), "ipp_operation", None) == request.operation_id:
                handler = getattr(self, d)
                break
        # we couldn't find a handler, so default to unknown operation
        if handler is None:
            handler = self.unknown_operation
        # call the handler
        handler(request, response)

    def unknown_operation(self, request, response):
        print "Received unknown operation %x" % request.operation_id
        response.operation_id = const.StatusCodes.OPERATION_NOT_SUPPORTED

    def _get_printer_attributes(self, printer, request, response):
        response.attribute_groups.append(ipp.AttributeGroup(
            const.AttributeTags.PRINTER,
            printer.get_printer_attributes(request)))

    def _get_job_attributes(self, job_id, printer, request, response):
        response.attribute_groups.append(ipp.AttributeGroup(
            const.AttributeTags.JOB,
            job.get_job_attributes(request)))

    def _get_printer_name(self, request):
        # make sure the first group is an OPERATION group
        group_tag = request.attribute_groups[0].tag
        if group_tag != const.AttributeTags.OPERATION:
            raise MalformedIPPRequestException, \
                  "Expected OPERATION group tag, got %d\n", group_tag

        # make sure the printer-uri value is appropriate
        printername_attr = request.attribute_groups[0]['printer-uri']
        printername_value_tag = printername_attr.values[0].value_tag
        if printername_value_tag != const.CharacterStringTags.URI:
            raise MalformedIPPRequestException, \
                  "Expected URI value tag, got %s" % printername_value_tag

        # actually get the printer name
        printername_value = printername_attr.values[0].value
        # XXX: hack -- CUPS will strip the port from the request, so
        # we can't do an exact comparison (also the hostname might be
        # different, depending on the CNAME or whether it's localhost)
        printername = printername_value.split("/")[-1]

        # make sure the printername is valid
        if printername not in self.printers:
            raise ValueError, "Invalid printer uri: %s" % printername_value

        return printername

    @handler_for(const.Operations.CUPS_GET_DEFAULT)
    def cups_get_default(self, request, response):
        print "get_default called"
        self._get_printer_attributes(self.printers[self.default], request, response)
        response.operation_id = const.StatusCodes.OK

    @handler_for(const.Operations.GET_PRINTER_ATTRIBUTES)
    def get_printer_attributes(self, request, response):
        print "get_printer_attributes called"

        # this is just like cups_get_default, except the printer name
        # is given
        printername = self._get_printer_name(request)
        self._get_printer_attributes(self.printers[printername], request, response)
        response.operation_id = const.StatusCodes.OK

    @handler_for(const.Operations.CUPS_GET_PRINTERS)
    def cups_get_printers(self, request, response):
        print "get_printers called"
        
        # Each printer will append a new printer attribute group.
        for printer in self.printers:
            self._get_printer_attributes(self.printers[printer], request, response)
        response.operation_id = const.StatusCodes.OK

    @handler_for(const.Operations.CUPS_GET_CLASSES)
    def cups_get_classes(self, request, response):
        print "get_classes called"
        response.operation_id = const.StatusCodes.OK
        # We have no printer classes, so nothing to return.

    @handler_for(const.Operations.GET_JOBS)
    def get_jobs(self, request, response):
        print "get_jobs called"

        printername = self._get_printer_name(request)
        # Each job will append a new job attribute group.
        for job in self.printers[printername].get_jobs():
            self._get_job_attributes(job, request, response)
        response.operation_id = const.StatusCodes.OK

class GutenbachIPPServer(BaseHTTPServer.BaseHTTPRequestHandler):
    def setup(self):
        self.root = GutenbachRequestHandler()
        BaseHTTPServer.BaseHTTPRequestHandler.setup(self)

    def handle_one_request(self):
        self.raw_requestline = self.rfile.readline()
        if not self.raw_requestline:
            self.close_connection = 1
            return
        if not self.parse_request(): # An error code has been sent, just exit
            return
        self.handle_ipp()

    def handle_ipp(self):
        # Receive a request
        length = int(self.headers.getheader('content-length', 0))
        request = ipp.Request(request=self.rfile, length=length)
        print "Received request:", repr(request)

        # Attributes
        attributes = [
            ipp.Attribute(
                'attributes-charset',
                [ipp.Value(ipp.Tags.CHARSET, 'utf-8')]),
            ipp.Attribute(
                'attributes-natural-language',
                [ipp.Value(ipp.Tags.NATURAL_LANGUAGE, 'en-us')])
            ]
        # Attribute group
        attribute_group = ipp.AttributeGroup(
            const.AttributeTags.OPERATION,
            attributes)

        # Set up the response
        response_kwargs = {}
        response_kwargs['version']          = request.version
        response_kwargs['operation_id']     = const.StatusCodes.INTERNAL_ERROR
        response_kwargs['request_id']       = request.request_id
        response_kwargs['attribute_groups'] = [attribute_group]
        response = ipp.Request(**response_kwargs)

        # Get the handler and pass it the request and response objects
        self.root.handle(request, response)
        print "Sending response:", repr(response)

        # Send the response across HTTP
        self.send_response(200, "o hai")
        self.send_header("Content-Type", "application/ipp")
        self.send_header("Connection", "close")
        self.end_headers()
        self.wfile.write(response.packed_value)

    ##### Printer Commands

    def print_job(self, request):
        pass

    def validate_job(self, request):
        pass

    #def get_jobs(self, request):
    #    pass

    def print_uri(self, request):
        pass

    def create_job(self, request):
        pass

    def pause_printer(self, request):
        pass

    def resume_printer(self, request):
        pass

    def set_printer_attributes(self, request):
        pass

    ##### Job Commands

    def cancel_job(self, request):
        pass

    def get_job_attributes(self, request):
        pass

    def send_document(self, request):
        pass

    def send_uri(self, request):
        pass

    def set_job_attributes(self, request):
        pass

    def cups_get_document(self, request):
        pass

    def restart_job(self, request):
        pass

    def promote_job(self, request):
        pass
