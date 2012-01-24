import logging
import threading
import subprocess
import time
from . import sync

# initialize logger
logger = logging.getLogger(__name__)

class Player(threading.Thread):

    def __init__(self, fh, *args, **kwargs):
        self.lock = threading.RLock()

        with self.lock:
            super(Player, self).__init__(*args, **kwargs)
            self.fh = fh
            self.player = None
            self._callback = None
            self._paused = False
            self._paused_condition = threading.Condition(self.lock)
            self._done = False
            self._done_condition = threading.Condition(self.lock)
            self._dryrun = False
            self._dryrun_time = 0.5

    @property
    @sync
    def is_playing(self):
        if self._dryrun:
            return self.ident is not None and \
                   self.isAlive() and \
                   not self.done
        else:
            return self.ident is not None and \
                   self.isAlive() and \
                   not self.done and \
                   self.player is not None and \
                   self.player.poll() is None


    # DONE
    @property
    @sync
    def done(self):
        return self._done
    @done.setter
    @sync
    def done(self, val):
        if (self._done != val):
            self._done = val
            self._done_condition.notifyAll()
    @sync
    def wait_done(self):
        """Wait for the player to finish playing.

        Requires that the main thread be started.
        """
        while not self._done:
            self._done_condition.wait()

    # PAUSED
    @property
    @sync
    def paused(self):
        return self._paused
    @paused.setter
    @sync
    def paused(self, val):
        if (self._paused != val):
            self._paused = val
            self._paused_condition.notifyAll()

    @sync
    def wait_unpaused(self):
        """Wait for the player to finish playing.

        Requires that the main thread be started.
        """
        while self._paused:
            self._paused_condition.wait()


    @property
    def callback(self):
        return self._callback
    @callback.setter
    @sync
    def callback(self, val):
        self._callback = val

    def start(self):
        super(Player, self).start()

    def run(self):
        try:
            if self.fh is None:
                raise ValueError, "file handler is None"

            logger.info("playing file '%s'" % self.fh.name)

            with self.lock:
                self.paused = False
                self.done = False

            command = ["mplayer", "-really-quiet", "-slave", self.fh.name]
            logger.info("running '%s'", " ".join(command))

            if self._dryrun:
                step = 0.01
                while self._dryrun_time > 0:
                    time.sleep(step)
                    self._dryrun_time -= step
                    self.wait_unpaused()
            else:
                with self.lock:
                    self.player = subprocess.Popen(
                        command,
                        stdin=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        stdout=subprocess.PIPE)

                # wait for mplayer to finish
                self.player.wait()

                logger.info("mplayer finished with code %d" % self.player.returncode)

                # get output from mplayer and log it
                with self.lock:
                    stderr = self.player.stderr.read()
                    stdout = self.player.stdout.read()

                if stderr.strip() != "":
                    logger.error(stderr)
                if stdout.strip() != "":
                    logger.debug(stdout)
        finally:
            with self.lock:
                if self.callback:
                    self.callback()
                self.done = True

    def mplayer_pause(self):
        # Note: Inner lock due to sleep.
        with self.lock:
            if self.is_playing:
                if not self._dryrun:
                    self.player.stdin.write("pause\n")
                self.paused = not(self.paused)
                logger.info("paused: %s", self.paused)
            else:
                logger.warning("trying to pause non-playing job")

    def mplayer_stop(self):
        # Note: Inner lock due to join.
        with self.lock:
            if self.is_playing:
                if not self._dryrun:
                    self.player.stdin.write("quit\n")
                else:
                    self._dryrun_time = 0.0
                self.paused = False
                logger.info("stopped")
            else:
                logger.warning("trying to stop non-playing job")
        self.join()

