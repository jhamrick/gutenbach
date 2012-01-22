from .errors import InvalidJobException, InvalidPrinterStateException, InvalidJobStateException
from .job import GutenbachJob
from gutenbach.ipp import PrinterStates as States
import gutenbach.ipp as ipp
import logging
import time
import threading
import heapq
import traceback
import sys
import tempfile
from . import sync


# initialize logger
logger = logging.getLogger(__name__)

class GutenbachPrinter(threading.Thread):

    # for IPP
    printer_attributes = [
        "printer-uri-supported",
        "uri-authentication-supported",
        "uri-security-supported",
        "printer-name",
        "printer-state",
        "printer-state-reasons",
        "ipp-versions-supported",
        "operations-supported",
        "charset-configured",
        "charset-supported",
        "natural-language-configured",
        "generated-natural-language-supported",
        "document-format-default",
        "document-format-supported",
        "printer-is-accepting-jobs",
        "queued-job-count",
        "pdl-override-supported",
        "printer-up-time",
        "compression-supported",
        "multiple-operation-time-out",
        "multiple-document-jobs-supported",
    ]

    job_attributes = [
        "job-id",
        "job-name",
        "job-originating-user-name",
        "job-k-octets",
        "job-state",
        "job-printer-uri"
    ]

    operations = [
        "print-job",
        "validate-job",
        "get-jobs",
        "print-uri",
        "create-job",
        "pause-printer",
        "resume-printer",
        "get-printer-attributes",
        "set-printer-attributes",
        "cancel-job",
        "send-document",
        "send-uri",
        "get-job-attributes",
        "set-job-attributes",
        "restart-job",
        "promote-job"
    ]
        
    def __init__(self, name, config, *args, **kwargs):

        super(GutenbachPrinter, self).__init__(*args, **kwargs)
        
        self.name = name
        self.config = config
        self.time_created = int(time.time())

        self.finished_jobs = []
        self.pending_jobs = []
        self.current_job = None
        self.jobs = {}

        self.lock = threading.RLock()
        self._running = False
        self.paused = False

        # CUPS ignores jobs with id 0, so we have to start at 1
        self._next_job_id = 1

    @sync
    def __repr__(self):
        return str(self)

    @sync
    def __str__(self):
        return "<Printer '%s'>" % self.name

    def run(self):
        self._running = True
        while self._running:
            try:
                with self.lock:
                    if self.current_job is None:
                        self.start_job()
                    elif self.current_job.is_done:
                        self.complete_job()
            except:
                logger.fatal(traceback.format_exc())
                sys.exit(1)
            time.sleep(0.1)

    def stop(self):
        with self.lock:
            self._running = False
        if self.ident is not None and self.isAlive():
            self.join()

    ######################################################################
    ###                          Properties                            ###
    ######################################################################

    @property
    def uris(self):
        uris = ["ipp://localhost:8000/printers/" + self.name,
                "ipp://localhost/printers/" + self.name]
        return uris
    
    @property
    def uri(self):
        return self.uris[0]

    @property
    @sync
    def state(self):
        if self.is_running and self.current_job is not None:
            state = States.PROCESSING
        elif self.is_running and len(self.pending_jobs) == 0:
            state = States.IDLE
        else:
            state = States.STOPPED
        return state

    @property
    @sync
    def active_jobs(self):
        jobs = self.pending_jobs[:]
        if self.current_job is not None:
            jobs.insert(0, self.current_job.id)
        return jobs

    @property
    def is_running(self):
        running = self.ident is not None and self.isAlive() and self._running
        return running

    ######################################################################
    ###                            Methods                             ###
    ######################################################################

    @sync
    def assert_running(self):
        if not self.is_running:
            raise RuntimeError, "%s not started" % str(self)

    @sync
    def start_job(self):
        self.assert_running()
        if not self.paused and self.current_job is None:
            try:
                job_id = heapq.heappop(self.pending_jobs)
                self.current_job = self.get_job(job_id)
                self.current_job.play()
            except IndexError:
                self.current_job = None
            except InvalidJobStateException:
                heapq.heappush(self.pending_jobs, self.current_job.id)
                self.current_job = None
                    
    @sync
    def complete_job(self):
        self.assert_running()
        if not self.paused and self.current_job is not None:
            try:
                if not self.current_job.is_done:
                    self.current_job.stop()
            finally:
                self.finished_jobs.append(self.current_job.id)
                self.current_job = None

    @sync
    def get_job(self, job_id):
        self.assert_running()
        if job_id not in self.jobs:
            raise InvalidJobException(job_id)
        return self.jobs[job_id]

    ######################################################################
    ###                        IPP Attributes                          ###
    ######################################################################

    @property
    def printer_uri_supported(self):
        self.assert_running()
        return ipp.PrinterUriSupported(self.uri)
    @printer_uri_supported.setter
    def printer_uri_supported(self, val):
        self.assert_running()
        raise ipp.errors.AttributesNotSettable("printer-uri-supported")

    @property
    def uri_authentication_supported(self):
        self.assert_running()
        return ipp.UriAuthenticationSupported("none")
    @uri_authentication_supported.setter
    def uri_authentication_supported(self, val):
        self.assert_running()
        raise ipp.errors.AttributesNotSettable("uri-authentication-supported")

    @property
    def uri_security_supported(self):
        self.assert_running()
        return ipp.UriSecuritySupported("none")
    @uri_security_supported.setter
    def uri_security_supported(self, val):
        self.assert_running()
        raise ipp.errors.AttributesNotSettable("uri-security-supported")

    @property
    def printer_name(self):
        self.assert_running()
        return ipp.PrinterName(self.name)
    @printer_name.setter
    def printer_name(self, val):
        self.assert_running()
        raise ipp.errors.AttributesNotSettable("printer-name")

    @property
    def printer_state(self):
        self.assert_running()
        return ipp.PrinterState(self.state)
    @printer_state.setter
    def printer_state(self, val):
        self.assert_running()
        raise ipp.errors.AttributesNotSettable("printer-state")

    @property
    def printer_state_reasons(self):
        self.assert_running()
        return ipp.PrinterStateReasons("none")
    @printer_state_reasons.setter
    def printer_state_reasons(self, val):
        self.assert_running()
        raise ipp.errors.AttributesNotSettable("printer-state-reasons")

    @property
    def ipp_versions_supported(self):
        self.assert_running()
        return ipp.IppVersionsSupported(*self.config['ipp-versions'])
    @ipp_versions_supported.setter
    def ipp_versions_supported(self, val):
        self.assert_running()
        raise ipp.errors.AttributesNotSettable("ipp-versions-supported")

    # XXX: We should query ourself for the supported operations
    @property
    def operations_supported(self):
        self.assert_running()
        return ipp.OperationsSupported(ipp.OperationCodes.GET_JOBS)
    @operations_supported.setter
    def operations_supported(self, val):
        self.assert_running()
        raise ipp.errors.AttributesNotSettable("operations-supported")

    @property
    def charset_configured(self):
        self.assert_running()
        return ipp.CharsetConfigured("utf-8") # XXX
    @charset_configured.setter
    def charset_configured(self, val):
        self.assert_running()
        raise ipp.errors.AttributesNotSettable("charset-configured")
        
    @property
    def charset_supported(self):
        self.assert_running()
        return ipp.CharsetSupported("utf-8") # XXX
    @charset_supported.setter
    def charset_supported(self, val):
        self.assert_running()
        raise ipp.errors.AttributesNotSettable("charset-supported")

    @property
    def natural_language_configured(self):
        self.assert_running()
        return ipp.NaturalLanguageConfigured("en-us")
    @natural_language_configured.setter
    def natural_language_configured(self, val):
        self.assert_running()
        raise ipp.errors.AttributesNotSettable("natural-language-configured")

    @property
    def generated_natural_language_supported(self):
        self.assert_running()
        return ipp.GeneratedNaturalLanguageSupported("en-us")
    @generated_natural_language_supported.setter
    def generated_natural_language_supported(self, val):
        self.assert_running()
        raise ipp.errors.AttributesNotSettable("generated-natural-language-supported")

    @property
    def document_format_default(self):
        self.assert_running()
        return ipp.DocumentFormatDefault("application/octet-stream")
    @document_format_default.setter
    def document_format_default(self, val):
        self.assert_running()
        raise ipp.errors.AttributesNotSettable("document-format-default")

    @property
    def document_format_supported(self):
        self.assert_running()
        return ipp.DocumentFormatSupported("application/octet-stream", "audio/mp3")
    @document_format_supported.setter
    def document_format_supported(self, val):
        self.assert_running()
        raise ipp.errors.AttributesNotSettable("document-format-supported")

    @property
    def printer_is_accepting_jobs(self):
        self.assert_running()
        return ipp.PrinterIsAcceptingJobs(True)
    @printer_is_accepting_jobs.setter
    def printer_is_accepting_jobs(self, val):
        self.assert_running()
        raise ipp.errors.AttributesNotSettable("printer-is-accepting-jobs")

    @property
    def queued_job_count(self):
        self.assert_running()
        return ipp.QueuedJobCount(len(self.active_jobs))
    @queued_job_count.setter
    def queued_job_count(self, val):
        self.assert_running()
        raise ipp.errors.AttributesNotSettable("queued-job-count")

    @property
    def pdl_override_supported(self):
        self.assert_running()
        return ipp.PdlOverrideSupported("not-attempted")
    @pdl_override_supported.setter
    def pdl_override_supported(self, val):
        self.assert_running()
        raise ipp.errors.AttributesNotSettable("pdl-override-supported")

    @property
    def printer_up_time(self):
        self.assert_running()
        return ipp.PrinterUpTime(int(time.time()) - self.time_created)
    @printer_up_time.setter
    def printer_up_time(self, val):
        self.assert_running()
        raise ipp.errors.AttributesNotSettable("printer-up-time")

    @property
    def compression_supported(self):
        self.assert_running()
        return ipp.CompressionSupported("none")
    @compression_supported.setter
    def compression_supported(self, val):
        self.assert_running()
        raise ipp.errors.AttributesNotSettable("compression-supported")

    @property
    def multiple_operation_time_out(self):
        self.assert_running()
        return ipp.MultipleOperationTimeOut(240)
    @multiple_operation_time_out.setter
    def multiple_operation_time_out(self, val):
        self.assert_running()
        raise ipp.errors.AttributesNotSettable("multiple-operation-time-out")

    @property
    def multiple_document_jobs_supported(self):
        self.assert_running()
        return ipp.MultipleDocumentJobsSupported(False)
    @multiple_document_jobs_supported.setter
    def multiple_document_jobs_supported(self, val):
        self.assert_running()
        raise ipp.errors.AttributesNotSettable("multiple-document-jobs-supported")

    ######################################################################
    ###                      Job IPP Attributes                        ###
    ######################################################################

    def job_id(self, job_id):
        self.assert_running()
        job = self.get_job(job_id)
        return ipp.JobId(job.id)

    def job_name(self, job_id):
        self.assert_running()
        job = self.get_job(job_id)
        return ipp.JobName(job.name)

    def job_originating_user_name(self, job_id):
        self.assert_running()
        job = self.get_job(job_id)
        return ipp.JobOriginatingUserName(job.creator)

    def job_k_octets(self, job_id):
        self.assert_running()
        job = self.get_job(job_id)
        return ipp.JobKOctets(job.size)

    def job_state(self, job_id):
        self.assert_running()
        job = self.get_job(job_id)
        return ipp.JobState(job.state)

    def job_printer_uri(self, job_id):
        self.assert_running()
        job = self.get_job(job_id)
        return ipp.JobPrinterUri(self.uri)

    ######################################################################
    ###                        IPP Operations                          ###
    ######################################################################

    @sync
    def print_job(self, document, document_name=None, document_format=None,
                  document_natural_language=None, requesting_user_name=None,
                  compression=None, job_name=None, job_k_octets=None):

        self.assert_running()

        # create the job
        job_id = self.create_job(
            requesting_user_name=requesting_user_name,
            job_name=job_name,
            job_k_octets=job_k_octets)
        
        # send the document
        self.send_document(
            job_id,
            document,
            document_name=document_name,
            document_format=document_format,
            document_natural_language=document_natural_language,
            requesting_user_name=requesting_user_name,
            compression=compression,
            last_document=False)

        return job_id

    @sync
    def verify_job(self, document_name=None, document_format=None,
                  document_natural_language=None, requesting_user_name=None,
                  compression=None, job_name=None, job_k_octets=None):

        self.assert_running()

        job_id = self._next_job_id
        job = GutenbachJob(
            job_id,
            creator=requesting_user_name,
            name=job_name)
        job.spool(tempfile.TemporaryFile())
        job.abort()
        del job

    @sync
    def get_jobs(self, requesting_user_name=None, which_jobs=None,
                 requested_attributes=None):
        
        self.assert_running()

        # Filter by the which-jobs attribute
        if which_jobs is None:
            which_jobs = "not-completed"

        if which_jobs == "completed":
            jobs = [self.jobs[job_id] for job_id in self.finished_jobs]
        elif which_jobs == "not-completed":
            jobs = [self.jobs[job_id] for job_id in self.active_jobs]
        else:
            raise ipp.errors.ClientErrorAttributes(
                which_jobs, ipp.WhichJobs(which_jobs))

        # Filter by username
        if requesting_user_name is None:
            user_jobs = jobs
        else:
            user_jobs = [job for job in jobs if job.creator == requesting_user_name]

        # Get the attributes of each job
        job_attrs = [self.get_job_attributes(
            job.id, requested_attributes=requested_attributes) for job in user_jobs]
        
        return job_attrs

    @sync
    def print_uri(self):
        self.assert_running()

    @sync
    def create_job(self, requesting_user_name=None, job_name=None,
                   job_k_octets=None):

        self.assert_running()

        job_id = self._next_job_id
        self._next_job_id += 1
        
        job = GutenbachJob(
            job_id,
            creator=requesting_user_name,
            name=job_name)

        self.jobs[job_id] = job
        self.pending_jobs.append(job_id)
        
        return job_id

    @sync
    def pause_printer(self):
        """Pause the printer.

        Does nothing if the printer is already paused.
        """
        
        self.assert_running()
        if not self.paused:
            if self.current_job is not None and self.current_job.is_playing:
                self.current_job.pause()
            self.paused = True
            logger.info("%s paused", str(self))

    @sync
    def resume_printer(self):
        """Resume the printer.

        Does nothing if the printer is not paused.
        """
        
        self.assert_running()
        if self.paused:
            if self.current_job is not None:
                self.current_job.resume()
            self.paused = False
            logger.info("%s unpaused", str(self))

    @sync
    def get_printer_attributes(self, requested_attributes=None):
        self.assert_running()
        if requested_attributes is None:
            requested = self.printer_attributes
        else:
            requested = [a for a in self.printer_attributes \
                         if a in requested_attributes]

        _attributes = [attr.replace("-", "_") for attr in requested]
        attributes = [getattr(self, attr) for attr in _attributes]
        return attributes

    @sync
    def set_printer_attributes(self, job_id, attributes):
        self.assert_running()
        for attr in attributes:
            try:
                setattr(self, attr, attributes[attr])
            except AttributeError:
                raise ipp.errors.ClientErrorAttributes

    @sync
    def cancel_job(self, job_id, requesting_user_name=None):
        self.assert_running()
        job = self.get_job(job_id)
        try:
            job.cancel()
        except InvalidJobStateException:
            # XXX
            raise

    @sync
    def send_document(self, job_id, document, document_name=None,
                      document_format=None, document_natural_language=None,
                      requesting_user_name=None, compression=None,
                      last_document=None):

        self.assert_running()
        job = self.get_job(job_id)
        job.spool(document)

    @sync
    def send_uri(self, job_id, document_uri, document_name=None,
                 document_format=None, document_natural_language=None,
                 requesting_user_name=None, compression=None,
                 last_document=None):

        self.assert_running()
        job = self.get_job(job_id)
        # XXX: need to validate URI
        # XXX: need to deal with the URI stream?
        #job.spool_uri(document_uri)

    @sync
    def get_job_attributes(self, job_id, requested_attributes=None):

        self.assert_running()
        if requested_attributes is None:
            requested = self.job_attributes
        else:
            requested = [a for a in self.job_attributes \
                         if a in requested_attributes]

        _attributes = [attr.replace("-", "_") for attr in requested]
        attributes = [getattr(self, attr)(job_id) for attr in _attributes]
        return attributes

    @sync
    def set_job_attributes(self, job_id, attributes):

        self.assert_running()
        job = self.get_job(job_id)
        for attr in attributes:
            if attr in ("job-id", "job-k-octets", "job-state", "job-printer-uri"):
                raise ipp.errors.ClientErrorAttributesNotSettable(attr)
            elif attr == "job-name":
                job.name = attributes[attr]
            elif attr == "job-originating-user-name":
                job.creator = attributes[attr] # XXX: do we want this?

    @sync
    def restart_job(self, job_id, requesting_user_name=None):

        self.assert_running()
        job = self.get_job(job_id)
        try:
            job.restart()
        except InvalidJobStateException:
            # XXX
            raise ipp.errors.ClientErrorNotPossible

        self.finished_jobs.remove(job_id)
        self.pending_jobs.append(job_id)

    @sync
    def promote_job(self, job_id, requesting_user_name=None):
        # According to RFC 3998, we need to put the job at the front
        # of the queue (so that when the currently playing job
        # completes, this one will go next
        
        self.assert_running()
        job = self.get_job(job_id)
        job.priority = 1 # XXX we need to actually do something
                         # correct here
