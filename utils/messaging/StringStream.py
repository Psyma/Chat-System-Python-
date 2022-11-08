import pickle
import socket
import asyncio

from utils.models.Message import Message

class StringStream(object):
    def __init__(self) -> None:
        pass

    def send(self, data: Message, transport: asyncio.Transport, size: int = None, dst: tuple = None):
        if size == None and dst == None:
            transport.write(pickle.dumps(data))
        else:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) 
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, size)
            self.socket.sendto(pickle.dumps(data), dst) 