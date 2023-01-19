from __future__ import annotations 
import os
import sys
import cv2 
import pickle 
import base64
import asyncio
import numpy as np
import time

CUR_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.join(CUR_DIR, '..')
sys.path.append(ROOT_DIR)

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

class Client():
    def __init__(self, host: str = '127.0.0.1', tcp_port: int = 9999, udp_port: int = 6666) -> None:
        self.host: str = host
        self.image: bytes = b''
        self.audio: bytes = b''
        self.username: str = "" 
        self.connected: bool = False 
        self.tcp_port: int = tcp_port
        self.udp_port: int = udp_port
        self.upload_filesize: int = 1
        self.download_filesize: int = 1
        self.can_upload_file: bool = True
        self.can_download_file: bool = True
        self.upload_filename: str = None
        self.download_filename: str = None
        self.string_sockname: tuple = None
        self.fullname_map: dict[str, str] = {}
        self.is_uploading_file_failed: bool = False 
        self.is_downloading_file_failed: bool = False
        self.downloads_path: str = ROOT_DIR + "/downloads" 
        self.uploading_files_map: dict[str, int] = {}
        self.downloading_files_map: dict[str, int] = {}
        self.upload_transport: asyncio.Transport = None
        self.string_transport: asyncio.Transport = None
        self.users_map: dict[str, dict[str, bool | str]] = {}
        self.users_chat_map: dict[str, dict[str, Queue | list]] = {}  

        if not os.path.exists(self.downloads_path):
            os.mkdir(self.downloads_path)

        self.file_buffer = []
        self.buffer_map = {}
        self.download_buffer = bytearray()
        self.profile_pictures: dict[str, bytes] = {}
    
    def tcp_string_connection_made(self, transport: asyncio.Transport):
        self.string_transport = transport
        self.string_peername = transport.get_extra_info('peername')
        self.string_sockname = transport.get_extra_info('sockname')  

    def tcp_string_data_received(self, data: bytes):  
        try: 
            data: Message = pickle.loads(data)  
            if data.type == MessageType.CONNECTED: 
                    pass
            elif data.type == MessageType.DISCONNECTED:
                    for user, value in self.users_map.items():
                        if user == data.sender:
                            value['online'] = False 
            elif data.type == MessageType.MESSAGE:  
                    if data.message or data.upload_filename:    
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
                            'id': data.message_id,
                            'name': name.split(" ")[0],
                            'message': data.message,
                            'filename': data.upload_filename,
                            'filesize': data.upload_filesize,
                            'timestamp': data.timestamp, 
                        })  
                        self.users_map[key]['last-message'] = data.message if data.message else data.upload_filename
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
                        if user.username not in self.users_chat_map:
                            self.users_chat_map[user.username] = {
                                'images': Queue(),
                                'audios': Queue(),
                                'messages': list(),
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
                                'id': chat.id,
                                'name': name.split(" ")[0],
                                'message': chat.message,
                                'filename': chat.filename,
                                'filesize': chat.filesize,
                                'timestamp': chat.timestamp, 
                            }) 
                            self.users_map[key]['last-message'] = chat.message if chat.message else chat.filename 
                    for user in data.users:
                        if user.profile_picture != None:
                            self.profile_pictures[user.username] = user.profile_picture
            elif data.type == MessageType.DOWNLOAD_FILE_PERCENTAGE:
                self.download_filename = data.download_filename
                self.download_filesize = data.download_filesize
            elif data.type == MessageType.PROFILE_PICTURE:
                for user in data.users:
                    if user.profile_picture != None:
                        self.profile_pictures[user.username] = user.profile_picture
        except:
            pass    
        time.sleep(0.01)
 
    def tcp_string_connection_lost(self):
        pass

    def tcp_upload_connection_made(self, transport: asyncio.Transport):
        self.upload_transport = transport  
        self.upload_peername = transport.get_extra_info('peername')
        self.upload_sockname = transport.get_extra_info('sockname')  

    def tcp_upload_data_received(self, data: bytes):  
        try:
            data: Message = pickle.loads(data)
            if data.type == MessageType.UPLOAD_FILE_PERCENTAGE:
                self.uploading_files_map[self.upload_filename] = int((int(data.upload_file_percent) / self.upload_filesize) * 100)
                if self.uploading_files_map[self.upload_filename] == 100:
                    self.upload_filename = None
                    self.can_upload_file = True  
        except:
            pass
        time.sleep(0.01)

    def tcp_upload_connection_lost(self):
        self.is_uploading_file_failed = True 

    def tcp_download_connection_made(self, transport: asyncio.Transport):
        self.download_transport = transport  
        self.download_peername = transport.get_extra_info('peername')
        self.download_sockname = transport.get_extra_info('sockname')  

    def tcp_download_data_received(self, data: bytes):  
        self.download_buffer += data 
        self.downloading_files_map[self.download_filename] = int((len(self.download_buffer) / int(self.download_filesize)) * 100)

        try:
            data: Message = pickle.loads(self.download_buffer)
            path = self.downloads_path + "/" + datetime.now().strftime('%m%d%Y%H%M%S.%f')
            if not os.path.exists(path):
                os.mkdir(path)
            with open(path + "/" + data.download_filename, 'wb') as file:
                file.write(data.download_filebytes)
            self.can_download_file = True
            self.download_buffer = bytearray()
        except Exception as e:
            pass
        time.sleep(0.01)

    def tcp_download_connection_lost(self):
        self.is_downloading_file_failed = True  

    def udp_connection_made(self, transport: asyncio.DatagramTransport):
        self.udp_transport = transport 
        self.udp_peername = transport.get_extra_info('peername')
        self.udp_sockname = transport.get_extra_info('sockname') 
        data = Message(
            sender=self.username, 
            timestamp=datetime.now().strftime('%m/%d/%Y %H:%M:%S.%f'), 
            sender_peername=self.udp_sockname, 
            type=MessageType.CONNECTED
        )
        transport.sendto(pickle.dumps(data), self.udp_peername)

    def udp_datagram_received(self, data: bytes, addr: tuple):
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
    
    def silence_event_loop_closed(self, func):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            try:
                return func(self, *args, **kwargs)
            except RuntimeError as e:
                if str(e) != 'Event loop is closed':
                    raise
        return wrapper

    def start(self): 
        _ProactorBasePipeTransport.__del__ = self.silence_event_loop_closed(_ProactorBasePipeTransport.__del__)
        asyncio.set_event_loop(asyncio.new_event_loop())
        self.loop = asyncio.get_event_loop()
        self.loop.set_default_executor(ThreadPoolExecutor(1000))

        coro = self.loop.create_connection(lambda: TCPClientProtocol(self.tcp_string_connection_made, self.tcp_string_data_received, self.tcp_string_connection_lost), self.host, self.tcp_port)
        server, _ = self.loop.run_until_complete(coro) 

        coro = self.loop.create_connection(lambda: TCPClientProtocol(self.tcp_upload_connection_made, self.tcp_upload_data_received, self.tcp_upload_connection_lost), self.host, 2222)
        server, _ = self.loop.run_until_complete(coro)

        coro = self.loop.create_connection(lambda: TCPClientProtocol(self.tcp_download_connection_made, self.tcp_download_data_received, self.tcp_download_connection_lost), self.host, 3333)
        server, _ = self.loop.run_until_complete(coro)
        
        connect = self.loop.create_datagram_endpoint(lambda: UDPClientProtocol(self.udp_connection_made, self.udp_datagram_received), remote_addr=(self.host, self.udp_port))
        transport, protocol = self.loop.run_until_complete(connect)
        self.connected = True
        self.loop.run_forever()

    def stop(self):  
        self.loop.call_soon_threadsafe(self.loop.stop)  
