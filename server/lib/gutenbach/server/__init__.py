from requests import GutenbachIPPHandler
import BaseHTTPServer
import logging

# configure logging
logging.basicConfig(level=logging.DEBUG)

def start():
    server_address = ('', 8000)
    httpd = BaseHTTPServer.HTTPServer(server_address, GutenbachIPPHandler)
    httpd.serve_forever()

if __name__ == "__main__":
    start()
