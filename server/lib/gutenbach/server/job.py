from . import errors
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

        Parameters
        ----------
        job_id : integer
            A unique id for this job.
        creator : string
            The user creating the job.
        name : string
            The human-readable name of the job.
        priority : integer
            The priority of the job, used for ordering.
        document : file object
            A file object containing the job data.
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
        """Compares two GutenbachJobs based on their priorities.

        """
        return cmp(self.priority, other.priority)

    def __del__(self):
        if self.player:
            if self.player.is_playing:
                self.player.mplayer_stop()
            if self.player.fh:
                if self.player.fh.closed:
                    self.player.fh.close()
            self.player = None

        self.document = None
        self.id = None
        self.creator = None
        self.name = None
        self.priority = None
        self._why_done = None

    ######################################################################
    ###                          Properties                            ###
    ######################################################################

    @property
    def id(self):
        """Unique job identifier (integer).  Should be a positive
        integer, except when unassigned, when it defaults to -1.
        
        """
        return self._id
    @id.setter
    def id(self, val):
        try:
            self._id = max(int(val), -1)
        except:
            self._id = -1

    @property
    def priority(self):
        """Job priority (integer).  Should be a nonzero positive
        integer; defaults to 1 when unassigned.

        """
        return self._priority
    @priority.setter
    def priority(self, val):
        try:
            self._priority = max(int(val), 1)
        except:
            self._priority = 1

    @property
    def creator(self):
        """The user who created the job (string).  Defaults to an
        empty string.

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
        """The job's human-readable name (string).  Defaults to an
        empty string.

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
        """The size of the job in octets/bytes (integer).  Defaults to
        0 if no document is specified or if there is an error reading
        the document.

        """
        try:
            size = os.path.getsize(self.document)
        except:
            size = 0
        return size

    ######################################################################
    ###                            State                               ###
    ######################################################################

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
        """Whether the job is ready to be played; i.e., it has all the
        necessary data to actually play the audio data.

        """

        return self.is_valid and \
               self.player is not None and \
               not self.player.is_playing and \
               not self._why_done == "canceled" and \
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
        """Whether the job is done playing, regardless of whether it
        completed successfully or not.

        """

        return (self.is_valid and \
                self.player is not None and \
                self.player.is_done) or \
                (self._why_done == "canceled" or \
                 self._why_done == "aborted")

    @property
    def is_completed(self):
        """Whether the job completed successfully.

        """

        return self.is_done and self._why_done == "completed"

    @property
    def is_canceled(self):
        """Whether the job was canceled.

        """

        return self.is_done and self._why_done == "canceled"

    @property
    def is_aborted(self):
        """Whether the job was aborted.

        """

        return self.is_done and self._why_done == "aborted"

    @property
    def state(self):
        """RFC 2911: 4.3.7 job-state (type1 enum)

        'pending': The job is a candidate to start processing, but is
            not yet processing.

        'pending-held': The job is not a candidate for processing for
            any number of reasons but will return to the 'pending'
            state as soon as the reasons are no longer present. The
            job's 'job-state-reason' attribute MUST indicate why the
            job is no longer a candidate for processing.

        'processing': One or more of:
        
            1. the job is using, or is attempting to use, one or more
               purely software processes that are analyzing, creating,
               or interpreting a PDL, etc.,
            2. the job is using, or is attempting to use, one or more
               hardware devices that are interpreting a PDL, making
               marks on a medium, and/or performing finishing, such as
               stapling, etc.,
            3. the Printer object has made the job ready for printing,
               but the output device is not yet printing it, either
               because the job hasn't reached the output device or
               because the job is queued in the output device or some
               other spooler, awaiting the output device to print it.

            When the job is in the 'processing' state, the entire job
            state includes the detailed status represented in the
            Printer object's 'printer-state', 'printer-state-
            reasons', and 'printer-state-message' attributes.

            Implementations MAY, though they NEED NOT, include
            additional values in the job's 'job-state-reasons'
            attribute to indicate the progress of the job, such as
            adding the 'job-printing' value to indicate when the
            output device is actually making marks on paper and/or the
            'processing-to-stop-point' value to indicate that the IPP
            object is in the process of canceling or aborting the
            job. Most implementations won't bother with this nuance.

        'processing-stopped': The job has stopped while processing for
            any number of reasons and will return to the 'processing'
            state as soon as the reasons are no longer present.

            The job's 'job-state-reason' attribute MAY indicate why
            the job has stopped processing. For example, if the output
            device is stopped, the 'printer-stopped' value MAY be
            included in the job's 'job-state-reasons' attribute.

            Note: When an output device is stopped, the device usually
            indicates its condition in human readable form locally at
            the device. A client can obtain more complete device
            status remotely by querying the Printer object's
            'printer-state', 'printer-state-reasons' and 'printer-
            state-message' attributes.

        'canceled': The job has been canceled by a Cancel-Job
            operation and the Printer object has completed canceling
            the job and all job status attributes have reached their
            final values for the job. While the Printer object is
            canceling the job, the job remains in its current state,
            but the job's 'job-state-reasons' attribute SHOULD contain
            the 'processing-to-stop-point' value and one of the
            'canceled-by-user', 'canceled-by-operator', or
            'canceled-at-device' value. When the job moves to the
            'canceled' state, the 'processing-to-stop-point' value, if
            present, MUST be removed, but the 'canceled-by-xxx', if
            present, MUST remain.

        'aborted': The job has been aborted by the system, usually
            while the job was in the 'processing' or 'processing-
            stopped' state and the Printer has completed aborting the
            job and all job status attributes have reached their final
            values for the job. While the Printer object is aborting
            the job, the job remains in its current state, but the
            job's 'job-state-reasons' attribute SHOULD contain the
            'processing-to-stop-point' and 'aborted-by- system'
            values. When the job moves to the 'aborted' state, the
            'processing-to-stop-point' value, if present, MUST be
            removed, but the 'aborted-by-system' value, if present,
            MUST remain.

        'completed': The job has completed successfully or with
            warnings or errors after processing and all of the job
            media sheets have been successfully stacked in the
            appropriate output bin(s) and all job status attributes
            have reached their final values for the job. The job's
            'job-state-reasons' attribute SHOULD contain one of:
            'completed-successfully', 'completed-with-warnings', or
            'completed-with-errors' values.

        The final value for this attribute MUST be one of:
        'completed', 'canceled', or 'aborted' before the Printer
        removes the job altogether. The length of time that jobs
        remain in the 'canceled', 'aborted', and 'completed' states
        depends on implementation. See section 4.3.7.2.

        The following figure shows the normal job state transitions.
        
                                                           +----> canceled
                                                          /
            +----> pending --------> processing ---------+------> completed
            |         ^                   ^               \
        --->+         |                   |                +----> aborted
            |         v                   v               /
            +----> pending-held    processing-stopped ---+

        Normally a job progresses from left to right. Other state
        transitions are unlikely, but are not forbidden. Not shown are
        the transitions to the 'canceled' state from the 'pending',
        'pending- held', and 'processing-stopped' states.

        Jobs reach one of the three terminal states: 'completed',
        'canceled', or 'aborted', after the jobs have completed all
        activity, including stacking output media, after the jobs have
        completed all activity, and all job status attributes have
        reached their final values for the job.

        """

        # XXX verify that these transitions are correct!

        if self.is_ready:
            state = States.PENDING
        elif self.is_playing and not self.is_paused:
            state = States.PROCESSING
        elif self.is_playing and self.is_paused:
            state = States.PROCESSING_STOPPED
        elif self.is_completed:
            state = States.COMPLETED
        elif self.is_canceled:
            state = States.CANCELED
        elif self.is_aborted:
            state = States.ABORTED
        else:
            state = States.PENDING_HELD
        return state

    ######################################################################
    ###                            Methods                             ###
    ######################################################################

    @staticmethod
    def verify_document(document):
        """Verifies that a document has the 'name', 'read', and
        'close' attributes (i.e., it should be like a file object).

        """
        
        if not hasattr(document, "name"):
            raise errors.InvalidDocument, "no name attribute"
        if not hasattr(document, "read"):
            raise errors.InvalidDocument, "no read attribute"
        if not hasattr(document, "close"):
            raise errors.InvalidDocument, "no close attribute"
        if not hasattr(document, "closed"):
            raise errors.InvalidDocument, "no closed attribute"

    def spool(self, document=None):
        """Non-blocking spool.  Job must be valid (see
        'GutenbachJob.is_valid'), and the document must be an open
        file handler.

        Raises
        ------
        InvalidDocument
            If the document is not valid.
        InvalidJobStateException
            If the job is not valid or it is already
            spooled/ready/finished.

        """

        if not self.is_valid or self.state != States.PENDING_HELD:
            raise errors.InvalidJobStateException(self.state)
        self.verify_document(document)
        self.document = document.name
        self.player = Player(document)
        logger.debug("document for job %d is '%s'" % (self.id, self.document))

    def play(self):
        """Non-blocking play.  Job must be ready (see
        'GutenbachJob.is_ready').

        Raises
        ------
        InvalidJobStateException
            If the job is not ready to be played.

        """
        
        # make sure the job is waiting to be played and that it's
        # valid
        if not self.is_ready:
            raise errors.InvalidJobStateException(self.state)
        
        # and set the state to processing if we're good to go
        logger.info("playing job %s" % str(self))

        def _completed():
            logger.info("completed job %s" % str(self))
            self._why_done = "completed"
        self.player.callback = _completed
        self.player.start()

    def pause(self):
        """Non-blocking pause.  Job must be playing (see
        'GutenbachJob.is_playing').

        Raises
        ------
        InvalidJobStateException
            If the job is not playing.

        """
        
        if not self.is_playing:
            raise errors.InvalidJobStateException(self.state)
        self.player.mplayer_pause()

    def resume(self):
        """Non-blocking resume.  Job must be paused (see
        'GutenbachJob.is_paused').

        Raises
        ------
        InvalidJobStateException
            If the job is not paused.

        """
        if not self.is_paused:
            raise errors.InvalidJobStateException(self.state)
        self.player.mplayer_pause()

    def cancel(self):
        """Blocking cancel. The job must not have been previously
        aborted or completed (though this method will succeed if it
        was previously canceled).  This should be used to stop the
        job following an external request.

        Raises
        ------
        InvalidJobStateException
            If the job has already finished.

        """
        
        if self.player and self.player.is_playing:
            self.player._callback = None
            self.player.mplayer_stop()

        elif self.is_done and not self._why_done == "canceled":
            raise errors.InvalidJobStateException(self.state)

        logger.info("canceled job %s" % str(self))
        self._why_done = "canceled"

    def abort(self):
        """Blocking abort. The job must not have been previously
        canceled or completed (though this method will succeed if it
        was previously aborted).  This should be used to stop the job
        following internal errors.

        Raises
        ------
        InvalidJobStateException
            If the job has already finished.

        """

        if self.player and self.player.is_playing:
            self.player._callback = None
            self.player.mplayer_stop()

        elif self.is_done and not self._why_done == "aborted":
            raise errors.InvalidJobStateException(self.state)

        logger.info("aborted job %s" % str(self))
        self._why_done = "aborted"

    def restart(self):
        """Non-blocking restart.  Job must be finished (see
        'GutenbachJob.is_done'), and will be ready to be played (see
        'GutenbachJob.is_ready') if this method is successful.

        Raises
        ------
        InvalidJobStateException
            If the job is not done.

        """

        if not self.is_done:
            raise errors.InvalidJobStateException(self.state)

        logger.debug("restarting job %d", self.id)

        self._why_done = None
        fh = self.player.fh

        if not fh or fh.closed:
            raise RuntimeError, "file handler is closed"

        self.player = Player(fh)
