import asyncio
from collections.abc import Callable

class TCPClientProtocol(asyncio.Protocol):
    def __init__(self, 
            connection_made_callback: Callable[[asyncio.BaseTransport]], 
            data_received_callback: Callable[[bytes]]) -> None:
        super().__init__() 
        self.connection_made_callback = connection_made_callback
        self.data_received_callback = data_received_callback
        
    def connection_made(self, transport: asyncio.BaseTransport) -> None:
        self.connection_made_callback(transport)  

    def data_received(self, data: bytes) -> None:
        self.data_received_callback(data) 

    def connection_lost(self, exc: Exception) -> None:
        asyncio.get_event_loop().stop() 