from gutenbach.server.requests import GutenbachRequestHandler
import BaseHTTPServer
import gutenbach.ipp as ipp
import logging
import sys
import traceback

# initialize logger
logger = logging.getLogger(__name__)

# initialize handler
handler = GutenbachRequestHandler()

class GutenbachIPPServer(BaseHTTPServer.BaseHTTPRequestHandler):
    def do_POST(self):
        # Receive a request
        length = int(self.headers.getheader('content-length', 0))
        if length == 0:
            logger.warning("content-length == 0")
            return
        request = ipp.Request(request=self.rfile, length=length)

        # Get the handler and pass it the request and response
        # objects.  It will fill in values for the response object or
        # throw a fatal error.
        logger.debug("Received request: %s" % repr(request))
        try:
            response = handler.handle(request)
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
