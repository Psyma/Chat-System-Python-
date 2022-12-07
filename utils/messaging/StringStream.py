import pickle 
import asyncio 

from utils.models.Message import Message 
from concurrent.futures import ThreadPoolExecutor
from threading import Thread 

class StringStream(object):
    def __init__(self) -> None:  
        self.stopped = False
        self.mssgreceived = True
        self.Q = asyncio.Queue() 

        def run():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(self.fetcher())
            self.stopped = True
            loop.close()

        t = Thread(target=run, args=())
        t.start()

    async def fetcher(self):
        while not self.stopped:  
            if not self.Q.empty() and self.mssgreceived:
                self.mssgreceived = False
                task = await self.Q.get()
                task()
            await asyncio.sleep(0.01) 

    def send(self, data: Message, transport: asyncio.Transport):
        def task(data: Message, transport: asyncio.Transport):
            data = pickle.dumps(data)   
            transport.write(data)   
            self.Q.task_done() 

        self.Q.put_nowait(lambda: task(data, transport))