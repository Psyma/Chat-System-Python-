from __future__ import annotations 
import cv2 
import pickle 
import base64
import asyncio
import numpy as np

from queue import Queue
from datetime import datetime
from imgui_datascience import * 

from utils.models.Message import Message
from utils.models.MessageType import MessageType
from concurrent.futures import ThreadPoolExecutor
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
            if data.sender not in self.users_chat_map:   
                self.users_chat_map[data.sender] = {
                    'images': Queue(),
                    'audios': Queue(),
                    'messages': list(),
            }
        elif data.type == MessageType.DISCONNECTED:
            for user, value in self.users_map.items():
                if user == data.sender:
                    value['online'] = False 
        elif data.type == MessageType.MESSAGE:  
            if data.message: 
                name = self.fullname_map[data.sender]
                message = "[{}] [{}]: {}".format(datetime.now().strftime('%m/%d/%Y %H:%M:%S'), name.split(" ")[0], data.message)
                self.users_chat_map[data.sender]['messages'].append(message)  
                self.users_map[data.sender]['last-message'] = data.message 
                temp = {}
                temp[data.sender] = self.users_map[data.sender]
                for key, value in self.users_map.items():
                    if key != data.sender:
                        temp[key] = value
                self.users_map = temp
        elif data.type == MessageType.REGISTER:
            print(data.message)
        elif data.type == MessageType.LOGIN:
            print(data.message)
        elif data.type == MessageType.CONNECTED_USERS: 
            for user in data.connected_users:  
                self.fullname_map[user.username] = user.fullname
                self.users_map[user.username] = {
                    'online': user.isonline,
                    'new-message': user.new_message,
                    'last-message': user.message
                } 
                if user.username not in self.users_chat_map:
                    self.users_chat_map[user.username] = {
                        'images': Queue(),
                        'audios': Queue(),
                        'messages': list(),
                }
        elif data.type == MessageType.CHATS_HISTORY:   
            for user in data.history_messages:
                if user.sender == self.username:
                    key = user.receiver
                    message = "[{}] [{}]: {}".format(user.timestamp, 'You', user.message)
                    self.users_chat_map[key]['messages'].append(message)
                elif user.receiver == self.username:
                    key = user.sender
                    name = self.fullname_map[user.sender]
                    message = "[{}] [{}]: {}".format(user.timestamp, name.split(" ")[0], user.message)  
                    self.users_chat_map[key]['messages'].append(message)  
                    self.users_map[user.sender]['last-message'] = user.message

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

    def start(self):
        asyncio.set_event_loop(asyncio.new_event_loop())
        self.loop = asyncio.get_event_loop()
        self.loop.set_default_executor(ThreadPoolExecutor(1000))
        coro = self.loop.create_connection(lambda: TCPClientProtocol(self.__tcp_connection_made, self.__tcp_data_received), self.host, self.tcp_port)
        server, _ = self.loop.run_until_complete(coro) 
        
        connect = self.loop.create_datagram_endpoint(lambda: UDPClientProtocol(self.__udp_connection_made, self.__udp_datagram_received), remote_addr=(self.host, self.udp_port))
        transport, protocol = self.loop.run_until_complete(connect)
        self.connected = True
        self.loop.run_forever()

    def stop(self):
        self.loop.call_soon_threadsafe(self.loop.stop)  
