__all__ = [
    'InvalidJobException',
    'InvalidPrinterStateException',
    'InvalidJobStateException',
    'MissingDataException'
    ]

class InvalidJobException(Exception):
    def __init__(self, jobid):
        self.jobid = jobid
    def __str__(self):
        return "Job does not exist: %d" % self.jobid

class InvalidPrinterStateException(Exception):
    errstr = {
        3: "idle",
        4: "processing",
        5: "stopped"
        }
    
    def __init__(self, state):
        self.state = int(state)
    def __str__(self):
        return "Invalid printer state: %s (%s)" % \
               (self.errstr[self.state], hex(self.state))

class InvalidJobStateException(Exception):
    errstr = {
        3: "pending",
        4: "held",
        5: "processing",
        6: "stopped",
        7: "cancelled",
        8: "aborted",
        9: "complete"
        }
    
    def __init__(self, state):
        self.state = int(state)
    def __str__(self):
        return "Invalid job state: %s (%s)" % \
               (self.errstr[self.state], hex(self.state))

class InvalidDocument(Exception):
    pass
class MissingDataException(Exception):
    pass
