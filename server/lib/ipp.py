#!/usr/bin/env python

# Adapted from the Quickprint IPP server code (http://quikprint.mit.edu)
# Modifications and additions written by Jessica Hamrick (jhamrick@mit.edu)

# Notes and Todo:
#   - make sure package creates gutenbach folder in /var/log

import os, sys
import cgi, cgitb
import logging
import MySQLdb
import ipplib

from ipplib import IPPRequest
from tempfile import mkstemp
from shutil import move
from logging import debug, info, warning, error, critical

# set up logging
LOGFILE = "/var/log/gutenbach/ipp.log"
logging.basicConfig(filename=LOGFILE, level=logging.DEBUG)
cgitb.enable(logdir='/var/log/gutenbach/cgi.log')

# make sure a temporary folder exists
TEMPDIR = '/tmp/gutenbach/ipp'
try:
    if not os.path.exists(TEMPDIR):
        info("Creating temporay directory '%s'" % TEMPDIR)
        os.makedirs(TEMPDIR)
except e, Exception:
    error("Could not create temporary directory '%s'" % TEMPDIR)

# print the content type for our request
print "Content-type: application/ipp\n"

class IPPServer(object):
    
    # nothing to do in the init
    def __init__(self):
        pass

    # this function processes an IPP request and sends a response
    def process(self, request_in, response_out):


        response = IPPRequest(version=request.version,
                              operation_id=request.operation_id,
                              request_id=request.request_id)
        #file('/mit/gutenbach/tmp/requests/'+str(request.operation_id)).write()
        handler = getattr(self, "_operation_%d" % request.operation_id, None)

        response._operation_attributes = [[]]
        response._operation_attributes[0] = filter( \
            lambda x: x[0] in ('attributes-charset', 'attributes-natural-language', 'printer-uri'),
            request._operation_attributes[0])

        # f = file('/tmp/gutenbach/ipp/printer2.log','a')
        # f.write("\n" + "*"*80 + "\n")
        # f.write(str(request))
        if handler is not None:
            response.setOperationId(handler(request, response))
            data_out = response.dump()
            response_out.write(data_out)
            response_test = IPPRequest(data=data_out)
            response_test.parse()
        #     f.write("\n" + "-"*80 + "\n")
        #     f.write(str(response_test))
        # f.write("\n" + "*"*80 + "\n")
        # f.close()

    def _operation_2(self, request, response):
        """print-job response"""
        (fno, fname) = mkstemp(dir='/tmp/gutenbach/ipp')
        os.write(fno, request.data)
        os.close(fno)
        opattr = filter(lambda x: x[0] in ('job-name'),
            request._operation_attributes[0])
        jname = 'unknown'
        if len(opattr) and opattr[0][0] == 'job-name':
            jname = opattr[0][1][0][1]
        jstat = os.stat(fname)
        jsize = jstat.st_size
        c = db.cursor()
        c.execute("INSERT INTO job (juser, jname, jfile, jsize, jtype) VALUES (%s, %s, %s, %s, %s)", \
                (AUTH, jname, fname, jsize, 'PostScript',))
        jid = db.insert_id()
        jfile = '/mit/gutenbach/jobs/' + AUTH + '_' + str(jid)
        move(fname, jfile)
        c.execute("UPDATE job SET jfile=%s, dupdated=NOW() WHERE jid=%s", \
                (jfile, str(jid),))
        response._job_attributes = [[ \
            ('job-id', [('integer', jid)]), \
            ('printer-uri', [('uri', printer_uri)]), \
            ('job-state', [('enum', ipplib.IPP_JOB_HELD)])]]
        return ipplib.IPP_OK

    def _operation_8(self, request, response):
        """delete-job response"""
        opattr = filter(lambda x: x[0] in ('job-id'),
            request._operation_attributes[0])
        if len(opattr) and opattr[0][0] == 'job-id':
            jid = opattr[0][1][0][1]
            c = db.cursor()
            c.execute("UPDATE job SET jstate = 'DEL' WHERE juser = %s AND jid = %s", \
                (AUTH, int(jid)))
        return ipplib.IPP_OK

    def _operation_9(self, request, response):
        """get-job-properties response"""
        opattr = filter(lambda x: x[0] in ('job-id'),
            request._operation_attributes[0])
        if len(opattr) and opattr[0][0] == 'job-id':
            jid = opattr[0][1][0][1]
        response._job_attributes.append([ \
            ('job-id', [('integer', jid)]), \
        #    ('job-name', [('nameWithoutLanguage', x[1])]), \
            ('job-originating-user-name', [('nameWithoutLanguage', AUTH)]), \
        #    ('job-k-octets', [('integer', x[2]/1024)]), \
            ('job-state', [('enum', ipplib.IPP_JOB_COMPLETE)])
        ])
        return ipplib.IPP_OK

    def _operation_10(self, request, response):
        """get-jobs response"""
        c = db.cursor()
        c.execute("SELECT jid, jname, jsize, jstate FROM job WHERE juser = %s AND jstate != %s ORDER BY dadded", \
            (AUTH, 'DEL',))
        response._job_attributes = []
        for x in c.fetchall():
            if x[3] == 'NEW':
                state = ipplib.IPP_JOB_HELD
            elif x[3] == 'DONE':
                state = ipplib.IPP_JOB_COMPLETE
            else:
                state = 0
            response._job_attributes.append([ \
                ('job-id', [('integer', x[0])]), \
                ('job-name', [('nameWithoutLanguage', x[1])]), \
                ('job-originating-user-name', [('nameWithoutLanguage', AUTH)]), \
                ('job-k-octets', [('integer', x[2]/1024)]), \
                ('job-state', [('enum', state)])
            ])
        return ipplib.IPP_OK

    def _operation_11(self, request, response):
        """get-printer-attributes response"""
        response._printer_attributes = \
            [[('printer-name', [('nameWithoutLanguage', 'Gutenbach')])]]
        return ipplib.IPP_OK

IPPServer().process(sys.stdin,sys.stdout)
