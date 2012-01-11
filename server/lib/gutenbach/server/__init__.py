import errors
from errors import *
__all__ = ['errors']
__all__.extend(errors.__all__)

from job import Job
__all__.append('Job')

from printer import GutenbachPrinter
__all__.append('GutenbachPrinter')

from requests import make_empty_response, GutenbachRequestHandler
__all__.append('make_empty_response')
__all__.append('GutenbachRequestHandler')

from server import IPPServer
__all__.append('IPPServer')

import BaseHTTPServer
import logging
import sys
import traceback

# configure and initialize logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def error(self, request=None, client_address=None):
    logger.fatal(traceback.format_exc())
    self.gutenbach_printer.running = False
    sys.exit(1)

def start():
    logger.info("Starting Gutenbach server...")
    gutenbach = GutenbachPrinter("test")
    gutenbach.start()

    logger.info("Starting IPP server...")
    server_address = ('', 8000)
    httpd = BaseHTTPServer.HTTPServer(server_address, IPPServer)
    httpd.handle_error = error.__get__(httpd)
    httpd.gutenbach_printer = gutenbach
    while gutenbach.isAlive():
        try:
            httpd.handle_request()
        except:
            error(httpd)

__all__.append('start')
