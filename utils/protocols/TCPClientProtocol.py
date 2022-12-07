import asyncio
from collections.abc import Callable

class TCPClientProtocol(asyncio.Protocol):
    def __init__(self, 
            connection_made_callback: Callable[[asyncio.BaseTransport]], 
            data_received_callback: Callable[[bytes]],
            connection_lost_callback: Callable[[asyncio.BaseTransport]]) -> None:
        super().__init__() 
        self.connection_made_callback = connection_made_callback
        self.data_received_callback = data_received_callback
        self.connection_lost_callback = connection_lost_callback 

    def connection_made(self, transport: asyncio.transports.BaseTransport) -> None:
        self.connection_made_callback(transport)  

    def data_received(self, data: bytes) -> None:
        self.data_received_callback(data) 

    def connection_lost(self, exc: Exception) -> None: 
        self.connection_lost_callback() 
        asyncio.get_event_loop().stop() 