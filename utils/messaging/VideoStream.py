from __future__ import annotations 

import cv2 
import socket
import pickle 
import base64
import datetime

from queue import Queue
from threading import Thread, Lock 
from utils.models.Message import Message
from utils.models.MessageType import MessageType

class VideoStream(object):
    def __init__(self, source: str | int) -> None:
        self.Q = Queue()
        self.stream = None
        self.source: str | int = source
        self.stopped: bool = False
        self.read_lock: Lock = Lock() 
        
    def start(self):
        self.stream = cv2.VideoCapture(self.source)
        assert self.stream.isOpened(), "Unable to open source"
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

if __name__ == "__main__":
    video = VideoStream(0) 

    while True:
        data = video.getitem()
        if type(data) != type(None):
            image = video.getitem()
            cv2.imshow('window', image)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
