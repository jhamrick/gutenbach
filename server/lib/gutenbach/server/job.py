from .errors import InvalidJobStateException, MissingDataException
from .player import Player
from gutenbach.ipp import JobStates as States
import logging
import os

# initialize logger
logger = logging.getLogger(__name__)

class GutenbachJob(object):

    def __init__(self, job_id=None, creator=None, name=None):
	"""Create an empty Gutenbach job.

	"""

        self.player = None

	self.id = job_id
        self.creator = creator
        self.name = name
	self.state = States.HELD
        self.priority = 1
        self.document = None

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
        try:
            size = os.path.getsize(self.document)
        except:
            size = 0
        return size

    @property
    def is_playing(self):
        return self.state == States.PROCESSING

    @property
    def is_ready(self):
        return self.state == States.PENDING

    @property
    def is_finished(self):
        return self.state != States.PENDING and \
               self.state != States.PROCESSING and \
               self.state != States.HELD
        
    ######################################################################
    ###                            Methods                             ###
    ######################################################################

    def spool(self, document, username=None):
        if self.state != States.HELD:
            raise InvalidJobStateException(self.state)

        self.document = document.name
        self.player = Player(document)
        self.creator = username
        self.state = States.PENDING

        logger.debug("document for job %d is '%s'" % (self.id, self.document))


    def play(self):
        """Non-blocking play function.  Sets the job state to
        PROCESSING.

        Raises
        ------
        InvalidJobStateException
            If the job is not ready to be played.

        """
        
        # make sure the job is waiting to be played and that it's
        # valid
        if not self.is_ready:
            raise InvalidJobStateException(self.state)
        
        # and set the state to processing if we're good to go
        logger.info("playing job %s" % str(self))

        def _completed():
            logger.info("completed job %s" % str(self))
            self.state = States.COMPLETE
            self.player = None

	self.state = States.PROCESSING
        self.player.callback = _completed
        self.player.start()

    def pause(self):
        """Non-blocking pause function.  Sets the job state to
        STOPPED.

        """
        
        if not self.is_playing:
            raise InvalidJobStateException(self.state)
        
        self.player.mplayer_pause()
        self.state = States.STOPPED

    def cancel(self):
        def _canceled():
            logger.info("canceled job %s" % str(self))
            self.state = States.CANCELLED
            self.player = None

        if self.is_playing:
            self.player.callback = _canceled
            self.player.mplayer_stop()
        elif self.is_finished:
            raise InvalidJobStateException(self.state)
        
        self.state = States.CANCELLED

    def abort(self):
        def _aborted():
            logger.info("aborted job %s" % str(self))
            self.state = States.ABORTED
            self.player = None

        if self.is_playing:
            self.player.callback = _aborted
            self.player.mplayer_stop()
        elif self.is_finished:
            raise InvalidJobStateException(self.state)
        
        self.state = States.ABORTED


