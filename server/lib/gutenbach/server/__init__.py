from server import GutenbachIPPServer
import BaseHTTPServer
import logging
import sys

# configure logging
logging.basicConfig(level=logging.DEBUG)

def error(self, request, client_address):
    sys.exit(1)

def start():
    server_address = ('', 8000)
    httpd = BaseHTTPServer.HTTPServer(server_address, GutenbachIPPServer)
    httpd.handle_error = error.__get__(httpd)
    httpd.serve_forever()

if __name__ == "__main__":
    start()
