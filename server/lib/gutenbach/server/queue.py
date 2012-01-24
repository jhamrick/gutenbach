import threading
from . import sync

class InterruptException(Exception):
    pass

class PausingQueue(object):
    def __init__(self, lock=None):
        self._items = []
        if lock:
            self.lock = lock
        else:
            self.lock = threading.RLock()
        self._ready = threading.Condition(self.lock)
        self._interrupted = False
        self._paused = False

    @sync
    def interrupt(self):
        self._interrupted = True
        self._ready.notifyAll()

    def wait_ready(func):
        @sync
        def do(self, *args, **kwargs):
            while self.paused or not self._items:
                self._ready.wait()
                if self._interrupted:
                    raise InterruptException()
            return func(self, *args, **kwargs)
        return do

    def notify_ready(func):
        @sync
        def do(self, *args, **kwargs):
            if not self.paused:
                ret = func(self, *args, **kwargs)
                self._ready.notifyAll()
            return ret
        return do

    @property
    @sync
    def paused(self):
        return self._paused
    @paused.setter
    @sync
    def paused(self, val):
        self._paused = val
        if not self._paused:
            self._ready.notifyAll()


    @wait_ready
    def pop(self):
        return self._items.pop(0)

    @notify_ready
    def push(self, item):
        self._items.insert(0, item)

    @notify_ready
    def append(self, item):
        self._items.append(item)

    @notify_ready
    def insert(self, index, item):
        self._items.insert(index, item)

    @sync
    def promote(self, item):
        self.move(0, item)

    @sync
    def move(self, index, item):
        self._items.remove(item)
        self._items.insert(index, item)

    @sync
    def copy(self):
        return self._items[:]

    @sync
    def empty(self):
        return not bool(self._items)

    @sync
    def __len__(self):
        return len(self._items)

    @sync
    def __contains__(self, val):
        return val in self._items
