import pyaudio   

from queue import Queue 
from threading import Thread, Lock

class AudioStream(object):
    def __init__(self, ms: int, rate: int, audio: pyaudio.PyAudio, format: int, channels: int):
        self.Q = Queue(maxsize=0)
        self.ms = ms
        self.rate = rate
        self.format = format
        self.channels = channels 
        self.chunk = int((ms * rate) / 1000)   
        self.play = audio.open(format=self.format, channels=self.channels, rate=self.rate, output=True, frames_per_buffer=self.chunk)
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

    def listen(self, data):
        self.play.write(data) 
        
    def update(self):  
        while not self.stopped:
            self.read_lock.acquire()
            data = self.stream.read(self.chunk)    
            self.Q.put(data) 
            self.read_lock.release()   
        
        self.stream.close()
        self.play.close()

if __name__ == "__main__":
    MS = 30
    RATE = 48000
    AUDIO = pyaudio.PyAudio()
    FORMAT = pyaudio.paInt16
    WEBRTCVAD = 1
    CHANNELS = 1

    audio = AudioStream(MS, RATE, AUDIO, FORMAT, CHANNELS)
    audio.start()  
    
    while True:
        try:
            data = audio.getitem()
            if type(data) != type(None): 
                audio.listen(data=data)
        except KeyboardInterrupt:
            break