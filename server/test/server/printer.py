from gutenbach.server import GutenbachJob
from gutenbach.server import GutenbachPrinter
from gutenbach.server import errors

from gutenbach.ipp import JobStates as States
import unittest
import tempfile
import time

def make_tempfile():
    fh = tempfile.NamedTemporaryFile()
    fh.write("test\n")
    fh.seek(0)
    return fh

class TestGutenbachPrinter(unittest.TestCase):

    testJobName = "unique_test_job"
    testJobRequestingUserName = "unique_test_username"

    def setUp(self):
        self.printer = GutenbachPrinter("test")
        self.printer.start()

    def tearDown(self):
        self.printer.running = False
        self.printer.join()

    # nb: this test assumes that pause_printer will block until it has paused.
    def testPausePrinter(self):
        self.printer.pause_printer()
        self.assertEqual(self.printer.paused, True)

        # check that no jobs are playing
        for job_id, job in self.printer.jobs.items():
            self.assertEqual(job.is_playing(), False)

    def createTestJob(self):
        return self.printer.create_job(self.testJobRequestingUserName, self.testJobName)
  
    def testCreateJob(self):
        countBeforeAdded = len(self.printer.jobs)
        job_id = self.createTestJob()
        self.assertEqual(len(self.printer.jobs) - 1, countBeforeAdded)

        queued_job = self.printer.get_job(job_id)
        b = queued_job is not None
        self.assertTrue(b)
        self.assertEqual(queued_job.name, self.testJobName)
        self.assertEqual(queued_job.creator, self.testJobRequestingUserName)
        self.assertEqual(queued_job.state, States.HELD)

    def testResumePrinter(self):
        self.printer.resume_printer()
        self.assertEqual(self.printer.paused, False)

    def testJobPlays(self):
        job_id = self.createTestJob()
        fh = make_tempfile()
        self.printer.get_job(job_id).spool(fh)
        self.assertTrue(job_id in self.printer.pending_jobs)
        self.assertFalse(job_id in self.printer.finished_jobs)
        self.printer.complete_job()
        while (self.printer.get_job(job_id).state == States.PENDING):
            time.sleep(0.1)
            continue
        
        non_pending_job = self.printer.get_job(job_id)
        self.assertTrue(non_pending_job.state == States.COMPLETE)

        self.assertFalse(job_id in self.printer.pending_jobs)
        self.assertTrue(job_id in self.printer.finished_jobs)

if __name__ == "__main__":
    unittest.main()
