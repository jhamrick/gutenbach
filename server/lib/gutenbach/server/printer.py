from . import InvalidJobException, InvalidPrinterStateException
from . import Job
from gutenbach.ipp import PrinterStates as States
import gutenbach.ipp as ipp
import logging
import time

# initialize logger
logger = logging.getLogger(__name__)

class GutenbachPrinter(object):

    # for IPP
    attributes = [
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

    operations = [
        "print-job",
        "complete-job",
        "start-job",
        "get-job",
        "get-jobs",
    ]
        
    def __init__(self, name):

	self.name = name
        self.time_created = int(time.time())
        self.state = States.IDLE

	self.finished_jobs = []
	self.active_jobs = []
	self.jobs = {}

        # cups ignores jobs with id 0, so we have to start at 1
	self._next_jobid = 1

    def __repr__(self):
        return str(self)

    def __str__(self):
        return "<Printer '%s'>" % self.name 

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
    def next_job(self):
        if len(self.active_jobs) == 0:
            job = None
        else:
            job = self.active_jobs[0]
        return job

    ######################################################################
    ###                            Methods                             ###
    ######################################################################

    def complete_job(self, jobid):
	job = self.jobs[self.active_jobs.pop(0)]
	self.finished_jobs.append(job)
	job.finish()
	return job.id

    def start_job(self, jobid):
	job = self.jobs[self.active_jobs[0]]
	if job.status != ipp.JobStates.PENDING:
	    raise InvalidPrinterStateException(job.status)
	job.play()

    def stop(self):
        if len(self.active_jobs) == 0:
            return
        job = self.jobs[self.active_jobs[0]]
        if job.player is not None:
            logger.info("stopping printer %s" % self.name)
            job.player.terminate()

    def get_job(self, jobid):
	if jobid not in self.jobs:
	    raise InvalidJobException(jobid)
	return self.jobs[jobid]

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
    ###                        IPP Operations                          ###
    ######################################################################

    def print_job(self):
        pass

    def validate_job(self):
        pass

    def get_jobs(self, requesting_user_name="", which_jobs=None):
        # Filter by the which-jobs attribute
        if which_jobs is None:
            jobs = self.jobs.values()
        elif which_jobs == "completed":
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
        
        return user_jobs

    def print_uri(self):
        pass

    def create_job(self, requesting_user_name="", job_name="", job_k_octets=0):
        job_id = self._next_jobid
        self._next_jobid += 1
        
        job = Job(job_id,
                  self,
                  creator=requesting_user_name,
                  name=job_name,
                  size=job_k_octets)
        
        self.jobs[job_id] = job
        self.active_jobs.append(job_id)
        self.state = States.PROCESSING
        
        return job

    def pause_printer(self):
        pass

    def resume_printer(self):
        pass

    def get_printer_attributes(self, requested_attributes=None):
        if requested_attributes is None:
            requested = self.attributes
        else:
            requested = [a for a in self.attributes if a in requested_attributes]

        _attributes = [attr.replace("-", "_") for attr in requested]
        attributes = [getattr(self, attr) for attr in _attributes]
        return attributes

    def set_printer_attributes(self):
        pass
