#!/usr/bin/python

import logging, BaseHTTPServer
import ipprequest

logging.basicConfig(level=logging.DEBUG)

class GutenbachIPPHandler(BaseHTTPServer.BaseHTTPRequestHandler):
    def handle_one_request(self):
        self.raw_requestline = self.rfile.readline()
        if not self.raw_requestline:
            self.close_connection = 1
            return
        if not self.parse_request(): # An error code has been sent, just exit
            return
        self.handle_ipp()

    def handle_ipp(self):
        req = ipprequest.IPPRequest(request=self.rfile,
                                    length=self.headers.getheader('content-length', 0))

        self.send_response(200, "o hai")
        self.send_header("Content-Type", "text/plain")
        self.send_header("Connection", "close")
        self.end_headers()
        self.wfile.write("I got ur request")

if __name__ == '__main__':
    server_address = ('', 8000)
    httpd = BaseHTTPServer.HTTPServer(server_address, GutenbachIPPHandler)
    httpd.serve_forever()
