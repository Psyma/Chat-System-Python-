from __future__ import annotations 
import cv2 
import pickle 
import base64
import asyncio
import numpy as np

from queue import Queue
from functools import wraps
from datetime import datetime
from imgui_datascience import * 

from utils.models.Message import Message
from utils.models.MessageType import MessageType
from concurrent.futures import ThreadPoolExecutor
from utils.messaging.StringStream import StringStream
from asyncio.proactor_events import _ProactorBasePipeTransport
from utils.protocols.TCPClientProtocol import TCPClientProtocol
from utils.protocols.UDPClientProtocol import UDPClientProtocol
class Client(object):
    def __init__(self, host: str = '127.0.0.1', tcp_port: int = 9999, udp_port: int = 6666) -> None:
        self.host: str = host
        self.tcp_port: int = tcp_port
        self.udp_port: int = udp_port
        self.image: bytes = b''
        self.audio: bytes = b''
        self.username: str = "" 
        self.fullname_map: dict[str, str] = {}
        self.sockname: tuple = None
        self.connected: bool = False
        self.string_stream = StringStream()
        self.tcp_transport: asyncio.Transport = None
        self.users_map: dict[str, dict[str, bool | str]] = {}
        self.users_chat_map: dict[str, dict[str, Queue | list]] = {}  

    def __tcp_connection_made(self, transport: asyncio.Transport):
        self.tcp_transport = transport
        self.peername = transport.get_extra_info('peername')
        self.sockname = transport.get_extra_info('sockname')  

    def __tcp_data_received(self, data: bytes): 
        data: Message = pickle.loads(data)

        if data.type == MessageType.CONNECTED: 
            pass
        elif data.type == MessageType.DISCONNECTED:
            for user, value in self.users_map.items():
                if user == data.sender:
                    value['online'] = False 
        elif data.type == MessageType.MESSAGE:  
            if data.message or data.filename:   
                ok = False
                if data.sender == self.username:
                    ok = True
                    name = "You"
                    key = data.receiver
                elif data.receiver == self.username:
                    ok = True
                    key = data.sender
                    name = self.fullname_map[data.sender]
                self.users_chat_map[key]['messages'].append({ 
                    'name': name.split(" ")[0],
                    'message': data.message,
                    'filename': data.filename,
                    'timestamp': data.timestamp, 
                })  
                self.users_map[key]['last-message'] = data.message if data.message else data.filename
                temp = {}
                temp[key] = self.users_map[key]
                for _key, value in self.users_map.items():
                    if _key != key:
                        temp[_key] = value
                self.users_map = temp  
        elif data.type == MessageType.REGISTER:
            print(data.message)
        elif data.type == MessageType.LOGIN:
            print(data.message)
        elif data.type == MessageType.CONNECTED_USERS: 
            for user in data.connected_users:  
                self.fullname_map[user.username] = user.fullname
                if user.username in self.users_map:
                    self.users_map[user.username]['online'] = user.isonline
                    self.users_map[user.username]['new-message'] = user.new_message
                else:
                    self.users_map[user.username] = {
                        'online': user.isonline,
                        'new-message': user.new_message,
                        'last-message': None
                    }  
        elif data.type == MessageType.CHATS_HISTORY:    
            keys = {}
            for chat in data.history_messages:  
                ok = False
                if chat.sender == self.username:
                    ok = True
                    name = "You"
                    key = chat.receiver
                elif chat.receiver == self.username:
                    ok = True
                    key = chat.sender
                    name = self.fullname_map[chat.sender]
                if key not in keys:
                    keys[key] = 1
                    self.users_chat_map[key] = {
                        'images': Queue(),
                        'audios': Queue(),
                        'messages': list(),
                    }
                if ok: 
                    self.users_chat_map[key]['messages'].append({
                        'name': name.split(" ")[0],
                        'message': chat.message,
                        'filename': chat.filename,
                        'timestamp': chat.timestamp, 
                    }) 
                    self.users_map[key]['last-message'] = chat.message if chat.message else chat.filename
        elif data.type == MessageType.MESSAGE_RECEIVED:
            self.string_stream.mssgreceived = True

    def __tcp_connection_lost(self):
        pass

    def __udp_connection_made(self, transport: asyncio.DatagramTransport):
        self.udp_transport = transport 
        self.udp_peername = transport.get_extra_info('peername')
        self.udp_sockname = transport.get_extra_info('sockname') 
        data = Message(
            sender=self.username, 
            timestamp=datetime.now().strftime('%m/%d/%Y %H:%M:%S'), 
            sender_peername=self.udp_sockname, 
            type=MessageType.CONNECTED
        )
        transport.sendto(pickle.dumps(data), self.udp_peername)

    def __udp_datagram_received(self, data: bytes, addr: tuple):
        data: Message = pickle.loads(data) 
        if data.image:
            self.image = self.image + data.image
            if data.image_index == data.image_len:
                try: 
                    pass
                except:
                    pass
                self.image = b'' 
        if data.audio:
            pass
    
    def __silence_event_loop_closed(self, func):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            try:
                return func(self, *args, **kwargs)
            except RuntimeError as e:
                if str(e) != 'Event loop is closed':
                    raise
        return wrapper

    def start(self):
        _ProactorBasePipeTransport.__del__ = self.__silence_event_loop_closed(_ProactorBasePipeTransport.__del__)
        asyncio.set_event_loop(asyncio.new_event_loop())
        self.loop = asyncio.get_event_loop()
        self.loop.set_default_executor(ThreadPoolExecutor(1000))
        coro = self.loop.create_connection(lambda: TCPClientProtocol(self.__tcp_connection_made, self.__tcp_data_received, self.__tcp_connection_lost), self.host, self.tcp_port)
        server, _ = self.loop.run_until_complete(coro) 
        
        connect = self.loop.create_datagram_endpoint(lambda: UDPClientProtocol(self.__udp_connection_made, self.__udp_datagram_received), remote_addr=(self.host, self.udp_port))
        transport, protocol = self.loop.run_until_complete(connect)
        self.connected = True
        self.loop.run_forever()

    def stop(self):  
        self.loop.call_soon_threadsafe(self.loop.stop)  
