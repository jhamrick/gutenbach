#!/usr/bin/python

import logging, BaseHTTPServer
from ipprequest import *
import ippconstants as const

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
        length = int(self.headers.getheader('content-length', 0))
        request = IPPRequest(request=self.rfile,
                             length=length)

        response_kwargs = {}
        response_kwargs['version'] = request.version
        response_kwargs['request_id'] = request.request_id
        response_kwargs = self.get_jobs(request, response_kwargs)
        response = IPPRequest(**response_kwargs)

        self.send_response(200, "o hai")
        self.send_header("Content-Type", "application/ipp")
        self.send_header("Connection", "close")
        self.end_headers()
        self.wfile.write(response.toBinaryData())

    def get_jobs(self, request, response_kwargs):
        """get-jobs response"""

        job_attributes = [IPPAttribute('job-id',
                                       [IPPValue(IPPTags.INTEGER,
                                                 12345,
                                                 unpack=False)]),
                          IPPAttribute('job-name',
                                       [IPPValue(IPPTags.NAME_WITHOUT_LANGUAGE,
                                                 'foo',
                                                 unpack=False)]),
                          IPPAttribute('job-originating-user-name',
                                       [IPPValue(IPPTags.NAME_WITHOUT_LANGUAGE,
                                                 'jhamrick',
                                                 unpack=False)]),
                          IPPAttribute('job-k-octets',
                                       [IPPValue(IPPTags.INTEGER,
                                                 1,
                                                 unpack=False)]),
                          IPPAttribute('job-state',
                                       [IPPValue(IPPTags.ENUM,
                                                 const.IPP_JOB_HELD,
                                                 unpack=False)]),
                          IPPAttribute('job-printer-uri',
                                       [IPPValue(IPPTags.URI,
                                                 'http://localhost:8000/printers/foo',
                                                 unpack=False)])]


        #req_op_attributes = request.getAttributeGroup(IPPTags.OPERATION_ATTRIBUTES_TAG)
        #print req_op_attributes
        #printer_uri = req_op_attributes[0].getAttribute('printer-uri')

        op_attributes = [IPPAttribute('attributes-charset',
                                      [IPPValue(IPPTags.CHARSET,
                                                'utf-8',
                                                unpack=False)]),
                         IPPAttribute('attributes-natural-language',
                                      [IPPValue(IPPTags.NATURAL_LANGUAGE,
                                                'en-us',
                                                unpack=False)])]
        
        job_attribute_group = IPPAttributeGroup(IPPTags.JOB_ATTRIBUTES_TAG,
                                                job_attributes)
        op_attributes_group = IPPAttributeGroup(IPPTags.OPERATION_ATTRIBUTES_TAG,
                                                op_attributes)
        response_kwargs['attribute_groups'] = [op_attributes_group,job_attribute_group]
        response_kwargs['operation_id'] = const.IPP_OK

        return response_kwargs

if __name__ == '__main__':
    server_address = ('', 8000)
    httpd = BaseHTTPServer.HTTPServer(server_address, GutenbachIPPHandler)
    httpd.serve_forever()
