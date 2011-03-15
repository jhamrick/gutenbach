import os
from exceptions import InvalidJobException, \
     InvalidPrinterStateException

class Job(object):

    def __init__(self, document=None):
	"""Initialize a Gutenbach job.

	This sets the status to 'initializing' and optionally sets the
	document to print to the value of document.
	"""
	 
	self._jobid = None
	self._status = 'initializing'
	self._document = document
	self._printer = None

    @property
    def jobid(self):
	return self._jobid

    @jobid.setter
    def jobid(self, val):
	raise AttributeError("Setting jobid is illegal!")

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

    @status.setter
    def status(self, val):
	raise AttributeError(
	    "Setting status directly is illegal!  " + \
	    "Please use enqueue(), play(), or finish().")

    @property
    def printer(self):
	return self._printer

    @printer.setter
    def printer(self, val):
	raise AttributeError(
	    "Setting printer directly is illegal!  " + \
	    "Please use enqueue().")

    def enqueue(self, printer, jobid):
	if self.status != 'initializing':
	    raise InvalidJobException(
		"Cannot enqueue a job that has " + \
		"already been initialized!")
	self._printer = printer
        self._jobid = jobid
	self._status = 'active'

    def play(self):
	if self.status != 'active':
	    raise InvalidJobException(
		"Cannot play an inactive job!")
	
	self._status = 'playing'
	# TODO: add external call to music player
        print "Playing job %s" % str(self)
	self.printer.complete_job(self.jobid)

    def finish(self):
	self._status = 'finished'

    def __repr__(self):
	return str(self)

    def __str__(self):
        return "<Job %d '%s'>" % \
               (self.jobid if self.jobid is not None else -1, \
                                  self.document)
