from __future__ import annotations 

import cv2

from queue import Queue
from threading import Thread, Lock 

class VideoStream(object):
    def __init__(self, source: str | int) -> None:
        self.Q = Queue()
        self.stopped = False
        self.read_lock = Lock()
        self.stream = cv2.VideoCapture(source)
        
        assert self.stream.isOpened(), "Unable to open source"
        
    def start(self):
        self.t = Thread(target=self.update, args=())
        self.t.daemon = True
        self.t.start()

    def stop(self):
        if self.stopped:
            return
        self.stopped = True
        if self.t.is_alive():
            self.t.join()

    def getitem(self):
        if not self.Q.empty():
            return self.Q.get()
        return None

    def update(self):
        while not self.stopped:
            ret, frame = self.stream.read()
            if not ret:
                self.Q.put(frame)