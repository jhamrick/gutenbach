from . import InvalidJobStateException, MissingDataException
from .player import Player
from gutenbach.ipp import JobStates as States
import os
import gutenbach.ipp as ipp
import logging

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
	self.state = States.HELD
        self.priority = 1

        self.document_name = None
        self.document_format = None
        self.document_natural_language = None
        self.compression = None
    
    def __repr__(self):
	return str(self)

    def __str__(self):
        return "<Job %d '%s'>" % (self.id, self.name)

    def __cmp__(self, other):
        return cmp(self.priority, other.priority)

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
        return self._size
    @size.setter
    def size(self, val):
        try:
            self._size = int(val)
        except TypeError:
            self._size = 0

    @property
    def is_playing(self):
        return self.state == States.PROCESSING

    @property
    def is_ready(self):
        return self.state == States.PENDING

    @property
    def is_finished(self):
        return self.state != States.PENDING and self.state != States.PROCESSING
        
    ######################################################################
    ###                            Methods                             ###
    ######################################################################

    def play(self):
        """Non-blocking play function.

        """
        
        # make sure the job is waiting to be played and that it's
        # valid
        if self.state != States.PENDING:
            raise InvalidJobStateException(self.state)
        
        # and set the state to processing if we're good to go
        logger.info("playing job %s" % str(self))
	self.state = States.PROCESSING
        self.player.callback = self._completed
        self.player.run()

    def pause(self):
        if self.player:
            self.player.mplayer_pause()

    def stop(self):
        if self.player:
            self.player.callback = self._stopped
            self.player.mplayer_stop()

    def _completed(self):
        if self.state != States.PROCESSING:
            raise InvalidJobStateException(self.state)
        logger.info("completed job %s" % str(self))
	self.state = States.COMPLETE
        self.player = None

    def _canceled(self):
        if self.state != States.PROCESSING:
            raise InvalidJobStateException(self.state)
        logger.info("canceled job %s" % str(self))
        self.state = States.CANCELLED
        self.player = None

    def _stopped(self):
        if self.state != States.PROCESSING:
            raise InvalidJobStateException(self.state)
        logger.info("stopped job %s" % str(self))
        self.state = States.STOPPED
        self.player = None

    def _aborted(self):
        if self.state != States.PROCESSING:
            raise InvalidJobStateException(self.state)
        logger.info("aborted job %s" % str(self))
        self.state = States.ABORTED
        self.player = None

    ######################################################################
    ###                        IPP Attributes                          ###
    ######################################################################

    @property
    def job_id(self):
        return ipp.JobId(self.id)

    @property
    def job_name(self):
        return ipp.JobName(self.name)

    @property
    def job_originating_user_name(self):
        return ipp.JobOriginatingUserName(self.creator)

    @property
    def job_k_octets(self):
        return ipp.JobKOctets(self.size)

    @property
    def job_state(self):
        return ipp.JobState(self.state)

    @property
    def job_printer_uri(self):
        return ipp.JobPrinterUri(self.printer.uri)


    ######################################################################
    ###                        IPP Operations                          ###
    ######################################################################

    def cancel_job(self):
        pass

    def send_document(self, document, document_name=None,
                      document_format=None, document_natural_language=None,
                      requesting_user_name=None, compression=None,
                      last_document=None):

        if self.state != States.HELD:
            raise InvalidJobStateException(self.state)

        self.player = Player(document)

        if self.size == 0:
            self.size = os.path.getsize(document.name)
        
        self.document_name = str(document_name)
        self.document_format = str(document_format)
        self.document_natural_language = str(document_natural_language)
        self.creator = str(requesting_user_name)
        self.compression = str(compression)
        self.state = States.PENDING

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
