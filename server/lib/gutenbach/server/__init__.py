import errors
from errors import *
__all__ = ['errors']
__all__.extend(errors.__all__)

from job import GutenbachJob
__all__.append('GutenbachJob')

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
logger = None

def error(self, request=None, client_address=None):
    logger.fatal(traceback.format_exc())
    self.gutenbach_printer.running = False
    sys.exit(1)

def start(config):
    global logger
    loglevel_num = getattr(logging, config['loglevel'].upper())
    logging.basicConfig(level=loglevel_num)
    logger = logging.getLogger(__name__)    
    logger.info("Starting Gutenbach server...")
    printers = sorted(config['printers'].keys())
    gutenbach = GutenbachPrinter(printers[0], config['printers'][printers[0]])
    gutenbach.start()

    logger.info("Starting IPP server...")
    server_address = ('', config['port'])
    httpd = BaseHTTPServer.HTTPServer(server_address, IPPServer)
    httpd.handle_error = error.__get__(httpd)
    httpd.gutenbach_printer = gutenbach
    while gutenbach.isAlive():
        try:
            httpd.handle_request()
        except:
            error(httpd)

__all__.append('start')
