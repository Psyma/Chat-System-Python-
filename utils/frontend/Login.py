from __future__ import annotations 
import os, sys 
import cv2 
import pickle 
import base64
import asyncio
import glfw
import numpy as np

from queue import Queue
from datetime import datetime
from imgui_datascience import *

CUR_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.join(CUR_DIR, '../..')
sys.path.append(ROOT_DIR)

from threading import Thread
import time
from utils.frontend.Gui import Gui
from utils.models.Message import Message 
from utils.models.MessageType import MessageType
from concurrent.futures import ThreadPoolExecutor
from utils.protocols.TCPClientProtocol import TCPClientProtocol 
from utils.messaging.StringStream import StringStream

class Login(Gui):
    def __init__(self, 
                window_name="", 
                window_width=420, 
                window_height=340, 
                is_resizeable=False, 
                host="127.0.0.1", 
                tcp_port=9999, ) -> None:
        super().__init__(window_name, window_width, window_height, is_resizeable)
        self.host = host
        self.tcp_port = tcp_port
        self.is_display_frame = True
        self.fonts_map = self.__set_fonts() 
        self.string_stream = StringStream()

        self.username = "tata"
        self.password = "1"
        self.login: bool = False
        self.register: bool = False
        self.register_username: str = ""
        self.register_password: str = ""
        self.register_password_confirm: str = ""
        self.register_firstname: str = ""
        self.register_middlename: str = ""
        self.register_lastname: str = ""
        self.tcp_transport = None

        self.delay = 4
        self.counter = 1
        self.delay_counter = 1
        self.message = ""
        self.logging_info = False
        self.connecting_to_server = False
        self.exit = False
        self.login_success = False

    def __tcp_connection_made(self, transport: asyncio.Transport):
        self.tcp_transport = transport
        self.peername = transport.get_extra_info('peername')
        self.sockname = transport.get_extra_info('sockname')   

    def __tcp_data_received(self, data: bytes): 
        data: Message = pickle.loads(data)  
        self.connecting_to_server = False 
        if data.type == MessageType.LOGIN_SUCCESS:  
            self.exit = True 
            self.login_success = True
        elif data.type == MessageType.LOGIN_FAILED:
            self.logging_info = True 
            self.message = data.message
        elif data.type == MessageType.REGISTER_SUCESS: 
            self.register = False
            self.logging_info = True
            self.message = "Account successfully created"
            self.register_username: str = ""
            self.register_password: str = ""
            self.register_password_confirm: str = ""
            self.register_firstname: str = ""
            self.register_middlename: str = ""
            self.register_lastname: str = "" 
        elif data.type == MessageType.REGISTER_FAILED: 
            self.logging_info = True
            self.message = "Username already exists"  
        elif data.type == MessageType.MESSAGE_RECEIVED:
            self.string_stream.mssgreceived = True

    def __tcp_connection_lost(self):
        self.connecting_to_server = True

    def __set_fonts(self):
        fonts_map: dict[str, dict[str, None | int | str]] = {
            "profile-fonts-Montserrat" : {
                "font-obj" : None,
                "font-size" : 25,
                "font-path" : ROOT_DIR + "/assets/MontserratAlternates-Bold.otf"
            },
            "profile-fonts-Bebas" : {
                "font-obj" : None,
                "font-size" : 20,
                "font-path" : ROOT_DIR + "/assets/Bebas-Regular.ttf"
            }, 
            "profile-fonts-Drift": {
                "font-obj" : None,
                "font-size" : 35,
                "font-path" : ROOT_DIR + "/assets/Drift.ttf"
            },
            "profile-fonts-Maladewa" : {
                "font-obj" : None,
                "font-size" : 40,
                "font-path" : ROOT_DIR + "/assets/Maladewa.ttf"
            },
            "profile-fonts-Maladewa-30" : {
                "font-obj" : None,
                "font-size" : 30,
                "font-path" : ROOT_DIR + "/assets/Maladewa.ttf"
            },
            "profile-fonts-Maladewa-x" : {
                "font-obj" : None,
                "font-size" : 27,
                "font-path" : ROOT_DIR + "/assets/Maladewa.ttf"
            },
            "profile-fonts-Drift-25" : {
                "font-obj" : None,
                "font-size" : 25,
                "font-path" : ROOT_DIR + "/assets/Drift.ttf"
            },
            "profile-fonts-Drift-40" : {
                "font-obj" : None,
                "font-size" : 40,
                "font-path" : ROOT_DIR + "/assets/Drift.ttf"
            },
        } 

        return fonts_map

    def start(self): 
        self.connecting_to_server = True
        self.t = Thread(target=self.__show_frames, args=())
        self.t.start()
        while self.is_display_frame: 
            try: 
                asyncio.set_event_loop(asyncio.new_event_loop())
                self.loop = asyncio.get_event_loop()
                self.loop.set_default_executor(ThreadPoolExecutor(1000))
                coro = self.loop.create_connection(lambda: TCPClientProtocol(self.__tcp_connection_made, self.__tcp_data_received, self.__tcp_connection_lost), self.host, self.tcp_port)
                server, _ = self.loop.run_until_complete(coro)  
                self.connecting_to_server = False 
                self.loop.run_forever()
            except: 
                pass
            time.sleep(1) 

    def stop(self):
        self.string_stream.stopped = True
        self.loop.call_soon_threadsafe(self.loop.stop)  

    def __register(self):
        imgui.set_next_window_position(0, 0)
        imgui.set_next_window_size(self.window_width, self.window_height)
        imgui.begin("Register", flags= imgui.WINDOW_NO_COLLAPSE | imgui.WINDOW_NO_SCROLLBAR) 
        
        width, height = imgui.get_window_size()
        imgui.push_font(self.fonts_map['profile-fonts-Drift-40']['font-obj']) 
        text = "Create an account"
        text_width, text_height = imgui.calc_text_size(text)
        imgui.set_cursor_pos_x((width - text_width) * 0.5)
        imgui.text_wrapped(text)
        imgui.pop_font()
        border_height = 200
        imgui.set_cursor_pos_y((height - border_height) * .5)
        imgui.begin_child("1", border=True, height=border_height)

        ret, value = imgui.input_text(label="Username", value=self.register_username, buffer_length=50, flags=imgui.INPUT_TEXT_ENTER_RETURNS_TRUE)
        if not ret:
            self.register_username = value 
        ret, value = imgui.input_text(label="Password", value=self.register_password, buffer_length=50, flags=imgui.INPUT_TEXT_ENTER_RETURNS_TRUE | imgui.INPUT_TEXT_PASSWORD)
        if not ret:
            self.register_password = value
        ret, value = imgui.input_text(label="Password Confirm", value=self.register_password_confirm, buffer_length=50, flags=imgui.INPUT_TEXT_ENTER_RETURNS_TRUE | imgui.INPUT_TEXT_PASSWORD)
        if not ret:
            self.register_password_confirm = value
        
        ret, value = imgui.input_text(label="First Name", value=self.register_firstname, buffer_length=50, flags=imgui.INPUT_TEXT_ENTER_RETURNS_TRUE)
        if not ret:
            self.register_firstname = value
        
        ret, value = imgui.input_text(label="Middle Name", value=self.register_middlename, buffer_length=50, flags=imgui.INPUT_TEXT_ENTER_RETURNS_TRUE)
        if not ret:
            self.register_middlename = value
        
        ret, value = imgui.input_text(label="Last Name", value=self.register_lastname, buffer_length=50, flags=imgui.INPUT_TEXT_ENTER_RETURNS_TRUE)
        if not ret:
            self.register_lastname = value

        if imgui.button("Register"):  
            ok = True 
            if not self.register_username:
                ok = False
                self.logging_info = True
                self.message = "Username is empty"
            elif not self.register_password or not self.register_password_confirm:
                ok = False
                self.logging_info = True
                self.message = "Password is empty"
            elif not self.register_firstname:
                ok = False
                self.logging_info = True
                self.message = "Firstname is empty"
            elif not self.register_middlename:
                ok = False
                self.logging_info = True
                self.message = "Middlename is empty"
            elif not self.register_lastname:
                ok = False
                self.logging_info = True
                self.message = "Lastname is empty"
            elif self.register_password != self.register_password_confirm:
                ok = False
                self.logging_info = True
                self.message = "Password do not match"
            elif self.register_password == self.register_password_confirm and ok:
                self.connecting_to_server = True 
                data = Message(
                    timestamp=datetime.now().strftime('%m/%d/%Y %H:%M:%S'),
                    register_username=self.register_username,
                    register_password=self.register_password,
                    register_firstname=self.register_firstname,
                    register_middlename=self.register_middlename,
                    register_lastname=self.register_lastname,
                    sender_peername=self.sockname,
                    type=MessageType.REGISTER
                ) 
                self.tcp_transport.write(pickle.dumps(data)) 

        imgui.same_line() 
        if imgui.button("Back"): 
            self.register = False
        
        imgui.end_child() 
        imgui.end()
 
    def __login(self):
        imgui.set_next_window_position(0, 0)
        imgui.set_next_window_size(self.window_width, self.window_height)
        imgui.begin("Account", flags= imgui.WINDOW_NO_COLLAPSE | imgui.WINDOW_NO_SCROLLBAR) 

        width, height = imgui.get_window_size()
        imgui.push_font(self.fonts_map['profile-fonts-Drift-40']['font-obj']) 
        text = "Account Login"
        text_width, text_height = imgui.calc_text_size(text)
        imgui.set_cursor_pos_x((width - text_width) * 0.5)
        imgui.text_wrapped(text)
        imgui.pop_font()
        border_height = 85
        imgui.set_cursor_pos_y((height - border_height) * .5)
        imgui.begin_child("1", border=True, height=border_height)
        
        ret, value = imgui.input_text(label="Username", value=self.username, buffer_length=20, flags=imgui.INPUT_TEXT_ENTER_RETURNS_TRUE)
        if not ret:
            self.username = value 
        
        ret, value = imgui.input_text(label="Password", value=self.password, buffer_length=50, flags=imgui.INPUT_TEXT_ENTER_RETURNS_TRUE | imgui.INPUT_TEXT_PASSWORD)
        if not ret:
            self.password = value 
        else:
            self.connecting_to_server = True
            data = Message(
                sender=self.username, 
                password=self.password,
                sender_peername=self.sockname,
                timestamp=datetime.now().strftime('%m/%d/%Y %H:%M:%S'), 
                type=MessageType.LOGIN
            )

            self.string_stream.send(data, self.tcp_transport) 
        
        if imgui.button("Register"): 
            self.register = True
        imgui.same_line()
        if imgui.button("Login"): 
            self.connecting_to_server = True
            data = Message(
                sender=self.username, 
                password=self.password,
                sender_peername=self.sockname,
                timestamp=datetime.now().strftime('%m/%d/%Y %H:%M:%S'), 
                type=MessageType.LOGIN
            )
    
            self.string_stream.send(data, self.tcp_transport) 
        imgui.same_line()
        if imgui.button("Close"):
            self.is_display_frame = False 
            self.window_stop = False
            self.string_stream.stopped = True

        imgui.end_child() 
        imgui.end()

    def __loading(self):
        imgui.set_next_window_size(165, 100)
        imgui.set_next_window_position((self.window_width - 165) * .50, (self.window_height - 100) * .50)
        if self.connecting_to_server:
            imgui.push_id('info-3')
            imgui.open_popup("[INFO]")
        if imgui.begin_popup_modal("[INFO]", flags=imgui.WINDOW_NO_RESIZE)[0]: 
            text = "Conneting to server"
            width, height = imgui.get_window_size()
            text_width, text_height = imgui.calc_text_size(text)
            imgui.set_cursor_pos_y(35) 
            imgui.set_cursor_pos_x((width - text_width) * 0.5)
            imgui.text(text)
            imgui.set_cursor_pos_y((height / 2) + 10)
            
            self.delay_counter = self.delay_counter + 1 
            for i in range(1, 8, 1):
                if i == self.counter: 
                    imgui.push_style_color(imgui.COLOR_TEXT, 0, 1, 0)  
                    imgui.bullet()
                    imgui.pop_style_color()
                else:
                    imgui.bullet()

            if self.counter == 7:
                if self.delay_counter == self.delay:
                    self.counter = 0
            if self.delay_counter == self.delay:
                self.delay_counter = 0
                self.counter = self.counter + 1
            
            imgui.end_popup()
            imgui.pop_id()

    def __logging_info(self):
        imgui.set_next_window_size(250, 100)
        imgui.set_next_window_position((self.window_width - 250) * .50, (self.window_height - 100) * .50)
        if self.logging_info:
            imgui.push_id('info-2')
            imgui.open_popup("[INFO]")
        if imgui.begin_popup_modal("[INFO]", flags=imgui.WINDOW_NO_RESIZE)[0]:  
            text_width, text_height = imgui.calc_text_size(self.message)
            width, height = imgui.get_window_size()
            imgui.text("")
            imgui.set_cursor_pos_x((width - text_width) * .50)
            imgui.text(self.message)
            imgui.set_cursor_pos_x((width - 50) * .50)
            if imgui.button("OK", width=50):
                self.logging_info = False
            imgui.end_popup()
            imgui.pop_id()

    def frame_commands(self):
        if self.exit:
            self.is_display_frame = False 
            self.window_stop = False

        imgui.get_style().window_rounding = 0 
        if self.register:
            self.__register()
        else:
            if not self.login:
                self.__login()
        if self.connecting_to_server:
            self.__loading()

        if self.logging_info:
            self.__logging_info()
            
    def __show_frames(self):
        self.is_display_frame = self.display_frames(self.fonts_map)
        self.stop() 