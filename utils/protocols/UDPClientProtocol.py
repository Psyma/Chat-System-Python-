import asyncio
from collections.abc import Callable

class UDPClientProtocol(asyncio.DatagramProtocol):
    def __init__(self, 
            connection_made_callback: Callable[[asyncio.DatagramTransport]], 
            datagram_received_callback: Callable[[bytes, tuple]]) -> None:
        super().__init__()
        self.connection_made_callback = connection_made_callback
        self.datagram_received_callback = datagram_received_callback

    def connection_made(self, transport: asyncio.DatagramTransport) -> None:
        self.connection_made_callback(transport) 
    
    def datagram_received(self, data: bytes, addr: tuple) -> None:
        self.datagram_received_callback(data, addr) 

    def error_received(self, exc: Exception) -> None:
        print('Error received:', exc) 

    def connection_lost(self, exc: Exception) -> None:
        print('UDP Client closed the connection')