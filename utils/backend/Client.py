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
        self.users_map: dict[str, dict[str, bool | str]] = {}
        self.users_chat_map: dict[str, dict[str, Queue | list]] = {} 

    def __tcp_connection_made(self, transport: asyncio.Transport):
        self.tcp_transport = transport
        self.peername = transport.get_extra_info('peername')
        self.sockname = transport.get_extra_info('sockname') 
        data = Message(sender=self.username, timestamp=datetime.now().strftime('%m/%d/%Y %H:%M:%S'), sender_peername=self.sockname, type=MessageType.CONNECTED) 
        self.tcp_transport.write(pickle.dumps(data))

    def __tcp_data_received(self, data: bytes): 
        data: Message = pickle.loads(data)

        if data.type == MessageType.CONNECTED:
            self.users_map[data.sender] = {
                'online': True,
                'new-message': True,
                'last-message': data.message
            }
            if data.sender not in self.users_chat_map:   
                self.users_chat_map[data.sender] = {
                    'images': Queue(),
                    'audios': Queue(),
                    'messages': list(),
            }
        elif data.type == MessageType.DISCONNECTED:
            del self.users_map[data.sender]
        elif data.type == MessageType.MESSAGE:  
            if data.message: 
                message = "[{}] [{}]: {}".format(datetime.now().strftime('%m/%d/%Y %H:%M:%S'), data.sender, data.message)
                self.users_chat_map[data.sender]['messages'].append(message)  

    def __udp_connection_made(self, transport: asyncio.DatagramTransport):
        self.udp_transport = transport 
        self.udp_peername = transport.get_extra_info('peername')
        self.udp_sockname = transport.get_extra_info('sockname') 
        data = Message(sender=self.username, timestamp=datetime.now().strftime('%m/%d/%Y %H:%M:%S'), sender_peername=self.udp_sockname, type=MessageType.CONNECTED)
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
        self.loop.run_forever()

    def stop(self):
        self.loop.call_soon_threadsafe(self.loop.stop)  
