#import alsaaudio as aa
from .exceptions import InvalidJobException, InvalidPrinterStateException
from gutenbach.ipp.attribute import Attribute
import gutenbach.ipp as ipp
import gutenbach.ipp.constants as const
import logging
import time

# initialize logger
logger = logging.getLogger(__name__)

class GutenbachPrinter(object):

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
        "compression-supported"]

    #def __init__(self, name, card, mixer):
    def __init__(self, name):

	self._name = name
        self._uri = "ipp://localhost:8000/printers/" + self._name
        self._time_created = int(time.time())

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

    ## Printer attributes
    @property
    def printer_uri_supported(self):
        return ipp.Attribute(
            "printer-uri-supported",
            [ipp.Value(ipp.Tags.URI, self._uri)])
    
    @property
    def uri_authentication_supported(self):
        return ipp.Attribute(
            "uri-authentication-supported",
            [ipp.Value(ipp.Tags.KEYWORD, "none")])

    @property
    def uri_security_supported(self):
        return ipp.Attribute(
            "uri-security-supported",
            [ipp.Value(ipp.Tags.KEYWORD, "none")])

    @property
    def printer_name(self):
        return ipp.Attribute(
            "printer-name",
            [ipp.Value(ipp.Tags.NAME_WITHOUT_LANGUAGE, self._name)])
        
    @property
    def printer_state(self):
        return ipp.Attribute(
            "printer-state",
            [ipp.Value(ipp.Tags.ENUM, const.PrinterStates.IDLE)])
        
    @property
    def printer_state_reasons(self):
        return ipp.Attribute(
            "printer-state-reasons",
            [ipp.Value(ipp.Tags.KEYWORD, "none")])

    @property
    def ipp_versions_supported(self):
        return ipp.Attribute(
            "ipp-versions-supported",
            [ipp.Value(ipp.Tags.KEYWORD, "1.0"),
             ipp.Value(ipp.Tags.KEYWORD, "1.1")])

    # XXX: We should query ourself for the supported operations
    @property
    def operations_supported(self):
        return ipp.Attribute(
            "operations-supported",
            [ipp.Value(ipp.Tags.ENUM, const.Operations.GET_JOBS)])

    @property
    def charset_configured(self):
        return ipp.Attribute(
            "charset-configured",
            [ipp.Value(ipp.Tags.CHARSET, "utf-8")])

    @property
    def charset_supported(self):
        return ipp.Attribute(
            "charset-supported",
            [ipp.Value(ipp.Tags.CHARSET, "utf-8")])

    @property
    def natural_language_configured(self):
        return ipp.Attribute(
            "natural-language-configured",
            [ipp.Value(ipp.Tags.NATURAL_LANGUAGE, "en-us")])

    @property
    def generated_natural_language_supported(self):
        return ipp.Attribute(
            "generated-natural-language-supported",
            [ipp.Value(ipp.Tags.NATURAL_LANGUAGE, "en-us")])

    @property
    def document_format_default(self):
        return ipp.Attribute(
            "document-format-default",
            [ipp.Value(ipp.Tags.MIME_MEDIA_TYPE, "application/octet-stream")])

    @property
    def document_format_supported(self):
        return ipp.Attribute(
            "document-format-supported",
            [ipp.Value(ipp.Tags.MIME_MEDIA_TYPE, "application/octet-stream"),
             ipp.Value(ipp.Tags.MIME_MEDIA_TYPE, "audio/mp3")])

    @property
    def printer_is_accepting_jobs(self):
        return ipp.Attribute(
            "printer-is-accepting-jobs",
            [ipp.Value(ipp.Tags.BOOLEAN, True)])

    @property
    def queued_job_count(self):
        return ipp.Attribute(
            "queued-job-count",
            [ipp.Value(ipp.Tags.INTEGER, len(self.active_jobs))])

    @property
    def pdl_override_supported(self):
        return ipp.Attribute(
            "pdl-override-supported",
            [ipp.Value(ipp.Tags.KEYWORD, "not-attempted")])

    @property
    def printer_up_time(self):
        return ipp.Attribute(
            "printer-up-time",
            [ipp.Value(ipp.Tags.INTEGER, int(time.time()) - self._time_created)])

    @property
    def compression_supported(self):
        return ipp.Attribute(
            "compression-supported",
            [ipp.Value(ipp.Tags.KEYWORD, "none")])

    def get_printer_attributes(self, request):
        attributes = [getattr(self, attr.replace("-", "_")) for attr in self.attributes]
        return attributes

    ## Printer operations
    @property
    def next_jobid(self):
	self._next_jobid += 1
	return self._next_jobid

    def print_job(self, job):
	jobid = self.next_jobid
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
	return "<Printer '%s'>" % self._name
