from gutenbach.server.requests import GutenbachRequestHandler
import BaseHTTPServer
import gutenbach.ipp as ipp
import logging
import sys
import traceback

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

        # Get the handler and pass it the request and response
        # objects.  It will fill in values for the response object or
        # throw a fatal error.
        logger.debug("Received request: %s" % repr(request))
        try:
            response = self.root.handle(request)
        except:
            logger.fatal(traceback.format_exc())
            sys.exit(1)

        # Send the response across HTTP
        logger.debug("Sending response: %s" % repr(response))
        try:
            binary = response.packed_value
        except:
            logger.fatal(traceback.format_exc())
            sys.exit(1)
            
        self.send_response(200, "Gutenbach IPP Response")
        self.send_header("Content-Type", "application/ipp")
        self.send_header("Connection", "close")
        self.end_headers()
        self.wfile.write(binary)
