import os
import sys
import pickle
import asyncio  
import struct
import time

CUR_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.join(CUR_DIR, '..')
sys.path.append(ROOT_DIR)

from queue import Queue
from datetime import datetime    
from utils.models.MessageType import MessageType
from concurrent.futures import ThreadPoolExecutor 

from utils.models.Message import Message
from utils.database.Repository import Repository, User, Status, Chats
from utils.protocols.TCPServerProtocol import TCPServerProtocol
from utils.protocols.UDPServerProtocol import UDPServerProtocol  

class Server():
    def __init__(self, host: str = '127.0.0.1', tcp_port: int = 9999, udp_port: int = 6666) -> None: 
        self.host: str = host
        self.filebuffer = bytearray()
        self.repo = Repository()
        self.buffer = bytearray() 
        self.tcp_port: int = tcp_port
        self.udp_port: int = udp_port
        self.server_logs: list[str] = []  
        self.buffer_map: dict[tuple, bytearray] = {}
        self.udp_peername_map: dict[str, tuple] = {}
        self.filebuffersize_map: dict[tuple, int] = {}
        self.sender_peername_map: dict[str, tuple] = {} 
        self.transport_map: dict[tuple, asyncio.Transport] = {}
        self.udp_transport_map: dict[tuple, asyncio.DatagramTransport] = {}
        self.images_path = ROOT_DIR + "/images"
        self.uploads_path = ROOT_DIR + "/uploads" 

        if not os.path.exists(self.images_path):
            os.mkdir(self.images_path)
        if not os.path.exists(self.uploads_path):
            os.mkdir(self.uploads_path)

        for user in self.repo.list(User):
            fields = {
                'isonline': 0,
            }
            self.repo.update(user.username, Status, **fields)  

    async def disconnected(self, transport: asyncio.BaseTransport):
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
                self.repo.update(sender, Status, **fields) 
                self.server_logs.append("[{}] {} has logged out".format(timestamp, sender))
                break 

        del self.transport_map[peername]
        for peername, transport in list(self.transport_map.items()):
            if sender != None:
                data = Message(sender=sender, timestamp=datetime.now().strftime('%m/%d/%Y %H:%M:%S'), type=MessageType.DISCONNECTED) 
                transport.write(pickle.dumps(data)) 

        await asyncio.sleep(1)   
    
    async def connected(self, data: Message):
        fields = {
            'isonline': 1
        }
        self.repo.update(data.sender, Status, **fields)
        self.sender_peername_map[data.sender] = data.sender_peername   
        self.server_logs.append("[{}] {} has logged in".format(data.timestamp, data.sender))
        status_results = self.repo.list(Status)
        chat_results = self.repo.list(Chats) 
        status_response = Message(
            connected_users=status_results,
            type=MessageType.CONNECTED_USERS
        )
        chats_response = Message(
            sender=data.sender,
            history_messages=chat_results,
            type=MessageType.CHATS_HISTORY
        )
        
        for sender, peername in self.sender_peername_map.items():
            self.transport_map[peername].write(pickle.dumps(status_response)) 
            if data.sender == sender:
                self.transport_map[peername].write(pickle.dumps(chats_response))
       
        await asyncio.sleep(1)   
    
    async def message(self, data: Message):                
        fields = {
            'isonline': 1,
            'new_message': 1,
            'message': data.message
        } 
        chats = {
            'sender': data.sender,
            'receiver': data.receiver,
            'filename': data.filename, 
            'file_reference': data.file_reference,
            'message': data.message,
            'timestamp': data.timestamp,
            'peername': str(data.sender_peername)
        }

        self.repo.save(Chats, **chats) 
        self.repo.update(data.sender, Status, **fields) 
        self.server_logs.append("[{}] {} sent message to {}".format(data.timestamp, data.sender, data.receiver))
        await self.sendmessage(data)  

    async def register(self, data: Message):
        success = False
        user = self.repo.find(data.register_username, User)
        if type(user) == type(None):
            success = True
            user_model = {
                'username': data.register_username,
                'password': data.register_password,
                'firstname': data.register_firstname,
                'middlename': data.register_middlename,
                'lastname': data.register_lastname
            }
            status_model = {
                'username': data.register_username,
                'isonline': 0,
                'message': data.message,
                'new_message': 0,
                'fullname': "{} {} {}".format(data.register_firstname, data.register_middlename, data.register_lastname)
            }
            self.repo.save(User, **user_model)
            self.repo.save(Status, **status_model) 
        
        response = Message(  
            type=MessageType.REGISTER_SUCESS if success else MessageType.REGISTER_FAILED
        )
        self.transport_map[data.sender_peername].write(pickle.dumps(response))
        await asyncio.sleep(1)

    async def login(self, data: Message):
        success = False 
        user = self.repo.find(data.sender, User)
        if type(user) != type(None): 
            if user.password == data.password:
                success = True
                message = "Incorrect username or password"
        
        if success:
            userstatus = self.repo.find(data.sender, Status)
            if userstatus.isonline:
                success = False
                message = "Account already logged"
        else:
            message = "Account don't exists"
        response = Message( 
            message=message,
            type=MessageType.LOGIN_SUCCESS if success else MessageType.LOGIN_FAILED
        ) 
        self.transport_map[data.sender_peername].write(pickle.dumps(response))  
        await asyncio.sleep(1)

    async def file(self, data: Message):
        if len(data.file) == data.filesize:
            chats = {
                'sender': data.sender,
                'receiver': data.receiver,
                'message': data.message,
                'filename': data.filename,
                'file_reference': data.file_reference, 
                'timestamp': data.timestamp,
                'peername': str(data.sender_peername)
            }
            self.repo.save(Chats, **chats)
            path = self.uploads_path + "/" + data.file_reference
            if not os.path.exists(path):
                os.mkdir(path)
            with open(path + "/" + data.filename, 'wb') as file:
                file.write(data.file)

            data.type = MessageType.MESSAGE
            await self.sendmessage(data) 
        await asyncio.sleep(1) 

    async def sendmessage(self, data: Message):
        user = self.repo.find(data.receiver, Status)
        if user.isonline:
            peername = self.sender_peername_map[data.receiver] 
            message = Message(
                image=data.image, 
                image_index=data.image_index, 
                image_len=data.image_len, 
                audio=data.audio, 
                message=data.message, 
                sender=data.sender, 
                receiver=data.receiver, 
                filename=data.filename,
                file_reference=data.file_reference,
                timestamp=data.timestamp, 
                sender_peername=peername,
                type=data.type
            )  
            self.transport_map[peername].write(pickle.dumps(message)) 
        
        user = self.repo.find(data.sender, User)
        peername = self.sender_peername_map[data.sender] 
        message = Message(
            image=data.image, 
            image_index=data.image_index, 
            image_len=data.image_len, 
            audio=data.audio, 
            message=data.message, 
            sender=data.sender, 
            receiver=data.receiver, 
            filename=data.filename,
            file_reference=data.file_reference,
            timestamp=data.timestamp, 
            sender_peername=peername,
            type=data.type
        )   
        self.transport_map[peername].write(pickle.dumps(message))
        await asyncio.sleep(1)

    def tcp_connection_made(self, transport: asyncio.BaseTransport):
        peername = transport.get_extra_info('peername')
        sockname = transport.get_extra_info('sockname') 
        self.transport_map[peername] = transport    
        self.server_logs.append("[{}] {} connected to the server".format(datetime.now().strftime('%m/%d/%Y %H:%M:%S'), peername))
    
    def tcp_data_received(self, data: bytes, transport: asyncio.BaseTransport):  
        peername = transport.get_extra_info('peername')
        if peername not in self.buffer_map: 
            self.buffer_map[peername] = bytearray()
            
        self.buffer_map[peername] += data 

        try:
            data: Message = pickle.loads(self.buffer_map[peername])
            if data.type == MessageType.CONNECTED:
                asyncio.ensure_future(self.connected(data))
            elif data.type == MessageType.MESSAGE:  
                asyncio.ensure_future(self.message(data))
            elif data.type == MessageType.REGISTER:
                asyncio.ensure_future(self.register(data))
            elif data.type == MessageType.LOGIN:   
                asyncio.ensure_future(self.login(data))
            self.buffer_map[peername] = bytearray()
        except:
            pass
        time.sleep(0.01)

    def tcp_connection_lost(self, transport: asyncio.BaseTransport):
        asyncio.ensure_future(self.disconnected(transport))

    def tcp_file_connection_made(self, transport: asyncio.BaseTransport):
        peername = transport.get_extra_info('peername')
        sockname = transport.get_extra_info('sockname') 
        self.transport_map[peername] = transport    
        self.server_logs.append("[{}] {} connected to the server".format(datetime.now().strftime('%m/%d/%Y %H:%M:%S'), peername))
    
    def tcp_file_data_received(self, data: bytes, transport: asyncio.Transport):  
        peername = transport.get_extra_info('peername')
        if peername not in self.filebuffersize_map:
            self.filebuffersize_map[peername] = 0
        self.filebuffersize_map[peername] += len(data)
        size = Message(
                message=str(self.filebuffersize_map[peername])
            )
        size = pickle.dumps(size) 
        transport.write(size)
        if peername not in self.buffer_map: 
            self.buffer_map[peername] = bytearray()
            
        self.buffer_map[peername] += data 

        try:
            data: Message = pickle.loads(self.buffer_map[peername])
            if data.type == MessageType.FILE:
                asyncio.ensure_future(self.file(data)) 
            self.buffer_map[peername] = bytearray()
            self.filebuffersize_map[peername] = 0
        except:
            pass
        time.sleep(0.01)

    def tcp_file_connection_lost(self, transport: asyncio.BaseTransport):
        asyncio.ensure_future(self.disconnected(transport))

    def udp_connection_made(self, transport: asyncio.DatagramTransport):
        self.udp_transport = transport 

    def udp_datagram_received(self, data: bytes, addr: tuple):
        data: Message = pickle.loads(data) 

        if data.type == MessageType.CONNECTED:
            self.udp_transport_map[data.sender_peername] = self.udp_transport
            self.udp_peername_map[data.sender] = data.sender_peername
        elif data.type == MessageType.MESSAGE:  
            self.udp_transport_map[self.udp_peername_map[data.sender]].sendto(pickle.dumps(data), self.udp_peername_map[data.receiver])  
 
    def start(self): 
        self.loop = asyncio.get_event_loop() 
        self.loop.set_default_executor(ThreadPoolExecutor(1000))
        coro = self.loop.create_server(lambda: TCPServerProtocol(self.tcp_connection_made, self.tcp_data_received, self.tcp_connection_lost), self.host, self.tcp_port)
        server = self.loop.run_until_complete(coro)

        coro = self.loop.create_server(lambda: TCPServerProtocol(self.tcp_file_connection_made, self.tcp_file_data_received, self.tcp_file_connection_lost), self.host, 2222)
        server = self.loop.run_until_complete(coro)
    
        connect = self.loop.create_datagram_endpoint(lambda: UDPServerProtocol(self.udp_connection_made, self.udp_datagram_received), local_addr=(self.host, self.udp_port))
        transport, protocol = self.loop.run_until_complete(connect) 
        self.loop.run_forever()

    def stop(self): 
        self.stopped = True
        self.loop.call_soon_threadsafe(self.loop.stop)  

