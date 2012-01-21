import errors
from errors import *
__all__ = ['errors']
__all__.extend(errors.__all__)

def sync(func):
    """Lock decorator

    Holds a lock (self.lock) for the durration of a method call.
    """

    def do(self, *args, **kwargs):
        with self.lock:
            return func(self, *args, **kwargs)

    return do
__all__.append('sync')


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
import os
import shutil

# configure and initialize logging
logger = None

def error(self, request=None, client_address=None):
    logger.fatal(traceback.format_exc())
    self.gutenbach_printer.running = False
    sys.exit(1)

def new_logfile(logfile):
    if os.path.exists(logfile):
        pth = os.path.abspath(os.path.dirname(logfile))
        filename = os.path.basename(logfile)
        logfiles = [f for f in os.listdir(pth) if f.startswith(filename + ".")]
        lognums = [0]
        for f in logfiles:
            try:
                lognums.append(int(f.lstrip(filename + ".")))
            except TypeError:
                pass
        nextnum = max(lognums) + 1
        shutil.move(logfile, os.path.join(pth, "%s.%d" % (filename, nextnum)))

def start(config):
    global logger
    logkwargs = {}
    logkwargs['level'] = getattr(logging, config['loglevel'].upper())
    if 'logfile' in config:
        logkwargs['filename'] = config['logfile']
        new_logfile(config['logfile'])            
    logging.basicConfig(**logkwargs)
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
