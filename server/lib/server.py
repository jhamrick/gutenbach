#!/usr/bin/python

import logging, BaseHTTPServer
import ipp
import ipp.constants as const

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
        request = ipp.Request(request=self.rfile,
                              length=length)
        print "Received request:", repr(request)

        response_kwargs = {}
        response_kwargs['version'] = request.version
        response_kwargs['request_id'] = request.request_id
        response_kwargs = self.get_jobs(request, response_kwargs)
        response = ipp.Request(**response_kwargs)
        print "Sending response:", repr(response)

        self.send_response(200, "o hai")
        self.send_header("Content-Type", "application/ipp")
        self.send_header("Connection", "close")
        self.end_headers()
        self.wfile.write(response.packed_value)

    def get_jobs(self, request, response_kwargs):
        """get-jobs response"""

        job_attributes = [ipp.Attribute('job-id',
                                       [ipp.Value(ipp.Tags.INTEGER,
                                                 12345,
                                                 )]),
                          ipp.Attribute('job-name',
                                       [ipp.Value(ipp.Tags.NAME_WITHOUT_LANGUAGE,
                                                 'foo',
                                                 )]),
                          ipp.Attribute('job-originating-user-name',
                                       [ipp.Value(ipp.Tags.NAME_WITHOUT_LANGUAGE,
                                                 'jhamrick',
                                                 )]),
                          ipp.Attribute('job-k-octets',
                                       [ipp.Value(ipp.Tags.INTEGER,
                                                 1,
                                                 )]),
                          ipp.Attribute('job-state',
                                       [ipp.Value(ipp.Tags.ENUM,
                                                 const.JobStates.HELD,
                                                 )]),
                          ipp.Attribute('job-printer-uri',
                                       [ipp.Value(ipp.Tags.URI,
                                                 'http://localhost:8000/printers/foo',
                                                 )])]


        #req_op_attributes = request.getAttributeGroup(ipp.Tags.OPERATION_ATTRIBUTES_TAG)
        #print req_op_attributes
        #printer_uri = req_op_attributes[0].getAttribute('printer-uri')

        op_attributes = [ipp.Attribute('attributes-charset',
                                      [ipp.Value(ipp.Tags.CHARSET,
                                                'utf-8',
                                                )]),
                         ipp.Attribute('attributes-natural-language',
                                      [ipp.Value(ipp.Tags.NATURAL_LANGUAGE,
                                                'en-us',
                                                )])]
        
        job_attribute_group = ipp.AttributeGroup(const.AttributeTags.JOB,
                                                 job_attributes)
        op_attributes_group = ipp.AttributeGroup(const.AttributeTags.OPERATION,
                                                 op_attributes)
        response_kwargs['attribute_groups'] = [op_attributes_group,job_attribute_group]
        response_kwargs['operation_id'] = const.StatusCodes.OK

        return response_kwargs

    ##### Printer Commands

    def print_job(self, request):
        pass

    def validate_job(self, request):
        pass

    def get_printer_attributes(self, request):
        pass

    #def get_jobs(self, request):
    #    pass

    def print_uri(self, request):
        pass

    def create_job(self, request):
        pass

    def cups_get_default(self, request):
        pass

    def cups_get_printers(self, request):
        pass

    def pause_printer(self, request):
        pass

    def resume_printer(self, request):
        pass

    def set_printer_attributes(self, request):
        pass

    ##### Job Commands

    def cancel_job(self, request):
        pass

    def get_job_attributes(self, request):
        pass

    def send_document(self, request):
        pass

    def send_uri(self, request):
        pass

    def set_job_attributes(self, request):
        pass

    def cups_get_document(self, request):
        pass

    def restart_job(self, request):
        pass

    def promote_job(self, request):
        pass

if __name__ == '__main__':
    server_address = ('', 8000)
    httpd = BaseHTTPServer.HTTPServer(server_address, GutenbachIPPHandler)
    httpd.serve_forever()
