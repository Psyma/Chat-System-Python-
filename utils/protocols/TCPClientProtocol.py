import asyncio
from collections.abc import Callable
from twisted.internet import reactor, protocol
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
 
class EchoClient(protocol.Protocol):
    """Once connected, send a message, then print the result."""
    def __init__(self, 
            connection_made_callback: Callable[[asyncio.BaseTransport]], 
            data_received_callback: Callable[[bytes]],
            connection_lost_callback: Callable[[asyncio.BaseTransport]]) -> None:
        super().__init__() 
        self.connection_made_callback = connection_made_callback
        self.data_received_callback = data_received_callback
        self.connection_lost_callback = connection_lost_callback 
        self.transport = None

    def connectionMade(self):
        self.connection_made_callback(self.transport)
        #self.transport.write(b"hello, world!")
    
    def dataReceived(self, data):
        "As soon as any data is received, write it back."
        self.data_received_callback(data)
        #print("Server said:", data)
        #self.transport.loseConnection()
    
    def connectionLost(self, reason):
        print("connection lost")