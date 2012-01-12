from .errors import InvalidJobStateException, MissingDataException
from .player import Player
from gutenbach.ipp import JobStates as States
import logging
import os

# initialize logger
logger = logging.getLogger(__name__)

class GutenbachJob(object):

    def __init__(self, job_id=None, creator=None, name=None,
                 priority=None, document=None):
	"""Create an empty Gutenbach job.

	"""

        self.player = None
        self.document = None

	self.id = job_id
        self.creator = creator
        self.name = name
        self.priority = priority
        self._why_done = None

        if document is not None:
            self.spool(document)

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
            self._id = max(int(val), -1)
        except TypeError:
            self._id = -1

    @property
    def priority(self):
        return self._priority
    @priority.setter
    def priority(self, val):
        try:
            self._priority = max(int(val), 1)
        except TypeError:
            self._priority = 1

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
    def is_valid(self):
        """Whether the job is ready to be manipulated (spooled,
        played, etc).  Note that playing the job still requires it to
        be spooled first.

        """
        return self.id > 0 and \
               self.priority > 0

    @property
    def is_ready(self):
        """Whether the job is ready to be played.

        """
        return self.is_valid and \
               self.player is not None and \
               not self.player.is_playing and \
               not self._why_done == "cancelled" and \
               not self._why_done == "aborted"

    @property
    def is_playing(self):
        """Whether the job is currently playing (regardless of whether
        it's paused).

        """
        return self.is_valid and \
               self.player is not None and \
               self.player.is_playing

    @property
    def is_paused(self):
        """Whether the job is currently paused.

        """
        return self.is_valid and \
               self.player is not None and \
               self.player.is_paused        

    @property
    def is_done(self):
        return (self.is_valid and \
                self.player is not None and \
                self.player.is_done) or \
                (self._why_done == "cancelled" or \
                 self._why_done == "aborted")

    @property
    def state(self):
        """
        State transitions are as follows:
HELD ---> PENDING ---> PROCESSING <--> STOPPED (aka paused)
             ^              |---> CANCELLED
             |              |---> ABORTED
             |              |---> COMPLETE ---|
             |--------------------------------|
        """
        if self.is_ready:
            state = States.PENDING
        elif self.is_playing and not self.is_paused:
            state = States.PROCESSING
        elif self.is_playing and self.is_paused:
            state = States.STOPPED
        elif self.is_done and self._why_done == "completed":
            state = States.COMPLETE
        elif self.is_done and self._why_done == "cancelled":
            state = States.CANCELLED
        elif self.is_done and self._why_done == "aborted":
            state = States.ABORTED
        else:
            state = States.HELD
        return state

    ######################################################################
    ###                            Methods                             ###
    ######################################################################

    def spool(self, document):
        if not self.is_valid:
            raise InvalidJobStateException(self.state)
        self.document = document.name
        self.player = Player(document)
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
            self._why_done = "completed"
        self.player.callback = _completed
        self.player.start()

    def pause(self):
        """Non-blocking pause function.  Sets the job state to
        STOPPED.

        """
        
        if not self.is_playing:
            raise InvalidJobStateException(self.state)
        self.player.mplayer_pause()

    def cancel(self):
        def _cancelled():
            logger.info("cancelled job %s" % str(self))
            self._why_done = "cancelled"

        if self.is_playing:
            self.player.callback = _cancelled
            self.player.mplayer_stop()
        elif self.is_done and not self._why_done == "cancelled":
            raise InvalidJobStateException(self.state)
        else:
            _cancelled()

    def abort(self):
        def _aborted():
            logger.info("aborted job %s" % str(self))
            self._why_done = "aborted"

        if self.is_playing:
            self.player.callback = _aborted
            self.player.mplayer_stop()
        elif self.is_done and not self._why_done == "aborted":
            raise InvalidJobStateException(self.state)
        else:
            _aborted()


