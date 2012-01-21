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
                    elif self.current_job.is_done:
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
                if not self.current_job.is_done:
                    self.current_job.stop()
            finally:
                self.finished_jobs.append(self.current_job.id)
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
    @printer_uri_supported.setter
    def printer_uri_supported(self, val):
        raise ipp.errors.AttributesNotSettable("printer-uri-supported")

    @property
    def uri_authentication_supported(self):
        return ipp.UriAuthenticationSupported("none")
    @uri_authentication_supported.setter
    def uri_authentication_supported(self, val):
        raise ipp.errors.AttributesNotSettable("uri-authentication-supported")

    @property
    def uri_security_supported(self):
        return ipp.UriSecuritySupported("none")
    @uri_security_supported.setter
    def uri_security_supported(self, val):
        raise ipp.errors.AttributesNotSettable("uri-security-supported")

    @property
    def printer_name(self):
        return ipp.PrinterName(self.name)
    @printer_name.setter
    def printer_name(self, val):
        raise ipp.errors.AttributesNotSettable("printer-name")

    @property
    def printer_state(self):
        return ipp.PrinterState(self.state)
    @printer_state.setter
    def printer_state(self, val):
        raise ipp.errors.AttributesNotSettable("printer-state")

    @property
    def printer_state_reasons(self):
        return ipp.PrinterStateReasons("none")
    @printer_state_reasons.setter
    def printer_state_reasons(self, val):
        raise ipp.errors.AttributesNotSettable("printer-state-reasons")

    @property
    def ipp_versions_supported(self):
        return ipp.IppVersionsSupported(*self.config['ipp-versions'])
    @ipp_versions_supported.setter
    def ipp_versions_supported(self, val):
        raise ipp.errors.AttributesNotSettable("ipp-versions-supported")

    # XXX: We should query ourself for the supported operations
    @property
    def operations_supported(self):
        return ipp.OperationsSupported(ipp.OperationCodes.GET_JOBS)
    @operations_supported.setter
    def operations_supported(self, val):
        raise ipp.errors.AttributesNotSettable("operations-supported")

    @property
    def charset_configured(self):
        return ipp.CharsetConfigured("utf-8") # XXX
    @charset_configured.setter
    def charset_configured(self, val):
        raise ipp.errors.AttributesNotSettable("charset-configured")
        
    @property
    def charset_supported(self):
        return ipp.CharsetSupported("utf-8") # XXX
    @charset_supported.setter
    def charset_supported(self, val):
        raise ipp.errors.AttributesNotSettable("charset-supported")

    @property
    def natural_language_configured(self):
        return ipp.NaturalLanguageConfigured("en-us")
    @natural_language_configured.setter
    def natural_language_configured(self, val):
        raise ipp.errors.AttributesNotSettable("natural-language-configured")

    @property
    def generated_natural_language_supported(self):
        return ipp.GeneratedNaturalLanguageSupported("en-us")
    @generated_natural_language_supported.setter
    def generated_natural_language_supported(self, val):
        raise ipp.errors.AttributesNotSettable("generated-natural-language-supported")

    @property
    def document_format_default(self):
        return ipp.DocumentFormatDefault("application/octet-stream")
    @document_format_default.setter
    def document_format_default(self, val):
        raise ipp.errors.AttributesNotSettable("document-format-default")

    @property
    def document_format_supported(self):
        return ipp.DocumentFormatSupported("application/octet-stream", "audio/mp3")
    @document_format_supported.setter
    def document_format_supported(self, val):
        raise ipp.errors.AttributesNotSettable("document-format-supported")

    @property
    def printer_is_accepting_jobs(self):
        return ipp.PrinterIsAcceptingJobs(True)
    @printer_is_accepting_jobs.setter
    def printer_is_accepting_jobs(self, val):
        raise ipp.errors.AttributesNotSettable("printer-is-accepting-jobs")

    @property
    def queued_job_count(self):
        return ipp.QueuedJobCount(len(self.active_jobs))
    @queued_job_count.setter
    def queued_job_count(self, val):
        raise ipp.errors.AttributesNotSettable("queued-job-count")

    @property
    def pdl_override_supported(self):
        return ipp.PdlOverrideSupported("not-attempted")
    @pdl_override_supported.setter
    def pdl_override_supported(self, val):
        raise ipp.errors.AttributesNotSettable("pdl-override-supported")

    @property
    def printer_up_time(self):
        return ipp.PrinterUpTime(int(time.time()) - self.time_created)
    @printer_up_time.setter
    def printer_up_time(self, val):
        raise ipp.errors.AttributesNotSettable("printer-up-time")

    @property
    def compression_supported(self):
        return ipp.CompressionSupported("none")
    @compression_supported.setter
    def compression_supported(self, val):
        raise ipp.errors.AttributesNotSettable("compression-supported")

    @property
    def multiple_operation_time_out(self):
        return ipp.MultipleOperationTimeOut(240)
    @multiple_operation_time_out.setter
    def multiple_operation_time_out(self, val):
        raise ipp.errors.AttributesNotSettable("multiple-operation-time-out")

    @property
    def multiple_document_jobs_supported(self):
        return ipp.MultipleDocumentJobsSupported(False)
    @multiple_document_jobs_supported.setter
    def multiple_document_jobs_supported(self, val):
        raise ipp.errors.AttributesNotSettable("multiple-document-jobs-supported")

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

    def create_job(self, requesting_user_name=None, job_name=None, job_k_octets=None):
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

    def set_printer_attributes(self, job_id, attributes):
        for attr in attributes:
            try:
                setattr(self, attr, attributes[attr])
            except AttributeError:
                raise ipp.errors.ClientErrorAttributes

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
        job.spool(document)

    def send_uri(self, job_id, document_uri, document_name=None,
                 document_format=None, document_natural_language=None,
                 requesting_user_name=None, compression=None,
                 last_document=None):
        job = self.get_job(job_id)
        # XXX: need to validate URI
        # XXX: need to deal with the URI stream?
        #job.spool_uri(document_uri)

    def get_job_attributes(self, job_id, requested_attributes=None):
        if requested_attributes is None:
            requested = self.job_attributes
        else:
            requested = [a for a in self.job_attributes \
                         if a in requested_attributes]

        _attributes = [attr.replace("-", "_") for attr in requested]
        attributes = [getattr(self, attr)(job_id) for attr in _attributes]
        return attributes

    def set_job_attributes(self, job_id, attributes):
        job = self.get_job(job_id)
        for attr in attributes:
            if attr in ("job-id", "job-k-octets", "job-state", "job-printer-uri"):
                raise ipp.errors.ClientErrorAttributesNotSettable(attr)
            elif attr == "job-name":
                job.name = attributes[attr]
            elif attr == "job-originating-user-name":
                job.creator = attributes[attr] # XXX: do we want this?
                
    def restart_job(self, job_id, requesting_user_name=None):
        job = self.get_job(job_id)
        try:
            job.restart()
        except InvalidJobStateException:
            # XXX
            raise ipp.errors.ClientErrorNotPossible

        with self.lock:
            self.finished_jobs.remove(job_id)
            self.pending_jobs.append(job_id)

    def promote_job(self, job_id, requesting_user_name=None):
        # According to RFC 3998, we need to put the job at the front
        # of the queue (so that when the currently playing job
        # completes, this one will go next
        
        job = self.get_job(job_id)
        job.priority = 1 # XXX we need to actually do something
                         # correct here
