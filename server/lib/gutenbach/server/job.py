from exceptions import InvalidJobException, InvalidPrinterStateException
import os

# initialize logger
logger = logging.getLogger(__name__)

class Job(object):

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
	 
	self._id = None
        self._name = document
	self._status = None
	self._document = document
	self._printer = None

    @property
    def job_id(self):
	return ipp.Attribute(
            'job-id',
            [ipp.Value(ipp.Tags.INTEGER, self._id)])

    @property
    def job_name(self):
        return ipp.Attribute(
            'job-name',
            [ipp.Value(ipp.Tags.NAME_WITHOUT_LANGUAGE, self._name)])

    # XXX: we need to actually calculate this!
    @property
    def job_originating_user_name(self):
        return ipp.Attribute(
            'job-originating-user-name',
            [ipp.Value(ipp.Tags.NAME_WITHOUT_LANGUAGE, "jhamrick")])

    # XXX: we need to actually calculate this!
    @property
    def job_k_octets(self):
        return ipp.Attribute(
            'job-k-octets',
            [ipp.Value(ipp.Tags.INTEGER, 1)])

    @property
    def job_state(self):
        return ipp.Attribute(
            'job-state',
            [ipp.Value(ipp.Tags.ENUM, self._status)])

    @property
    def job_printer_uri(self):
        return ipp.Attribute(
            'job-printer-uri',
            [ipp.Value(ipp.Tags.URI, self._printer._uri)])

    def get_job_attributes(self, request):
        attributes = [getattr(self, attr.replace("-", "_")) for attr in self.attributes]
        return attributes

    
    #######
    @property
    def document(self):
	return self._document

    @document.setter
    def document(self, path):
	if not os.path.exists(path):
	    raise IOError("Document '%s' does not exist!" % path)
	self._document = path

    @property
    def status(self):
	return self._status

    @property
    def printer(self):
	return self._printer

    def enqueue(self, printer, job_id):
	if self._status != None:
	    raise InvalidJobException(
		"Cannot enqueue a job that has " + \
		"already been initialized!")
	self._printer = printer
        self._job_id = job_id
	self._status = const.JobStates.PENDING

    def play(self):
	if self.status != 'active':
	    raise InvalidJobException(
		"Cannot play an inactive job!")
	
	self._status = const.JobStates.PROCESSING
	# TODO: add external call to music player
        print "Playing job %s" % str(self)
	self._printer.complete_job(self._id)

    def finish(self):
	self._status = const.JobStates.COMPLETE

    def __repr__(self):
	return str(self)

    def __str__(self):
        return "<Job %d '%s'>" % \
               (self._id if self._id is not None else -1, \
                self._document)
