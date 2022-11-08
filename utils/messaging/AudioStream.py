import pyaudio
import webrtcvad  

from queue import Queue
from threading import Thread, Lock

class AudioStream(object):
    def __init__(self, ms: int, rate: int, audio, format: int, webrtcvad_agrr: int, channels: int):
        self.Q = Queue(maxsize=0)
        self.ms = ms
        self.rate = rate
        self.format = format
        self.channels = channels 
        self.chunk = int((ms * rate) / 1000)
        self.vad = webrtcvad.Vad(webrtcvad_agrr) 
        self.stream = audio.open(format=self.format, channels=self.channels, rate=self.rate, input=True, frames_per_buffer=self.chunk)  
         
        self.stopped = False
        self.read_lock = Lock()
    
    def get_sample_size(self):
        return self.audio.get_sample_size(self.format)
        
    def start(self):
        self.t = Thread(target=self.update, args=())
        self.t.daemon = True
        self.t.start()
        return self

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
        frames = []
        while not self.stopped:
            self.read_lock.acquire()
            data = self.stream.read(self.chunk)  
            is_speech = self.vad.is_speech(data, self.rate) 
            if is_speech: 
                frames.append(data)
            else:
                if len(frames): 
                    self.Q.put(b''.join(frames))    
                    frames = []  
            self.read_lock.release()   

    
    