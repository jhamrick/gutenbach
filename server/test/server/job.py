from gutenbach.server import GutenbachJob
from gutenbach.server import errors
from gutenbach.ipp import JobStates as States
import unittest
import tempfile
import sys

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
        
class TestGoodGutenbachJob(unittest.TestCase):

    def setUp(self):
        self.job = GutenbachJob(job_id=1, creator="foo", name="test")

    def testSpool(self):
        fh = make_tempfile()
        self.assertTrue(self.job.is_valid)
        self.assertFalse(self.job.is_ready)
        self.job.spool(fh)
        self.assertTrue(self.job.is_ready)
        
        # Verify various properties
        self.assertEqual(self.job.document, fh.name)
        self.assertNotEqual(self.job.player, None)
        self.assertEqual(self.job.state, States.PENDING)

        self.job.abort()


if __name__ == "__main__":
    unittest.main()
