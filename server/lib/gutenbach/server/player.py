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

    @property
    def is_playing(self):
        with self.lock:
            playing = self.player and self.player.poll() is None
        return playing

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
        with self.lock:
            if self.callback:
                self.callback()

    def mplayer_play(self):
        logger.info("playing file '%s'" % self.fh.name)
        
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
                self.player.stdin.write("pause\n")
                
    def mplayer_stop(self):
        with self.lock:
            if self.is_playing:
                self.player.stdin.write("quit\n")
