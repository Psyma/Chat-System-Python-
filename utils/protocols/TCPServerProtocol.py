import asyncio
from collections.abc import Callable

class TCPServerProtocol(asyncio.Protocol):
    def __init__(self, 
            connection_made_callback: Callable[[asyncio.BaseTransport]], 
            data_received_callback: Callable[[bytes]], 
            connection_lost_callback: Callable[[asyncio.BaseTransport]]) -> None:
        asyncio.Protocol.__init__(self)
        self.connection_made_callback = connection_made_callback
        self.data_received_callback = data_received_callback
        self.connection_lost_callback = connection_lost_callback

    def connection_made(self, transport: asyncio.BaseTransport) -> None:    
        self.transport = transport
        self.connection_made_callback(self.transport)  

    def data_received(self, data: bytes) -> None: 
        self.data_received_callback(data, self.transport) 
    
    def connection_lost(self, exc: Exception) -> None:
        self.connection_lost_callback(self.transport) 