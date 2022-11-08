import pickle
import socket
import asyncio

from utils.models.Message import Message

class StringStream(object):
    def __init__(self) -> None:
        pass

    def send(self, data: Message, transport: asyncio.Transport):
        transport.write(pickle.dumps(data))