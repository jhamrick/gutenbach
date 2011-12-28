from . import InvalidJobException, InvalidPrinterStateException
import os
import gutenbach.ipp as ipp
import logging
import subprocess
import time

# initialize logger
logger = logging.getLogger(__name__)

class Job(object):

    # for IPP
    attributes = [
        "job-id",
        "job-name",
        "job-originating-user-name",
        "job-k-octets",
        "job-state",
        "job-printer-uri"
    ]

    def __init__(self, jid, printer, creator="", name="", size=0):
	"""Initialize a Gutenbach job.

	This sets the status to 'initializing' and optionally sets the
	document to print to the value of document.

	"""

	self.jid      = jid
	self.printer  = printer

        self.creator  = creator
        self.name     = name
        self.size     = size

        self.document = None
        self.document_name = None
        self.player = None

	self.status   = ipp.JobStates.HELD

    def __getattr__(self, attr):
        try:
            return self.__getattribute__(attr)
        except AttributeError:
            pass
        return self.__getattribute__(attr.replace("-", "_"))

    def __hasattr__(self, attr):
        try:
            getattr(self, attr)
            return True
        except AttributeError:
            return False

    #### Job attributes

    @property
    def job_id(self):
        return ipp.JobId(self.jid)

    @property
    def job_name(self):
        return ipp.JobName(self.name)

    # XXX: we need to actually calculate this!
    @property
    def job_originating_user_name(self):
        return ipp.JobOriginatingUserName(self.creator)

    # XXX: we need to actually calculate this!
    @property
    def job_k_octets(self):
        return ipp.JobKOctets(self.size)

    @property
    def job_state(self):
        return ipp.JobState(self.status)

    @property
    def job_printer_uri(self):
        return ipp.JobPrinterUri(self.printer.uri)

    def get_job_attributes(self, request=None):
        if request and 'requested-attributes' in request:
            requested = []
            for value in request['requested-attributes'].values:
                if value.value in self.attributes:
                    requested.append(value.value)
        else:
            requested = self.attributes
            
        attributes = [getattr(self, attr) for attr in requested]
        return attributes
    
    #######

    def play(self):
        logger.info("playing job %s" % str(self))
	# TODO: add external call to music player
	self.status = ipp.JobStates.PROCESSING
        self.player = subprocess.Popen(
            "/usr/bin/mplayer -quiet %s" % self.document.name,
            shell=True)
            #stderr=subprocess.PIPE,
            #stdout=subprocess.PIPE)
        while self.player.poll() is None:
            time.sleep(0.1)
        logger.info("mplayer finished with code %d" % self.player.returncode)
        #if self.player.returncode < 0:
        #    logger.error(self.player.stderr)
        #logger.debug(self.player.stdout)
        self.player = None
	self.printer.complete_job(self.jid)

    def finish(self):
        logger.info("finished job %s" % str(self))
	self.status = ipp.JobStates.COMPLETE

    def __repr__(self):
	return str(self)

    def __str__(self):
        return "<Job %d '%s'>" % (self.jid if self.jid is not None else -1, self.name)
