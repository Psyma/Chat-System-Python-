import pickle 
import asyncio 

from utils.models.Message import Message   

class StringStream(object):
    def __init__(self) -> None:  
        pass

    def send(self, data: Message, transport: asyncio.Transport):
        data = pickle.dumps(data)
        transport.write(data)