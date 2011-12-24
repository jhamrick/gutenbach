from exceptions import InvalidJobException, InvalidPrinterStateException
import os
import gutenbach.ipp.object_attributes.job_description_attributes as jda

# initialize logger
logger = logging.getLogger(__name__)

class Job(object):

    # for IPP
    attributes = [
        "job-id",
        "job-name",
        "job-originating-user-name",
        "job-k-octets",
        "job-state",
        "job-printer-uri"
    ]

    def __init__(self, document=None):
	"""Initialize a Gutenbach job.

	This sets the status to 'initializing' and optionally sets the
	document to print to the value of document.
	"""
	 
	self.jid = None
        self.name = document
	self.status = None
	self.document = document
	self.printer = None

    def __getattr__(self, attr):
        try:
            return super(Job, self).__getattr__(attr)
        except AttributeError:
            pass

        return super(Job, self).__getattr__(
            attr.replace("-", "_"))

    def __hasattr__(self, attr):
        has = super(Job, self).__hasattr__(attr)
        if not has:
            has = super(Job, self).__hasattr__(
                attr.replace("-", "_"))
        return has

    #### Job attributes

    @property
    def job_id(self):
        return jda.JobId(self.jid)

    @property
    def job_name(self):
        return jda.JobName(self.name)

    # XXX: we need to actually calculate this!
    @property
    def job_originating_user_name(self):
        return jda.JobOriginatingUserName("jhamrick")

    # XXX: we need to actually calculate this!
    @property
    def job_k_octets(self):
        return jda.JobKOctets(1)

    @property
    def job_state(self):
        return jda.JobState(self.status)

    @property
    def job_printer_uri(self):
        return jda.JobPrinterUri(self.printer.uri)

    def get_job_attributes(self, request):
        attributes = [getattr(self, attr) for attr in self.attributes]
        return attributes
    
    #######

    def enqueue(self, printer, job_id):
	if self.status != None:
	    raise InvalidJobException(
		"Cannot enqueue a job that has " + \
		"already been initialized!")
	self.printer = printer
        self.jid = job_id
	self.status = const.JobStates.PENDING

    def play(self):
	if self.status != 'active':
	    raise InvalidJobException(
		"Cannot play an inactive job!")
	
	self.status = const.JobStates.PROCESSING
	# TODO: add external call to music player
        print "Playing job %s" % str(self)
	self.printer.complete_job(self.jid)

    def finish(self):
	self.status = const.JobStates.COMPLETE

    def __repr__(self):
	return str(self)

    def __str__(self):
        return "<Job %d '%s'>" % \
               (self.jid if self.jid is not None else -1, \
                self.document)
