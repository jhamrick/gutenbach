from server import GutenbachIPPServer
import BaseHTTPServer
import logging
import sys
import traceback

# configure logging
logging.basicConfig(level=logging.DEBUG)

# initialize logger
logger = logging.getLogger(__name__)

def error(self, request, client_address):
    logger.fatal(traceback.format_exc())
    sys.exit(1)

def start():
    server_address = ('', 8000)
    httpd = BaseHTTPServer.HTTPServer(server_address, GutenbachIPPServer)
    httpd.handle_error = error.__get__(httpd)
    httpd.serve_forever()

if __name__ == "__main__":
    start()
