from requests import GutenbachIPPServer
import BaseHTTPServer
import logging

# configure logging
logging.basicConfig(level=logging.DEBUG)

def start():
    server_address = ('', 8000)
    httpd = BaseHTTPServer.HTTPServer(server_address, GutenbachIPPServer)
    httpd.serve_forever()

if __name__ == "__main__":
    start()
