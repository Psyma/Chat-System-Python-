from __future__ import annotations 
import os
import cv2
import sys  
import time
import glfw
import imgui 
import socket
import pickle
import random
import base64
import pyaudio 
import easygui
import asyncio
import socket
import pathlib
import filetype

from threading import Thread 
from datetime import datetime 
from imgui_datascience import *

CUR_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.join(CUR_DIR, '..')
sys.path.append(ROOT_DIR)

from utils.frontend.Gui import Gui 
from utils.frontend.Login import Login
from utils.backend.Client import Client
from utils.models.Message import Message
from utils.models.MessageType import MessageType
from utils.messaging.VideoStream import VideoStream
from utils.messaging.AudioStream import AudioStream
from utils.messaging.StringStream import StringStream

class AppClient(Gui):
    def __init__(self, 
                window_name="", 
                window_width=1024, 
                window_height=768, 
                is_resizeable=False, 
                host="127.0.0.1", 
                tcp_port=9999, 
                udp_port=6666) -> None:
        super().__init__(window_name, window_width, window_height, is_resizeable)

        MS = 30
        RATE = 48000
        AUDIO = pyaudio.PyAudio()
        FORMAT = pyaudio.paInt16 
        CHANNELS = 1

        self.debug = False
        self.to_user: str = ""   
        self.is_display_chatbox: bool = False
        self.is_display_frame: bool = True
        self.is_audio_call: bool = False
        self.fonts_map: dict[str, dict[str, None | int | str]] = self.set_fonts()
        self.client = Client(host=host, tcp_port=tcp_port, udp_port=udp_port)
        self.string_stream = StringStream()
        self.video_stream = VideoStream(0) 
        self.audio_stream = AudioStream(MS, RATE, AUDIO, FORMAT, CHANNELS)    

        self.password: str = ""  
        self.is_login: bool = False
        self.is_register: bool = False
        self.register_username: str = ""
        self.register_password: str = ""
        self.register_password_confirm: str = ""
        self.register_firstname: str = ""
        self.register_middlename: str = ""
        self.register_lastname: str = ""  
        self.is_connected = False 
        self.delay = 4
        self.counter = 1
        self.delay_counter = 1
        self.upload_limit = 50 

    def start(self): 
        self.t = Thread(target=self.show_frames, args=())
        self.t.start()
        while self.is_display_frame:
            try:
                self.is_register = False
                self.client.connected = False
                self.is_connected = False
                self.client.start()   
            except: 
                pass
            time.sleep(1) 

    def frame_commands(self):   
        if self.client.connected and not self.is_connected:
            self.is_connected = True
            data = Message(
                sender = self.client.username, 
                sender_peername = self.client.sockname,
                timestamp = datetime.now().strftime('%m/%d/%Y %H:%M:%S'), 
                type = MessageType.CONNECTED
            )  
            self.send_string(data)
          
        self.profile() 
        if self.is_display_chatbox:
            self.chatbox()
        self.loading()  

    def loading(self):
        imgui.set_next_window_size(165, 100)
        imgui.set_next_window_position((self.window_width - 165) * .50, (self.window_height - 100) * .50)
        if not self.is_connected:
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

    def send_string(self, data: Message):
        self.string_stream.send(data, self.client.tcp_transport) 
        
    def send_image(self, frame, size = 65536): 
        encoded, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
        frames = base64.b64encode(buffer)

        chunks = [frames[i:i+size] for i in range(0,len(frames), size)] 
        for i, chunk in enumerate(chunks):
            message = Message(
                image=chunk, 
                image_index=i, 
                image_len=len(chunks) - 1,  
                sender=self.client.username, 
                receiver=self.to_user, 
                timestamp=datetime.now().strftime('%m/%d/%Y %H:%M:%S'), 
                type=MessageType.MESSAGE
            ) 
                                
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) 
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, size)
            self.socket.sendto(pickle.dumps(message), self.client.udp_peername)
    
    def send_audio(self, frame, size: int = 65536):
        data = Message(
            audio=frame, 
            sender=self.client.username, 
            receiver=self.to_user, 
            timestamp=datetime.now().strftime('%m/%d/%Y %H:%M:%S'), 
            type=MessageType.MESSAGE
        ) 
        
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) 
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, size)
        self.socket.sendto(pickle.dumps(data), self.client.udp_peername)

    def video_call(self):
        pass

    def audio_call(self):
        pass

    def truncate(self, string, width):
        if len(string) > width:
            string = string[:width-3] + '...'
        return string

    def set_fonts(self):
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

    def chatbox(self): 
        imgui.set_next_window_size(self.window_width - 299, self.window_height)
        imgui.set_next_window_position(299, 0)
        imgui.begin("Chatbox", flags=imgui.WINDOW_NO_COLLAPSE)
        
        if True:
            imgui.begin_child("1", border=False, height=65, flags=imgui.WINDOW_NO_SCROLLBAR)
            img = cv2.imread(ROOT_DIR + "/assets/default_profile.png")
            imgui_cv.image(img, width=65)
            imgui.same_line()
            if True:
                width, height = imgui.get_window_size()
                imgui.begin_child("1.1", border=True, width=(width * .50) - 65, flags=imgui.WINDOW_NO_SCROLLBAR)
                imgui.push_font(self.fonts_map['profile-fonts-Maladewa-30']['font-obj']) 
                if self.debug:
                    imgui.text_wrapped(self.truncate("Juan Dela Organization", 25))
                    imgui.pop_font()
                    if imgui.is_item_hovered():
                        imgui.set_tooltip("Juan Dela Organization")
                else:
                    imgui.text_wrapped(self.truncate(self.client.fullname_map[self.to_user], 25))
                    imgui.pop_font()
                    if imgui.is_item_hovered():
                        imgui.set_tooltip(self.client.fullname_map[self.to_user])
                if self.client.users_map[self.to_user]['online']:
                    imgui.push_style_color(imgui.COLOR_TEXT, 0, 1, 0)
                    imgui.text_wrapped("Active now")
                    imgui.pop_style_color() 
                else:
                    imgui.push_style_color(imgui.COLOR_TEXT, 1, 0, 0)
                    imgui.text_wrapped("Offline")
                    imgui.pop_style_color() 
                imgui.end_child()

            if True:
                imgui.same_line()
                imgui.begin_child("1.2", border=True)
                imgui.set_cursor_pos_y(13)
                if imgui.button("Video Call"):
                    pass
                imgui.same_line()
                if imgui.button("Audio Call"):
                    pass
                changed, search_text_val = imgui.input_text("Search", "", 100, flags=imgui.INPUT_TEXT_ENTER_RETURNS_TRUE)
                imgui.end_child()
             
            imgui.end_child()

        if True: 
            imgui.begin_child("2", border=False)
            changed, text_val = imgui.input_text("Message", "", 1_000_000, flags=imgui.INPUT_TEXT_ENTER_RETURNS_TRUE)
            if changed:
                if text_val: 
                    data = Message(
                        message = text_val, 
                        sender = self.client.username, 
                        receiver = self.to_user, 
                        timestamp = datetime.now().strftime('%m/%d/%Y %H:%M:%S'), 
                        sender_peername = self.client.sockname, 
                        type = MessageType.MESSAGE
                    ) 
                    self.send_string(data)  

                imgui.set_keyboard_focus_here()
            imgui.same_line()
            if imgui.button("Add files"):
                filepath = easygui.fileopenbox() 
                if filepath != None:
                    filesize = os.path.getsize(filepath)
                    if True: #round(filesize / 1_000_000) <= self.upload_limit: 
                        with open(filepath, 'rb') as file: 
                            filename = pathlib.Path(filepath).name
                            data = Message(
                                sender=self.client.username,
                                file = file.read(),  
                                filename = filename,
                                filesize = filesize, 
                                receiver = self.to_user, 
                                file_reference="{}-{}-{}".format(time.time(), self.client.username, self.to_user),
                                timestamp = datetime.now().strftime('%m/%d/%Y %H:%M:%S'), 
                                sender_peername = self.client.sockname, 
                                type = MessageType.FILE
                            )  
                            self.send_string(data) 
                    else: 
                        pass # TODO: info message
            imgui.same_line()
            if imgui.button("Stickers"):
                pass
            imgui.same_line()
            if imgui.button("GIF"):
                pass
            
            if True: 
                imgui.begin_child("3", border=True)  
                for user, value in self.client.users_chat_map.items():
                    if user == self.to_user:  
                        for i in range(len(value['messages']) - 1, -1, -1):
                            name = value['messages'][i]['name'] 
                            message = value['messages'][i]['message'] 
                            timestamp = value['messages'][i]['timestamp'] 
                            filename = value['messages'][i]['filename']
                            if str(search_text_val).casefold() in str(message).casefold():
                                message = "[{}] [{}]: {}".format(timestamp, name.split(" ")[0], message if not filename else filename)
                                if "] [You]:" in message: 
                                    imgui.push_style_color(imgui.COLOR_TEXT, 1, 1, 1) 
                                else:
                                    imgui.push_style_color(imgui.COLOR_TEXT, 0, 106 / 255, 1) 
                                imgui.text_wrapped(message)  
                                imgui.pop_style_color()   
                                if filename and imgui.is_item_hovered():
                                    imgui.set_tooltip("attachment")
                                    if imgui.core.is_item_clicked(0): 
                                        print("Clicked!") # TODO view image & video

                imgui.end_child()
            imgui.end_child()
        imgui.end()

    def profile(self): 
        imgui.set_next_window_size(300, self.window_height)
        imgui.set_next_window_position(0, 0)
        imgui.get_style().window_rounding = 0
        imgui.begin("Profile", flags= imgui.WINDOW_NO_COLLAPSE | imgui.WINDOW_NO_SCROLLBAR) 

        if True:
            imgui.begin_child("1", border=True, height=130) 
            img = cv2.imread(ROOT_DIR + "/assets/default_profile.png")  
            imgui_cv.image(img, width=65) 
            imgui.same_line()
            imgui.begin_child("1.1", border=True, height=65)
            imgui.push_font(self.fonts_map['profile-fonts-Maladewa-30']['font-obj'])  
            if self.client.username in self.client.fullname_map:
                imgui.text_wrapped(self.truncate(self.client.fullname_map[self.client.username], 20)) 
            else:
                imgui.text(self.truncate("-"*15, 20)) 
            imgui.pop_font()
            if imgui.is_item_hovered():
                imgui.set_tooltip(self.client.fullname_map[self.client.username])
            imgui.push_style_color(imgui.COLOR_TEXT, 0, 1, 0)
            imgui.text_wrapped("Active now")
            imgui.pop_style_color()
            imgui.end_child()
            changed, text_val = imgui.input_text("Search", "", 100, flags=imgui.INPUT_TEXT_ENTER_RETURNS_TRUE)
            imgui.button("Chats")
            imgui.same_line()
            imgui.button("Calls")
            imgui.same_line()
            imgui.button("Contacts")
            imgui.same_line()
            imgui.button("Notifications")
            imgui.end_child() 

        if True:
            imgui.begin_child("2", border=True)
            if changed:
                imgui.set_keyboard_focus_here()
            for i, (key, value) in enumerate(self.client.users_map.items()):
                if key == self.client.username:
                    continue
                if str(text_val).casefold() in key.casefold():   
                    if key in self.client.fullname_map:
                        imgui.push_font(self.fonts_map['profile-fonts-Drift']['font-obj']) 
                        if int(value['online']):
                            imgui.push_style_color(imgui.COLOR_TEXT, 0, 1, 0, 1)
                        else:
                            imgui.push_style_color(imgui.COLOR_TEXT, 1, 0, 0, 1) 
                        imgui.push_id(str(i) + key)
                        clicked, _ = imgui.selectable(label=self.client.fullname_map[key][0], flags=imgui.SELECTABLE_SPAN_ALL_COLUMNS | imgui.SELECTABLE_DONT_CLOSE_POPUPS)
                        if clicked:
                            self.to_user = key 
                            self.is_display_chatbox = True
                        imgui.pop_id()
                        imgui.pop_font()
                        imgui.pop_style_color()
                        
                        imgui.same_line()
                        imgui.set_cursor_pos_x(40)
                        if imgui.core.is_item_clicked(0):
                            self.to_user = key 
                            self.is_display_chatbox = True
                        imgui.begin_child(str(i) + "3", border=False, height=50)  
                        imgui.push_font(self.fonts_map['profile-fonts-Maladewa-x']['font-obj'])   
                        imgui.text(self.client.fullname_map[key]) 
                        imgui.pop_font() 
                        if type(value['last-message']) == type(None):
                            imgui.text_colored("-", 102 / 255, 99 / 255, 92 / 255)
                        else:
                            imgui.text_colored(self.truncate(value['last-message'], 30), 102 / 255, 99 / 255, 92 / 255)  
                        imgui.end_child() 

            imgui.end_child()
        imgui.end()

    def show_frames(self):
        self.is_display_frame = self.display_frames(self.fonts_map)  
        self.client.stop()  
    
if __name__ == "__main__":        
    # TODO: sending files percentage
    # TODO: view image & video
    # TODO: change profile picture
    # TODO: video & audio call 
    host = '127.0.0.1'
    login = Login(host=host)
    login.start() 
    if login.login_success:
        client = AppClient(host=host, is_resizeable=True)
        client.client.username = login.username 
        client.start() 