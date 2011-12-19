import logging
import BaseHTTPServer
import traceback
from gutenbach.server.requests import GutenbachRequestHandler
import gutenbach.ipp as ipp
import gutenbach.ipp.constants as const

# initialize logger
logger = logging.getLogger(__name__)

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
        logger.debug("Received request: %s" % repr(request))

        # Operation attributes -- typically the same for any request
        attributes = [
            ipp.Attribute(
                'attributes-charset',
                [ipp.Value(ipp.Tags.CHARSET, 'utf-8')]),
            ipp.Attribute(
                'attributes-natural-language',
                [ipp.Value(ipp.Tags.NATURAL_LANGUAGE, 'en-us')])
            ]
        # Put the operation attributes in a group
        attribute_group = ipp.AttributeGroup(
            const.AttributeTags.OPERATION,
            attributes)

        # Set up the default response -- handlers will override these
        # values if they need to
        response_kwargs = {}
        response_kwargs['version']          = request.version
        response_kwargs['operation_id']     = const.StatusCodes.OK
        response_kwargs['request_id']       = request.request_id
        response_kwargs['attribute_groups'] = [attribute_group]
        response = ipp.Request(**response_kwargs)

        # Get the handler and pass it the request and response objects
        try:
            self.root.handle(request, response)
        except:
            response_kwargs['operation_id'] = const.StatusCodes.INTERNAL_ERROR
            logger.error(traceback.format_exc())

        # Send the response across HTTP
        logger.debug("Sending response: %s" % repr(response))
        self.send_response(200, "Gutenbach IPP Response")
        self.send_header("Content-Type", "application/ipp")
        self.send_header("Connection", "close")
        self.end_headers()
        self.wfile.write(response.packed_value)
