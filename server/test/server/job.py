from gutenbach.server import GutenbachJob
from gutenbach.server import errors
from gutenbach.ipp import JobStates as States
import unittest
import tempfile
import sys
import time
import logging

def make_tempfile():
    fh = tempfile.NamedTemporaryFile()
    fh.write("test\n")
    fh.seek(0)
    return fh

class TestEmptyGutenbachJob(unittest.TestCase):

    def setUp(self):
        self.job = GutenbachJob()

    def testPlayer(self):
        self.assertEqual(self.job.player, None)
    def testId(self):
        self.assertEqual(self.job.id, -1)
    def testCreator(self):
        self.assertEqual(self.job.creator, "")
    def testName(self):
        self.assertEqual(self.job.name, "")
    def testSize(self):
        self.assertEqual(self.job.size, 0)
    def testState(self):
        self.assertEqual(self.job.state, States.HELD)
    def testPriority(self):
        self.assertEqual(self.job.priority, 1)

    def testStateProperties(self):
        self.assertFalse(self.job.is_valid)
        self.assertFalse(self.job.is_ready)
        self.assertFalse(self.job.is_playing)
        self.assertFalse(self.job.is_paused)
        self.assertFalse(self.job.is_done)
        self.assertFalse(self.job.is_completed)
        self.assertFalse(self.job.is_cancelled)
        self.assertFalse(self.job.is_aborted)

    def testSpool(self):
        fh = tempfile.NamedTemporaryFile()
        self.assertRaises(errors.InvalidJobStateException, self.job.spool, fh)
        fh.close()
    def testPlay(self):
        self.assertRaises(errors.InvalidJobStateException, self.job.play)
    def testPause(self):
        self.assertRaises(errors.InvalidJobStateException, self.job.pause)
    def testCancel(self):
        self.job.cancel()
        self.assertTrue(self.job.is_cancelled)
        self.assertEqual(self.job.state, States.CANCELLED)
    def testAbort(self):
        self.job.abort()
        self.assertTrue(self.job.is_aborted)
        self.assertEqual(self.job.state, States.ABORTED)

class TestBadGutenbachJob(unittest.TestCase):

    def testBadJobId(self):
        job = GutenbachJob(job_id=-2)
        self.assertEqual(job.id, -1)
        job.id = -2
        self.assertEqual(job.id, -1)

    def testBadCreator(self):
        job = GutenbachJob(
            job_id=1,
            creator=12345)
        self.assertEqual(job.creator, "12345")
        job.creator = None
        self.assertEqual(job.creator, "")
        job.creator = []
        self.assertEqual(job.creator, "[]")

    def testBadName(self):
        job = GutenbachJob(
            job_id=1,
            creator="foo",
            name=12345)
        self.assertEqual(job.name, "12345")
        job.name = None
        self.assertEqual(job.name, "")
        job.name = []
        self.assertEqual(job.name, "[]")

    def testBadPriority(self):
        job = GutenbachJob(
            job_id=1,
            creator="foo",
            name="test",
            priority=-1)
        self.assertEqual(job.priority, 1)
        job.priority = 0
        self.assertEqual(job.priority, 1)
        job.priority = 1
        self.assertEqual(job.priority, 1)
        job.priority = sys.maxint
        self.assertEqual(job.priority, sys.maxint)
        job.priority = "hello"
        self.assertEqual(job.priority, 1)
        job.priority = []
        self.assertEqual(job.priority, 1)

    def testBadDocument(self):
        job = GutenbachJob(
            job_id=1,
            creator="foo",
            name="test",
            priority=1)
        self.assertRaises(errors.InvalidDocument, job.spool, "hello")
        self.assertRaises(errors.InvalidDocument, job.spool, [])
        self.assertRaises(errors.InvalidDocument, job.spool, 12345)

        fh = make_tempfile()
        job = GutenbachJob(
            job_id=1,
            creator="foo",
            name="test",
            priority=1,
            document=fh)
        self.assertRaises(errors.InvalidJobStateException, job.spool, "hello")
        self.assertRaises(errors.InvalidJobStateException, job.spool, [])
        self.assertRaises(errors.InvalidJobStateException, job.spool, 12345)

class TestOperations(unittest.TestCase):

    def setUp(self):
        fh = make_tempfile()
        self.job = GutenbachJob(
            job_id=1,
            creator="foo",
            name="test",
            priority=1,
            document=fh)
        self.job.player._dryrun = True

    def testPlay(self):
        self.job.play()
        self.assertTrue(self.job.is_playing)

        while self.job.is_playing:
            time.sleep(0.1)

        self.assertTrue(self.job.is_done)
        self.assertTrue(self.job.is_completed)
        self.assertFalse(self.job.is_aborted)
        self.assertFalse(self.job.is_cancelled)

    def testPause(self):
        self.job.play()
        self.assertTrue(self.job.is_playing)
        self.assertFalse(self.job.is_paused)

        self.job.pause()
        self.assertTrue(self.job.is_playing)
        self.assertTrue(self.job.is_paused)

        time.sleep(0.6)
        self.assertTrue(self.job.is_playing)
        self.assertTrue(self.job.is_paused)

        self.job.pause()
        self.assertTrue(self.job.is_playing)
        self.assertFalse(self.job.is_paused)
        
        while self.job.is_playing:
            time.sleep(0.1)
            
        self.assertTrue(self.job.is_done)
        self.assertTrue(self.job.is_completed)
        self.assertFalse(self.job.is_aborted)
        self.assertFalse(self.job.is_cancelled)

    def testCancel(self):
        self.job.play()
        self.assertTrue(self.job.is_playing)
        self.assertFalse(self.job.is_cancelled)

        self.job.cancel()
        self.assertFalse(self.job.is_playing)
        self.assertTrue(self.job.is_done)
        self.assertTrue(self.job.is_cancelled)
        self.assertFalse(self.job.is_aborted)

    def testAbort(self):
        self.job.play()
        self.assertTrue(self.job.is_playing)
        self.assertFalse(self.job.is_aborted)

        self.job.abort()
        self.assertFalse(self.job.is_playing)
        self.assertTrue(self.job.is_done)
        self.assertFalse(self.job.is_cancelled)
        self.assertTrue(self.job.is_aborted)

    def testRestart(self):
        # XXX: Todo
        pass

if __name__ == "__main__":
    logging.basicConfig(loglevel=logging.CRITICAL)
    unittest.main()
