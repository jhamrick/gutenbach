from . import InvalidJobException, InvalidPrinterStateException
from gutenbach.ipp import JobStates as States
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

    def __init__(self, job_id=-1, printer=None, creator=None, name=None, size=None):
	"""Create an empty Gutenbach job.

	"""

	self.printer = printer
        self.player = None

	self.id = job_id
        self.creator = creator
        self.name = name
        self.size = size
	self.status = States.HELD

        self.document = None
        self.document_name = None
        self.document_format = None
        self.document_natural_language = None
        self.compression = None
    
    def __repr__(self):
	return str(self)

    def __str__(self):
        return "<Job %d '%s'>" % (self.id, self.name)

    ######################################################################
    ###                          Properties                            ###
    ######################################################################

    @property
    def id(self):
        """Unique job identifier.  Should be a positive integer,
        except when unassigned, when it defaults to -1.
        
        """
        return self._id
    @id.setter
    def id(self, val):
        try:
            self._id = int(val)
        except TypeError:
            self._id = -1

    @property
    def creator(self):
        """The user who created the job; analogous to the IPP
        requesting-user-name.

        """
        return self._creator
    @creator.setter
    def creator(self, val):
        if val is None:
            self._creator = ""
        else:
            self._creator = str(val)

    @property
    def name(self):
        """The job's name.

        """
        return self._name
    @name.setter
    def name(self, val):
        if val is None:
            self._name = ""
        else:
            self._name = str(val)

    @property
    def size(self):
        """The size of the job in bytes.

        """
        if self.document:
            size = os.path.getsize(self.document.name)
        else:
            size = self._size
        return size
    @size.setter
    def size(self, val):
        try:
            self._size = int(val)
        except TypeError:
            self._size = 0

    ######################################################################
    ###                            Methods                             ###
    ######################################################################

    def play(self):
        logger.info("playing job %s" % str(self))
	self.status = States.PROCESSING
        self.player = subprocess.Popen(
            "/usr/bin/mplayer -really-quiet -slave %s" % self.document.name,
            shell=True,
            stderr=subprocess.PIPE,
            stdout=subprocess.PIPE)
        while self.player.poll() is None:
            time.sleep(0.1)
        logger.info("mplayer finished with code %d" % self.player.returncode)
        stderr = self.player.stderr.read()
        stdout = self.player.stdout.read()
        if stderr.strip() != "":
            logger.error(stderr)
        logger.debug(stdout)
        self.player = None
	self.printer.complete_job(self.id)

    def finish(self):
        logger.info("finished job %s" % str(self))
	self.status = States.COMPLETE

    ######################################################################
    ###                        IPP Attributes                          ###
    ######################################################################

    @property
    def job_id(self):
        return ipp.JobId(self.id)

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


    ######################################################################
    ###                        IPP Operations                          ###
    ######################################################################

    def cancel_job(self):
        pass

    def send_document(self,
                      document,
                      document_name=None,
                      document_format=None,
                      document_natural_language=None,
                      requesting_user_name=None,
                      compression=None,
                      last_document=None):

        if self.status != States.HELD:
            raise InvalidJobStateException(self.status)
        
        self.document = document
        self.document_name = str(document_name)
        self.document_format = str(document_format)
        self.document_natural_language = str(document_natural_language)
        self.creator = str(requesting_user_name)
        self.compression = str(compression)
        self.status = States.PENDING

        logger.debug("document for job %d is '%s'" % (self.id, self.document_name))

    def send_uri(self):
        pass

    def get_job_attributes(self, requested_attributes=None):
        if requested_attributes is None:
            requested = self.attributes
        else:
            requested = [a for a in self.attributes if a in requested_attributes]

        _attributes = [attr.replace("-", "_") for attr in requested]
        attributes = [getattr(self, attr) for attr in _attributes]
        return attributes

    def set_job_attributes(self):
        pass

    def restart_job(self):
        pass

    def promote_job(self):
        pass
