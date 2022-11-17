import pickle
import asyncio 
import logging

from datetime import datetime  
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from utils.models.MessageType import MessageType
from concurrent.futures import ThreadPoolExecutor

from utils.models.Message import Message
from utils.models.UserModel import UserModel
from utils.models.ChatsModel import ChatsModel
from utils.models.StatusModel import StatusModel
from utils.database.UserDatabase import UserDatabase
from utils.database.ChatsDatabase import ChatsDatabase
from utils.database.StatusDatabase import StatusDatabase
from utils.protocols.TCPServerProtocol import TCPServerProtocol
from utils.protocols.UDPServerProtocol import UDPServerProtocol

class Server(object):
    def __init__(self, host: str = '127.0.0.1', tcp_port: int = 9999, udp_port: int = 6666) -> None: 
        self.host: str = host
        self.tcp_port: int = tcp_port
        self.udp_port: int = udp_port
        self.tcp_transport = None
        self.transport_map: dict[tuple, asyncio.Transport] = {}
        self.sender_peername_map: dict[str, tuple] = {}
        self.peername_peername_map: dict[str, tuple] = {}
        self.udp_transport_map: dict[tuple, asyncio.DatagramTransport] = {}
        self.udp_peername_map: dict[str, tuple] = {}
        self.server_logs: list[str] = []

        logging.disable(logging.WARNING)
        engine = create_engine('sqlite:///database.sqlite', echo=True)
        Session = sessionmaker(bind=engine)
        session = Session()
        
        self.userdb = UserDatabase(session=session, engine=engine)
        self.chatsdb = ChatsDatabase(session=session, engine=engine)
        self.statusdb = StatusDatabase(session=session, engine=engine) 

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
                fields = {
                    'isonline': 0
                }
                self.statusdb.update(sender, **fields) 
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
            fields = {
                'isonline': 1,
                'new_message': 1,
                'message': data.message
            }
            chats = ChatsModel(
                sender=data.sender,
                receiver=data.receiver,
                message=data.message,
                timestamp=data.timestamp,
                peername=str(data.sender_peername)
            )
            self.chatsdb.create(chats)
            self.statusdb.update(data.sender, **fields)

            for status in self.statusdb.list():
                if status.username == data.receiver:
                    if status.isonline:
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
            user = UserModel(
                username=data.register_username,
                password=data.register_password,
                firstname=data.register_firstname,
                middlename=data.register_middlename,
                lastname=data.register_lastname
            )
            status = StatusModel(
                username=data.register_username,
                isonline=0,
                message=data.message,
                new_message=0,
                fullname="{} {} {}".format(data.register_firstname, data.register_middlename, data.register_lastname)
            )
            if type(self.userdb.get(data.register_username)) == type(None):
                self.userdb.create(user)
                self.statusdb.create(status)
                response = Message( 
                    message="you are registered",
                    type=MessageType.LOGIN
                ) 
            else:
                response = Message( 
                    message="user already exists",
                    type=MessageType.LOGIN
                )
            self.transport_map[data.sender_peername].write(pickle.dumps(response)) 
        elif data.type == MessageType.LOGIN: 
            if type(self.userdb.get(data.sender)) != type(None):
                fields = {
                    'isonline': 1
                }
                self.statusdb.update(data.sender, **fields)
                self.sender_peername_map[data.sender] = data.sender_peername   
                self.server_logs.append("[{}] {} has logged in".format(timestamp, data.sender))

                status_results = self.statusdb.list()
                chats_results = self.chatsdb.list()
                status_response = Message(
                    connected_users=status_results,
                    type=MessageType.CONNECTED_USERS
                )
                chats_response = Message(
                    sender=data.sender,
                    history_messages=chats_results,
                    type=MessageType.CHATS_HISTORY
                ) 

                for peername_key, peername_value in self.peername_peername_map.items(): 
                    self.transport_map[peername_key].write(pickle.dumps(status_response)) 
                    if self.sender_peername_map[data.sender] == peername_key:
                        self.transport_map[peername_key].write(pickle.dumps(chats_response)) 
            else:
                response = Message(
                    message="Incorrect username or password",
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
        for user in self.userdb.list():
            fields = {
                'isonline': 0,
            }
            self.statusdb.update(user.username, **fields)
        self.loop.call_soon_threadsafe(self.loop.stop)  