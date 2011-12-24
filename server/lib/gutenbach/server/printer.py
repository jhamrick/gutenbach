#import alsaaudio as aa
from .exceptions import InvalidJobException, InvalidPrinterStateException
from gutenbach.ipp.attribute import Attribute
import gutenbach.ipp as ipp
import gutenbach.ipp.constants as const
import gutenbach.ipp.object_attributes.printer_description_attributes as pda
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
        return pda.PrinterUriSupported(self.uri)

    @property
    def uri_authentication_supported(self):
        return pda.UriAuthenticationSupported("none")

    @property
    def uri_security_supported(self):
        return pda.UriSecuritySupported("none")

    @property
    def printer_name(self):
        return pda.PrinterName(self.name)

    @property
    def printer_state(self):
        return pda.PrinterState(ipp.constants.PrinterStates.IDLE)

    @property
    def printer_state_reasons(self):
        return pda.PrinterStateReasons("none")

    @property
    def ipp_versions_supported(self):
        return pda.IppVersionsSupported("1.0", "1.1")

    # XXX: We should query ourself for the supported operations
    @property
    def operations_supported(self):
        return pda.OperationsSupported(ipp.Operations.GET_JOBS)

    @property
    def charset_configured(self):
        return pda.CharsetConfigured("utf-8")

    @property
    def charset_supported(self):
        return pda.CharsetSupported("utf-8")

    @property
    def natural_language_configured(self):
        return pda.NaturalLanguageConfigured("en-us")

    @property
    def generated_natural_language_supported(self):
        return pda.GeneratedNaturalLanguageSupported("en-us")

    @property
    def document_format_default(self):
        return pda.DocumentFormatDefault("application/octet-stream")

    @property
    def document_format_supported(self):
        return pda.DocumentFormatSupported("application/octet-stream", "audio/mp3")

    @property
    def printer_is_accepting_jobs(self):
        return pda.PrinterIsAcceptingJobs(True)

    @property
    def queued_job_count(self):
        return pda.QueuedJobCount(len(self.active_jobs))

    @property
    def pdl_override_supported(self):
        return pda.PdlOverrideSupported("not-attempted")

    @property
    def printer_up_time(self):
        return pda.PrinterUpTime(int(time.time()) - self.time_created)

    @property
    def compression_supported(self):
        return pda.CompressionSupported("none")

    @property
    def multiple_operation_time_out(self):
        return pda.MultipleOperationTimeOut(240)

    @property
    def multiple_document_jobs_supported(self):
        return pda.MultipleDocumentJobsSupported(False)

    def get_printer_attributes(self, request):
        attributes = [getattr(self, attr) for attr in self.attributes]
        return attributes

    ## Printer operations

    def print_job(self, job):
	jobid = self._next_jobid
        self._next_jobid += 1
	self.active_jobs.append(jobid)
	self.jobs[jobid] = job
	job.enqueue(self, jobid)
	return jobid

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
        jobs = [self.jobs[job_id] for job_id in self.active_jobs]
        return jobs            

    def __repr__(self):
	return str(self)

    def __str__(self):
	return "<Printer '%s'>" % self.name
