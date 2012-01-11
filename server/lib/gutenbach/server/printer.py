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
        
    def __init__(self, name, *args, **kwargs):

        super(GutenbachPrinter, self).__init__(*args, **kwargs)
        
        self.name = name
        self.time_created = int(time.time())

        self.finished_jobs = []
        self.pending_jobs = []
        self.current_job = None
        self.jobs = {}

        self.lock = threading.RLock()
        self.running = False
        self.paused = False

        # CUPS ignores jobs with id 0, so we have to start at 1
        self._next_job_id = 1

    def __repr__(self):
        return str(self)

    def __str__(self):
        return "<Printer '%s'>" % self.name 

    def run(self):
        self.running = True
        while self.running:
            with self.lock:
                try:
                    if self.current_job is None:
                        self.start_job()
                    elif self.current_job.is_finished:
                        self.complete_job()
                except:
                    logger.fatal(traceback.format_exc())
                    sys.exit(1)
            time.sleep(0.1)

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
    def state(self):
        with self.lock:
            if self.current_job is not None:
                val = States.PROCESSING
            elif len(self.pending_jobs) == 0:
                val = States.IDLE
            else:
                val = States.STOPPED
        return val

    @property
    def active_jobs(self):
        with self.lock:
            jobs = self.pending_jobs[:]
            if self.current_job is not None:
                jobs.insert(0, self.current_job.id)
        return jobs

    ######################################################################
    ###                            Methods                             ###
    ######################################################################

    def start_job(self):
        with self.lock:
            if self.current_job is None:
                try:
                    job_id = heapq.heappop(self.pending_jobs)
                    self.current_job = self.get_job(job_id)
                    self.current_job.play()
                except IndexError:
                    self.current_job = None
                except InvalidJobStateException:
                    heapq.heappush(self.pending_jobs, self.current_job.id)
                    self.current_job = None
                    
    def complete_job(self):
        with self.lock:
            if self.current_job is None:
                return

            try:
                if not self.current_job.is_finished:
                    self.current_job.stop()
            finally:
                self.finished_jobs.append(self.current_job)
                self.current_job = None

    def get_job(self, job_id):
        with self.lock:
            if job_id not in self.jobs:
                raise InvalidJobException(job_id)
            job = self.jobs[job_id]
        return job

    ######################################################################
    ###                        IPP Attributes                          ###
    ######################################################################

    @property
    def printer_uri_supported(self):
        return ipp.PrinterUriSupported(self.uri)

    @property
    def uri_authentication_supported(self):
        return ipp.UriAuthenticationSupported("none")

    @property
    def uri_security_supported(self):
        return ipp.UriSecuritySupported("none")

    @property
    def printer_name(self):
        return ipp.PrinterName(self.name)

    @property
    def printer_state(self):
        return ipp.PrinterState(self.state)

    @property
    def printer_state_reasons(self):
        return ipp.PrinterStateReasons("none")

    @property
    def ipp_versions_supported(self):
        return ipp.IppVersionsSupported("1.0", "1.1")

    # XXX: We should query ourself for the supported operations
    @property
    def operations_supported(self):
        return ipp.OperationsSupported(ipp.OperationCodes.GET_JOBS)

    @property
    def charset_configured(self):
        return ipp.CharsetConfigured("utf-8")

    @property
    def charset_supported(self):
        return ipp.CharsetSupported("utf-8")

    @property
    def natural_language_configured(self):
        return ipp.NaturalLanguageConfigured("en-us")

    @property
    def generated_natural_language_supported(self):
        return ipp.GeneratedNaturalLanguageSupported("en-us")

    @property
    def document_format_default(self):
        return ipp.DocumentFormatDefault("application/octet-stream")

    @property
    def document_format_supported(self):
        return ipp.DocumentFormatSupported("application/octet-stream", "audio/mp3")

    @property
    def printer_is_accepting_jobs(self):
        return ipp.PrinterIsAcceptingJobs(True)

    @property
    def queued_job_count(self):
        return ipp.QueuedJobCount(len(self.active_jobs))

    @property
    def pdl_override_supported(self):
        return ipp.PdlOverrideSupported("not-attempted")

    @property
    def printer_up_time(self):
        return ipp.PrinterUpTime(int(time.time()) - self.time_created)

    @property
    def compression_supported(self):
        return ipp.CompressionSupported("none")

    @property
    def multiple_operation_time_out(self):
        return ipp.MultipleOperationTimeOut(240)

    @property
    def multiple_document_jobs_supported(self):
        return ipp.MultipleDocumentJobsSupported(False)

    ######################################################################
    ###                      Job IPP Attributes                        ###
    ######################################################################

    def job_id(self, job_id):
        job = self.get_job(job_id)
        return ipp.JobId(job.id)

    def job_name(self, job_id):
        job = self.get_job(job_id)
        return ipp.JobName(job.name)

    def job_originating_user_name(self, job_id):
        job = self.get_job(job_id)
        return ipp.JobOriginatingUserName(job.creator)

    def job_k_octets(self, job_id):
        job = self.get_job(job_id)
        return ipp.JobKOctets(job.size)

    def job_state(self, job_id):
        job = self.get_job(job_id)
        return ipp.JobState(job.state)

    def job_printer_uri(self, job_id):
        job = self.get_job(job_id)
        return ipp.JobPrinterUri(self.uri)

    ######################################################################
    ###                        IPP Operations                          ###
    ######################################################################

    def print_job(self):
        pass

    def validate_job(self):
        pass

    def get_jobs(self, requesting_user_name=None, which_jobs=None,
                 requested_attributes=None):
        
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

    def print_uri(self):
        pass

    def create_job(self, requesting_user_name="", job_name="", job_k_octets=0):
        job_id = self._next_job_id
        self._next_job_id += 1
        
        job = GutenbachJob(
            job_id,
            creator=requesting_user_name,
            name=job_name)
        
        self.jobs[job_id] = job
        self.pending_jobs.append(job_id)
        
        return job_id

    def pause_printer(self):
        pass

    def resume_printer(self):
        pass

    def get_printer_attributes(self, requested_attributes=None):
        if requested_attributes is None:
            requested = self.printer_attributes
        else:
            requested = [a for a in self.printer_attributes \
                         if a in requested_attributes]

        _attributes = [attr.replace("-", "_") for attr in requested]
        attributes = [getattr(self, attr) for attr in _attributes]
        return attributes

    def set_printer_attributes(self):
        pass

    def cancel_job(self, job_id, requesting_user_name=None):
        job = self.get_job(job_id)
        try:
            job.cancel()
        except InvalidJobStateException:
            # XXX
            raise

    def send_document(self, job_id, document, document_name=None,
                      document_format=None, document_natural_language=None,
                      requesting_user_name=None, compression=None,
                      last_document=None):

        job = self.get_job(job_id)
        job.spool(document, username=requesting_user_name)

    def send_uri(self):
        pass

    def get_job_attributes(self, job_id, requested_attributes=None):
        if requested_attributes is None:
            requested = self.job_attributes
        else:
            requested = [a for a in self.job_attributes \
                         if a in requested_attributes]

        _attributes = [attr.replace("-", "_") for attr in requested]
        attributes = [getattr(self, attr)(job_id) for attr in _attributes]
        return attributes

    def set_job_attributes(self):
        pass

    def restart_job(self):
        pass

    def promote_job(self):
        pass
