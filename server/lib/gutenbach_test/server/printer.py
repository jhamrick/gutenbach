__all__ = [
    'TestEmptyGutenbachPrinter',
    'TestBadEmptyGutenbachPrinter',
    'TestGutenbachPrinter',
    ]

from gutenbach.server import GutenbachJob
from gutenbach.server import GutenbachPrinter
from gutenbach.server import errors

from gutenbach.ipp import PrinterStates as States
import unittest
import tempfile
import time
import logging
import threading

def make_tempfile():
    fh = tempfile.NamedTemporaryFile()
    fh.write("test\n")
    fh.seek(0)
    return fh

class TestEmptyGutenbachPrinter(unittest.TestCase):

    testJobName = "unique_test_job"
    testJobRequestingUserName = "unique_test_username"
    testPrinterConfig = {
        'ipp-versions': ["1.0", "1.1"]
        }

    def setUp(self):
        self.printer = GutenbachPrinter("test", self.testPrinterConfig)

    def testName(self):
        self.assertEqual(self.printer.name, "test")
    def testConfig(self):
        self.assertEqual(self.printer.config, self.testPrinterConfig)
    def testTimeCreated(self):
        self.assertTrue(self.printer.time_created is not None)
    def testFinishedJobs(self):
        self.assertEqual(self.printer.finished_jobs, [])
    def testPendingJobs(self):
        self.assertTrue(self.printer.pending_jobs.empty())
    def testCurrentJob(self):
        self.assertEqual(self.printer.current_job, None)
    def testJobs(self):
        self.assertEqual(self.printer.jobs, {})
    def testActiveJobs(self):
        self.assertEqual(self.printer.active_jobs, [])
    def testRunning(self):
        self.assertEqual(self.printer.is_running, False)
    def testPaused(self):
        self.assertEqual(self.printer.paused, False)
    def testNextJobId(self):
        self.assertEqual(self.printer._next_job_id, 1)
    def testState(self):
        self.assertEqual(self.printer.state, States.STOPPED)

    def testGetJob(self):
        self.assertRaises(RuntimeError, self.printer.get_job, 0)

    def testIPPAttributes(self):
        for attribute in self.printer.printer_attributes:
            attr = attribute.replace("-", "_")
            self.assertRaises(RuntimeError, getattr, self.printer, attr)
            self.assertRaises(RuntimeError, setattr, self.printer, attr, None)
        for attribute in self.printer.job_attributes:
            attr = getattr(self.printer, attribute.replace("-", "_"))
            self.assertRaises(RuntimeError, attr, 0)

    def testIPPOperations(self):
        self.assertRaises(RuntimeError, self.printer.print_job, None)
        self.assertRaises(RuntimeError, self.printer.validate_job)
        self.assertRaises(RuntimeError, self.printer.get_jobs)
        self.assertRaises(RuntimeError, self.printer.print_uri)
        self.assertRaises(RuntimeError, self.printer.create_job)
        self.assertRaises(RuntimeError, self.printer.pause_printer)
        self.assertRaises(RuntimeError, self.printer.resume_printer)
        self.assertRaises(RuntimeError, self.printer.get_printer_attributes)
        self.assertRaises(RuntimeError, self.printer.set_printer_attributes, {})
        self.assertRaises(RuntimeError, self.printer.cancel_job, 0)
        self.assertRaises(RuntimeError, self.printer.send_document, 0, None)
        self.assertRaises(RuntimeError, self.printer.send_uri, 0, "")
        self.assertRaises(RuntimeError, self.printer.get_job_attributes, 0)
        self.assertRaises(RuntimeError, self.printer.set_job_attributes, 0, {})
        self.assertRaises(RuntimeError, self.printer.restart_job, 0)
        self.assertRaises(RuntimeError, self.printer.promote_job, 0)

class TestBadEmptyGutenbachPrinter(unittest.TestCase):

    testJobName = "unique_test_job"
    testJobRequestingUserName = "unique_test_username"
    testPrinterConfig = {
        'ipp-versions': ["1.0", "1.1"]
        }

    def testBadPrinterName(self):
        printer = GutenbachPrinter(None, self.testPrinterConfig)
        self.assertEqual(printer.name, "None")
        printer.name = "foo"
        self.assertEqual(printer.name, "foo")
        printer.name = 1234
        self.assertEqual(printer.name, "1234")
        printer.name = []
        self.assertEqual(printer.name, "[]")

    def testBadConfig(self):
        self.assertRaises(ValueError, GutenbachPrinter, "test", {})
        self.assertRaises(ValueError, GutenbachPrinter, "test", {"hello": 1234})
        self.assertRaises(ValueError, GutenbachPrinter, "test", [])
        self.assertRaises(ValueError, GutenbachPrinter, "test", 1234)
        self.assertRaises(ValueError, GutenbachPrinter, "test", "hello")
        conf = self.testPrinterConfig.copy()
        printer = GutenbachPrinter("test", conf)
        printer.config = conf.items()
        self.assertEqual(printer.config, conf)
        conf["hello"] = "goodbye"
        self.assertNotEqual(printer.config, conf)
        printer.config = conf
        self.assertEqual(printer.config, conf)

class TestGutenbachPrinter(unittest.TestCase):

    testJobName = "unique_test_job"
    testJobRequestingUserName = "unique_test_username"
    testPrinterConfig = {
        'ipp-versions': ["1.0", "1.1"],
        'dryrun': True
        }

    def setUp(self):
        self.printer = GutenbachPrinter("test", self.testPrinterConfig)
        self.printer.start()
        while not self.printer.is_running:
            time.sleep(0.01)

    def tearDown(self):
        self.printer.stop()

    def createTestJob(self):
        job_id = self.printer.create_job(
            self.testJobRequestingUserName,
            self.testJobName)
        return job_id

    def testPrintJob(self):
        raise NotImplementedError

    def testValidateJob(self):
        raise NotImplementedError

    def testGetJobs(self):
        raise NotImplementedError

    def testPrintUri(self):
        raise NotImplementedError

    def testCreateJob(self):
        for i in xrange(2):
            countBeforeAdded = len(self.printer.jobs)
            job = self.createTestJob()
            self.assertEqual(len(self.printer.jobs) - 1, countBeforeAdded)
            self.printer.send_document(job, make_tempfile())
            self.assertTrue(job in self.printer.pending_jobs)
            self.assertFalse(job in self.printer.finished_jobs)
            self.assertEqual(self.printer.state, States.PROCESSING)

        while len(self.printer.active_jobs) > 0:
            time.sleep(0.01)
        self.assertEqual(self.printer.state, States.IDLE)

    def testPausePrinter(self):
        job = self.createTestJob()
        self.printer.send_document(job, make_tempfile())
        job = self.createTestJob()
        self.printer.send_document(job, make_tempfile())
        self.assertTrue(self.printer.is_running)
        self.assertEqual(self.printer.state, States.PROCESSING)
        self.assertFalse(self.printer.paused)

        while self.printer.current_job is None:
            time.sleep(0.01)

        self.printer.pause_printer()
        self.assertTrue(self.printer.paused)
        time.sleep(0.6)
        self.assertTrue(self.printer.current_job is not None)
        self.assertEqual(self.printer.state, States.STOPPED)

        # check that no jobs are playing
        for job_id, job in self.printer.jobs.items():
            self.assertEqual(job.is_paused, job.is_playing)

    def testResumePrinter(self):
        job = self.createTestJob()
        self.printer.send_document(job, make_tempfile())
        job = self.createTestJob()
        self.printer.send_document(job, make_tempfile())
        self.assertTrue(self.printer.is_running)
        self.assertEqual(self.printer.state, States.PROCESSING)
        self.assertFalse(self.printer.paused)

        while self.printer.current_job is None:
            time.sleep(0.01)

        self.printer.pause_printer()
        self.assertTrue(self.printer.paused)
        time.sleep(0.6)
        self.assertTrue(self.printer.current_job is not None)
        self.assertEqual(self.printer.state, States.STOPPED)

        # check that no jobs are playing
        for job_id, job in self.printer.jobs.items():
            self.assertEqual(job.is_paused, job.is_playing)

        self.printer.resume_printer()
        self.assertFalse(self.printer.paused)
        self.assertEqual(self.printer.state, States.PROCESSING)

        while len(self.printer.active_jobs) > 0:
            time.sleep(0.01)
        self.assertEqual(self.printer.state, States.IDLE)

    def testGetPrinterAttributes(self):
        raise NotImplementedError

    def testSetPrinterAttributes(self):
        raise NotImplementedError

    def testCancelJob(self):
        raise NotImplementedError

    def testSendDocument(self):
        raise NotImplementedError

    def testSendUri(self):
        raise NotImplementedError

    def testGetJobAttributes(self):
        raise NotImplementedError

    def testSetJobAttributes(self):
        raise NotImplementedError

    def testRestartJob(self):
        raise NotImplementedError

    def testPromoteJob(self):
        raise NotImplementedError

if __name__ == "__main__":
    logging.basicConfig(loglevel=logging.DEBUG)
    unittest.main()
