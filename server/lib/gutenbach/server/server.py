import gutenbach.ipp as ipp

from . import InvalidPrinterStateException, InvalidJobException
from . import GutenbachPrinter
from . import GutenbachRequestHandler

import BaseHTTPServer
import logging
import sys
import traceback
import tempfile
import threading
import time

# initialize logger
logger = logging.getLogger(__name__)

class GutenbachServer(threading.Thread):

    def run(self):
        self.printer = GutenbachPrinter(name="test")
        self.request_stop = False

        while not self.request_stop:
            job = self.printer.next_job
            if job is not None:
                try:
                    self.printer.start_job(job)
                except InvalidPrinterStateException:
                    pass
                except:
                    logger.fatal(traceback.format_exc())
                    sys.exit(1)
            time.sleep(0.1)

class IPPServer(BaseHTTPServer.BaseHTTPRequestHandler):
    
    def send_continue(self):
        self.send_response(100, "continue")
        self.send_header("Content-Type", "application/ipp")
        self.end_headers()

    def send_ok(self, response):
        logger.debug(repr(response))
        binary, data_file = response.packed_value
            
        self.send_response(200, "ok")
        self.send_header("Content-Type", "application/ipp")
        self.send_header("Connection", "close")
        self.end_headers()
        
        self.wfile.write(binary)
        if data_file is not None:
            data = data_file.read(1024)
            while data != '':
                self.wfile.write(data)
                data = data_file.read(1024)

    def log_request(self, code=0, size=0):
        logger.info("response (%s)" % code)

    def log_message(self, fmt, *args):
        logger.info(fmt % args)

    def read_chunks(self):
        size = sys.maxint
        totalsize = 0

        with tempfile.SpooledTemporaryFile() as tmp:
            while size > 0:
                a, b = self.rfile.read(2)
                size = a + b
                while not (a == "\r" and b == "\n"):
                    a = b
                    b = self.rfile.read(1)
                    size += b
                size = int(size[:-2], base=16)
                totalsize += size
                chunk = self.rfile.read(size)
                clrf = self.rfile.read(2)
                assert clrf == "\r\n"
                tmp.write(chunk)

            tmp.seek(0)
            request = ipp.Request(request=tmp, length=totalsize)

        return request
                
    def do_POST(self):
        length = int(self.headers.getheader('content-length', 0))
        expect = self.headers.getheader('expect', None)
        encoding = self.headers.getheader('transfer-encoding', None)

        logger.info("request %s (%d bytes)" % (self.command, length))
        logger.debug(str(self.headers))

        # Parse the request
        if length == 0 and encoding == "chunked":
            request = self.read_chunks()
        else:
            request = ipp.Request(request=self.rfile, length=length)

        # Get the handler and pass it the request and response
        # objects.  It will fill in values for the response object or
        # throw a fatal error.
        logger.debug("request: %s" % repr(request))
        response = GutenbachRequestHandler(self.server.gutenbach_server).handle(request)
        self.send_ok(response)
