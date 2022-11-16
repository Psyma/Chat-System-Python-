import pickle
import asyncio 

from datetime import datetime  
from utils.models.Message import Message
from utils.models.MessageType import MessageType
from concurrent.futures import ThreadPoolExecutor 
from utils.protocols.TCPServerProtocol import TCPServerProtocol
from utils.protocols.UDPServerProtocol import UDPServerProtocol

class Server(object):
    def __init__(self, host: str = '127.0.0.1', tcp_port: int = 9999, udp_port: int = 6666) -> None:
        self.host: str = host
        self.tcp_port: int = tcp_port
        self.udp_port: int = udp_port
        self.tcp_transport = None
        self.transport_map: dict[tuple, asyncio.BaseTransport] = {}
        self.sender_peername_map: dict[str, tuple] = {}
        self.peername_peername_map: dict[str, tuple] = {}
        self.udp_transport_map: dict[tuple, asyncio.DatagramTransport] = {}
        self.udp_peername_map: dict[str, tuple] = {}

        self.server_logs: list[str] = []

    async def __connected(self): 
        for peername1, transport in list(self.transport_map.items()):
            for sender, peername2, in list(self.sender_peername_map.items()):  
                if peername1 != peername2: 
                    data = Message(sender=sender, timestamp=datetime.now().strftime('%m/%d/%Y %H:%M:%S'), type=MessageType.CONNECTED)  
                    transport.write(pickle.dumps(data)) 
                    await asyncio.sleep(0.01)

    async def __disconnected(self, transport: asyncio.BaseTransport):
        sender = None
        peername = transport.get_extra_info('peername')
        timestamp = datetime.now().strftime('%m/%d/%Y %H:%M:%S')
        for sender1, peername1 in list(self.sender_peername_map.items()):
            if peername == peername1:
                sender = sender1
                del self.sender_peername_map[sender1] 
                self.server_logs.append("[{}] {} has logged out".format(timestamp, sender))
                break
        
        for key_peername, val_peername in list(self.peername_peername_map.items()):
            if peername == key_peername:
                del self.peername_peername_map[peername]
                self.server_logs.append("[{}] {} disconnected from the server".format(timestamp, peername))
                break

        del self.transport_map[peername]
        for peername, transport in list(self.transport_map.items()):
            if sender != None:
                data = Message(sender=sender, timestamp=datetime.now().strftime('%m/%d/%Y %H:%M:%S'), type=MessageType.DISCONNECTED) 
                transport.write(pickle.dumps(data)) 
            await asyncio.sleep(0.01)   

    def __tcp_connection_made(self, transport: asyncio.BaseTransport):
        peername = transport.get_extra_info('peername')
        sockname = transport.get_extra_info('sockname') 
        self.transport_map[peername] = transport    
        
    def __tcp_data_received(self, data: bytes):
        data: Message = pickle.loads(data) 
        timestamp = datetime.now().strftime('%m/%d/%Y %H:%M:%S')
    
        if data.type == MessageType.CONNECTED:
            self.peername_peername_map[data.sender_peername] = data.sender_peername   
            asyncio.ensure_future(self.__connected()) 
            self.server_logs.append("[{}] {} connected to the server".format(timestamp, data.sender_peername))
        elif data.type == MessageType.MESSAGE: 
            peername = self.sender_peername_map[data.receiver] 
            data = Message(
                image=data.image, 
                image_index=data.image_index, 
                image_len=data.image_len, 
                audio=data.audio, 
                message=data.message, 
                sender=data.sender, 
                receiver=data.receiver, 
                timestamp=timestamp, 
                type=data.type
            )  
            self.transport_map[peername].write(pickle.dumps(data))
            self.server_logs.append("[{}] {} sent message to {}".format(timestamp, data.sender, data.receiver))
        elif data.type == MessageType.REGISTER:
            response = Message(
                message="you are registered",
                type=MessageType.LOGIN
            )  
            self.transport_map[data.sender_peername].write(pickle.dumps(response)) 
        elif data.type == MessageType.LOGIN:
            # check database is credentials is correct or not  
            self.sender_peername_map[data.sender] = data.sender_peername   
            self.server_logs.append("[{}] {} has logged in".format(timestamp, data.sender))
            response = Message(
                message="user already exists",
                type=MessageType.LOGIN
            )  
            self.transport_map[data.sender_peername].write(pickle.dumps(response)) 

    def __tcp_connection_lost(self, transport: asyncio.BaseTransport):
         asyncio.ensure_future(self.__disconnected(transport))

    def __udp_connection_made(self, transport: asyncio.DatagramTransport):
        self.udp_transport = transport 

    def __udp_datagram_received(self, data: bytes, addr: tuple):
        data: Message = pickle.loads(data) 

        if data.type == MessageType.CONNECTED:
            self.udp_transport_map[data.sender_peername] = self.udp_transport
            self.udp_peername_map[data.sender] = data.sender_peername
        elif data.type == MessageType.MESSAGE:  
            self.udp_transport_map[self.udp_peername_map[data.sender]].sendto(pickle.dumps(data), self.udp_peername_map[data.receiver])  
    
    def start(self):
        self.loop = asyncio.get_event_loop()
        self.loop.set_default_executor(ThreadPoolExecutor(1000))
        coro = self.loop.create_server(lambda: TCPServerProtocol(self.__tcp_connection_made, self.__tcp_data_received, self.__tcp_connection_lost), self.host, self.tcp_port)
        server = self.loop.run_until_complete(coro)
    
        connect = self.loop.create_datagram_endpoint(lambda: UDPServerProtocol(self.__udp_connection_made, self.__udp_datagram_received), local_addr=(self.host, self.udp_port))
        transport, protocol = self.loop.run_until_complete(connect)
        self.loop.run_forever()

    def stop(self):
        self.loop.call_soon_threadsafe(self.loop.stop)  