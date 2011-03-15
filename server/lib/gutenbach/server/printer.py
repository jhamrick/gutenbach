import alsaaudio as aa
import gutenbach.ipp
from gutenbach.ipp.attribute import Attribute
from .exceptions import InvalidJobException, \
     InvalidPrinterStateException

class Printer(object):

    def __init__(self, name, card, mixer):

	self.name = name

	if card >= len(aa.cards()):
	    raise aa.ALSAAudioError(
		"Audio card at index %d does not exist!" % card)
	elif mixer not in aa.mixers(card):
	    raise aa.ALSAAudioError(
		"Audio mixer '%s' does not exist!" % mixer)
	
	self.card = card
	self.mixer = mixer

	self.finished_jobs = []
	self.active_jobs = []
	self.jobs = {}

	self._next_jobid = 0

    @property
    def next_jobid(self):
	self._next_jobid += 1
	return self._next_jobid

    @next_jobid.setter
    def next_jobid(self, val):
	raise AttributeError("Setting next_jobid is illegal!")

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

    def __repr__(self):
	return str(self)

    def __str__(self):
	return "<Printer '%s'>" % self.name
