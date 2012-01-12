import logging
import threading
import subprocess
import time

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
            self._done = False
            self._dryrun = False
            self._dryrun_time = 0.5

    @property
    def is_playing(self):
        with self.lock:
            if self._dryrun:
                playing = self.isAlive() and not self.is_done
            else:
                playing = self.isAlive() and \
                          not self.is_done and \
                          self.player is not None and \
                          self.player.poll() is None
        return playing

    @property
    def is_paused(self):
        with self.lock:
            paused = self.is_playing and self._paused
        return paused

    @property
    def is_done(self):
        return self._done

    @property
    def callback(self):
        return self._callback
    @callback.setter
    def callback(self, val):
        with self.lock:
            self._callback = val

    def run(self):
        if self.fh is None:
            raise ValueError, "file handler is None"
        
        self.mplayer_play()
        self._done = True
        with self.lock:
            if self.callback:
                self.callback()

    def mplayer_play(self):
        if not self.isAlive():
            return
        
        logger.info("playing file '%s'" % self.fh.name)
        self._paused = False

        if self._dryrun:
            step = 0.01
            while self._dryrun_time > 0:
                time.sleep(step)
                self._dryrun_time -= step
                while self.is_paused:
                    time.sleep(0.01)
            return
        
        # open mplayer
        with self.lock:
            self.player = subprocess.Popen(
                "/usr/bin/mplayer -really-quiet -slave %s" % self.fh.name,
                shell=True,
                stdin=subprocess.PIPE,
                stderr=subprocess.PIPE,
                stdout=subprocess.PIPE)

        # wait for mplayer to finish
        while True:
            with self.lock:
                playing = self.is_playing
            if not playing:
                break
            time.sleep(0.1)

        logger.info("mplayer finished with code %d" % self.player.returncode)
        
        # get output from mplayer and log it
        with self.lock:
            stderr = self.player.stderr.read()
            stdout = self.player.stdout.read()
            
        if stderr.strip() != "":
            logger.error(stderr)
        if stdout.strip() != "":
            logger.debug(stdout)

    def mplayer_pause(self):
        with self.lock:
            if self.is_playing:
                if not self._dryrun:
                    self.player.stdin.write("pause\n")
                self._paused = not(self._paused)
                logger.info("paused: %s", self.is_paused)
            else:
                logger.warning("trying to pause non-playing job")
                
    def mplayer_stop(self):
        with self.lock:
            if self.is_playing:
                if not self._dryrun:
                    self.player.stdin.write("quit\n")
                else:
                    self._dryrun_time = 0.0
                logger.info("stopped")
            else:
                logger.warning("trying to stop non-playing job")
