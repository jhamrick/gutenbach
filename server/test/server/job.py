from gutenbach.server import GutenbachJob
from gutenbach.server import errors
from gutenbach.ipp import JobStates as States
import unittest
import tempfile

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
        self.assertFalse(self.job.is_playing)
        self.assertFalse(self.job.is_ready)
        self.assertFalse(self.job.is_finished)

    def testSpool(self):
        fh = make_tempfile()
        self.job.spool(fh)
        self.assertEqual(self.job.document, fh.name)
        self.assertNotEqual(self.job.player, None)
        self.assertEqual(self.job.creator, "")
        self.assertEqual(self.job.state, States.PENDING)
        # This should fail, because the id hasn't been set
        self.assertFalse(self.job.is_ready)
        self.job.id = 1
        self.assertTrue(self.job.is_ready)
        self.job.abort()
    def testPlay(self):
        self.assertRaises(errors.InvalidJobStateException, self.job.play)
    def testPause(self):
        self.assertRaises(errors.InvalidJobStateException, self.job.pause)
    def testCancel(self):
        self.job.cancel()
        self.assertEqual(self.job.state, States.CANCELLED)
    def testAbort(self):
        self.job.abort()
        self.assertEqual(self.job.state, States.ABORTED)

class TestBadGutenbachJob(unittest.TestCase):

    def testBadJobId(self):
        self.job = GutenbachJob(job_id=-2)
        self.assertEqual(self.job.id, -1)
        self.job.id = -2
        self.assertEqual(self.job.id, -1)

    def testBadCreator(self):
        self.job = GutenbachJob(job_id=1, creator=12345)
        self.assertEqual(self.job.creator, "12345")
        self.job.creator = None
        self.assertEqual(self.job.creator, "")
        self.job.creator = []
        self.assertEqual(self.job.creator, "[]")

    def testBadName(self):
        self.job = GutenbachJob(job_id=1, creator="foo", name=12345)
        self.assertEqual(self.job.name, "12345")
        self.job.name = None
        self.assertEqual(self.job.name, "")
        self.job.name = []
        self.assertEqual(self.job.name, "[]")

if __name__ == "__main__":
    unittest.main()
