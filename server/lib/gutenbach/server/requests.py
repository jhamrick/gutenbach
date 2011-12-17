import BaseHTTPServer
import gutenbach.ipp
import gutenbach.ipp.constants as const
import logging
import time

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

class IPPRequestHandler(object):
    """A generic base class for IPP requests.  Provides a dispatch
    function to conver request operation ids to handler functions.

    """
    
    def _ipp_dispatch(self, request):
        for d in dir(self):
            if getattr(getattr(self, d), "ipp_operation", None) == request.operation_id:
                return getattr(self, d)
        return self.unknown_operation

    def unknown_operation(self, request, response):
        print "Received UNKNOWN OPERATION %x" % request.operation_id
        response.operation_id = const.StatusCodes.OPERATION_NOT_SUPPORTED

class PrinterRequestHandler(IPPRequestHandler):
    """This handles requests that are printer-specific: for example,
    the printer's name or state.

    """
    
    def __init__(self, name):
        self.name = name

    @handler_for(const.Operations.GET_PRINTER_ATTRIBUTES)
    def get_printer_attributes(self, request, response):
        printer_attributes = ipp.AttributeGroup(const.AttributeTags.PRINTER)
        printer_attributes.append(ipp.Attribute(
            "printer-uri-supported",
            [ipp.Value(ipp.Tags.URI, "ipp://localhost:8000/printers/" + self.name)]))

        printer_attributes.append(ipp.Attribute(
            "uri-authentication-supported",
            [ipp.Value(ipp.Tags.KEYWORD, "none")]))

        printer_attributes.append(ipp.Attribute(
            "uri-security-supported",
            [ipp.Value(ipp.Tags.KEYWORD, "none")]))

        printer_attributes.append(ipp.Attribute(
            "printer-name",
            [ipp.Value(ipp.Tags.NAME_WITHOUT_LANGUAGE, self.name)]))

        printer_attributes.append(ipp.Attribute(
            "printer-state",
            [ipp.Value(ipp.Tags.ENUM, const.PrinterStates.IDLE)]))

        printer_attributes.append(ipp.Attribute(
            "printer-state-reasons",
            [ipp.Value(ipp.Tags.KEYWORD, "none")]))

        printer_attributes.append(ipp.Attribute(
            "ipp-versions-supported",
            [ipp.Value(ipp.Tags.KEYWORD, "1.0"),
             ipp.Value(ipp.Tags.KEYWORD, "1.1")]))

        # XXX: We should query ourself for the supported operations
        printer_attributes.append(ipp.Attribute(
            "operations-supported",
            [ipp.Value(ipp.Tags.ENUM, const.Operations.GET_JOBS)]))

        printer_attributes.append(ipp.Attribute(
            "charset-configured",
            [ipp.Value(ipp.Tags.CHARSET, "utf-8")]))

        printer_attributes.append(ipp.Attribute(
            "charset-supported",
            [ipp.Value(ipp.Tags.CHARSET, "utf-8")]))

        printer_attributes.append(ipp.Attribute(
            "natural-language-configured",
            [ipp.Value(ipp.Tags.NATURAL_LANGUAGE, "en-us")]))

        printer_attributes.append(ipp.Attribute(
            "generated-natural-language-supported",
            [ipp.Value(ipp.Tags.NATURAL_LANGUAGE, "en-us")]))

        printer_attributes.append(ipp.Attribute(
            "document-format-default",
            [ipp.Value(ipp.Tags.MIME_MEDIA_TYPE, "application/octet-stream")]))

        printer_attributes.append(ipp.Attribute(
            "document-format-supported",
            [ipp.Value(ipp.Tags.MIME_MEDIA_TYPE, "application/octet-stream"),
             ipp.Value(ipp.Tags.MIME_MEDIA_TYPE, "audio/mp3")]))

        printer_attributes.append(ipp.Attribute(
            "printer-is-accepting-jobs",
            [ipp.Value(ipp.Tags.BOOLEAN, True)]))

        printer_attributes.append(ipp.Attribute(
            "queued-job-count",
            [ipp.Value(ipp.Tags.INTEGER, 1)]))

        printer_attributes.append(ipp.Attribute(
            "pdl-override-supported",
            [ipp.Value(ipp.Tags.KEYWORD, "not-attempted")]))

        printer_attributes.append(ipp.Attribute(
            "printer-up-time",
            [ipp.Value(ipp.Tags.INTEGER, int(time.time()))]))

        printer_attributes.append(ipp.Attribute(
            "compression-supported",
            [ipp.Value(ipp.Tags.KEYWORD, "none")]))

        response.attribute_groups.append(printer_attributes)
        response.operation_id = const.StatusCodes.OK
        print "get_printer_attributes called"

class RootRequestHandler(IPPRequestHandler):
    printers = [PrinterRequestHandler(name="sipbmp3")]

    @handler_for(const.Operations.CUPS_GET_DEFAULT)
    def cups_get_default(self, request, response):
        print "get_default called"
        return self.printers[0].get_printer_attributes(request, response)

    @handler_for(const.Operations.CUPS_GET_PRINTERS)
    def cups_get_printers(self, request, response):
        print "get_printers called"
        response.operation_id = const.StatusCodes.OK
        # Each printer will append a new printer attribute group.
        for p in self.printers:
            p.get_printer_attributes(request, response)

    @handler_for(const.Operations.CUPS_GET_CLASSES)
    def cups_get_classes(self, request, response):
        print "get_classes called"
        response.operation_id = const.StatusCodes.OK
        # We have no printer classes, so nothing to return.

class GutenbachIPPHandler(BaseHTTPServer.BaseHTTPRequestHandler):
    def setup(self):
        self.root = RootRequestHandler()
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
        handler = self.root._ipp_dispatch(request)
        handler(request, response)
        print "Sending response:", repr(response)

        # Send the response across HTTP
        self.send_response(200, "o hai")
        self.send_header("Content-Type", "application/ipp")
        self.send_header("Connection", "close")
        self.end_headers()
        self.wfile.write(response.packed_value)

    def get_jobs(self, request, response_kwargs):
        """get-jobs response"""

        # Job attributes
        job_attributes = [
            ipp.Attribute(
                'job-id',
                [ipp.Value(ipp.Tags.INTEGER, 12345)]),
            ipp.Attribute(
                'job-name',
                [ipp.Value(ipp.Tags.NAME_WITHOUT_LANGUAGE, 'foo')]),
            ipp.Attribute(
                'job-originating-user-name',
                [ipp.Value(ipp.Tags.NAME_WITHOUT_LANGUAGE, 'jhamrick')]),
            ipp.Attribute(
                'job-k-octets',
                [ipp.Value(ipp.Tags.INTEGER, 1)]),
            ipp.Attribute(
                'job-state',
                [ipp.Value(ipp.Tags.ENUM, const.JobStates.HELD)]),
            ipp.Attribute(
                'job-printer-uri',
                [ipp.Value(ipp.Tags.URI, 'ipp://localhost:8000/printers/foo')])
            ]
        # Job attribute group
        job_attribute_group = ipp.AttributeGroup(
            const.AttributeTags.JOB,
            job_attributes)

        # Operation attributions
        op_attributes = [
            ipp.Attribute(
                'attributes-charset',
                [ipp.Value(ipp.Tags.CHARSET, 'utf-8')]),
            ipp.Attribute(
                'attributes-natural-language',
                [ipp.Value(ipp.Tags.NATURAL_LANGUAGE, 'en-us')])
            ]
        # Operation attribution group
        op_attributes_group = ipp.AttributeGroup(
            const.AttributeTags.OPERATION,
            op_attributes)

        # Setup the actual response dictionary
        response_kwargs['attribute_groups'] = [op_attributes_group,job_attribute_group]
        response_kwargs['operation_id'] = const.StatusCodes.OK

        return response_kwargs

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
