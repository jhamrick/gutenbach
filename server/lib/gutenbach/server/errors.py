__all__ = [
    'InvalidJobException',
    'InvalidPrinterStateException',
    'InvalidJobStateException',
    ]

class InvalidJobException(Exception):
    def __init__(self, jobid):
	self.jobid = jobid
    def __str__(self):
	return "Job does not exist: %d" % self.jobid

class InvalidPrinterStateException(Exception):
    def __init__(self, state):
        self.state = hex(state)
    def __str__(self):
        return "Invalid printer state: %s" % self.state

class InvalidJobStateException(Exception):
    def __init__(self, state):
        self.state = hex(state)
    def __str__(self):
        return "Invalid job state: %s" % self.state
