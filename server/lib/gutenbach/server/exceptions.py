class InvalidJobException(Exception):
    def __init__(self, jobid):
	self.jobid = jobid

    def __str__(self):
	return "Job with id '%d' does not exist!" % self.jobid

class InvalidPrinterStateException(Exception):
    def __init__(self, message):
	self.message = message

    def __str__(self):
	return self.message

class MalformedIPPRequestException(Exception):
    def __init__(self, message):
        self.message = message

    def __str__(self):
        return self.message
