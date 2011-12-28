#import alsaaudio as aa
from .exceptions import InvalidJobException, InvalidPrinterStateException
from .job import Job
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
        

    #def __init__(self, name, card, mixer):
    def __init__(self, name):

	self.name = name
        self.uri = "ipp://localhost:8000/printers/" + self.name
        self.time_created = int(time.time())
        self.state = "idle"

	# if card >= len(aa.cards()):
	#     raise aa.ALSAAudioError(
	# 	"Audio card at index %d does not exist!" % card)
	# elif mixer not in aa.mixers(card):
	#     raise aa.ALSAAudioError(
	# 	"Audio mixer '%s' does not exist!" % mixer)
	
	# self.card = card
	# self.mixer = mixer

	self.finished_jobs = []
	self.active_jobs = []
	self.jobs = {}

	self._next_jobid = 0

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

    ## Printer attributes

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
        return ipp.PrinterState(ipp.constants.PrinterStates.IDLE)

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

    ## Printer operations

    def get_printer_attributes(self, request=None):
        if request and 'requested-attributes' in request:
            requested = []
            for value in request['requested-attributes'].values:
                if value.value in self.attributes:
                    requested.append(value.value)
        else:
            requested = self.attributes
            
        attributes = [getattr(self, attr) for attr in requested]
        return attributes

    def create_job(self, request):
        operation = request.attribute_groups[0]
        kwargs = {}
        
        # requesting username
        if 'requesting-user-name' in operation:
            username_attr = operation['requesting-user-name']
            username = username_attr.values[0].value
            if username_attr != ipp.RequestingUserName(username):
                raise ipp.errors.ClientErrorBadRequest(str(username_attr))
            kwargs['creator'] = username

        # job name
        if 'job-name' in operation:
            job_name_attr = operation['job-name']
            job_name = job_name_attr.values[0].value
            if job_name_attr != ipp.JobName(job_name):
                raise ipp.errors.ClientErrorBadRequest(str(job_name_attr))
            kwargs['name'] = job_name

        # job size
        if 'job-k-octets' in operation:
            job_k_octets_attr = operation['job-k-octets']
            job_k_octets = job_k_octets_attr.values[0].value
            if job_k_octets_attr != ipp.JobKOctets(job_k_octets):
                raise ipp.errors.ClientErrorBadRequest(str(job_k_octets_attr))
            kwargs['size'] = job_k_octets

        job_id = self._next_jobid
        self._next_jobid += 1
        
        job = Job(job_id, self, **kwargs)
        self.jobs[job_id] = job
        self.active_jobs.append(job_id)
        print self.active_jobs
        return job

    def print_job(self, job):
        pass

    def complete_job(self, jobid):
	job = self.jobs[self.active_jobs.pop(0)]
	if job.jobid != jobid:
	    raise InvalidJobException(
		"Completed job %d has unexpected job id %d!" % \
		(job.jobid, jobid))
	
	self.finished_jobs.append(job)
	job.finish()
	return job.jobid

    def start_job(self, jobid):
	job = self.jobs[self.active_jobs[0]]
	if job.jobid != jobid:
	    raise InvalidJobException(
		"Completed job %d has unexpected job id %d!" % \
		(job.jobid, jobid))

	if job.status == 'playing':
	    raise InvalidPrinterStateException(
		"Next job in queue (id %d) is " + \
		"already playing!" % jobid)

	job.play()

    def get_job(self, jobid):
	if jobid not in self.jobs:
	    raise InvalidJobException(jobid)
	return self.jobs[jobid]

    def get_jobs(self):
        print self.active_jobs
        jobs = [self.jobs[job_id] for job_id in self.active_jobs]
        return jobs

    # def __repr__(self):
    #     return str(self)

    # def __str__(self):
    #     return "<Printer '%s'>" % self.name
