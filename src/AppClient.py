from __future__ import annotations 
import os
import cv2
import sys  
import time
import imgui 
import socket
import pickle
import base64
import pyaudio

from threading import Thread 
from datetime import datetime 
from imgui_datascience import *

CUR_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.join(CUR_DIR, '..')
sys.path.append(ROOT_DIR)

from utils.frontend.Gui import Gui
from utils.backend.Client import Client
from utils.models.Message import Message
from utils.models.MessageType import MessageType
from utils.messaging.VideoStream import VideoStream
from utils.messaging.AudioStream import AudioStream
from utils.messaging.StringStream import StringStream

class AppClient(Gui):
    def __init__(self, 
                window_name="", 
                window_width=360, 
                window_height=450, 
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

        self.to_user: str = "" 
        self.password: str = ""
        self.login: bool = False
        self.display_chatbox: bool = False
        self.is_display_frame: bool = True
        self.fonts_map = self.set_fonts()
        self.client = Client(host=host, tcp_port=tcp_port, udp_port=udp_port)
        self.string_stream = StringStream()
        self.video_stream = VideoStream(0) # TODO:
        self.audio_stream = AudioStream(MS, RATE, AUDIO, FORMAT, CHANNELS) # TODO:

    def start(self): 
        self.t = Thread(target=self.show_frames, args=())
        self.t.start()
        while self.is_display_frame:
            try:
                if self.login:
                    self.client.start()
            except: 
                pass 
            time.sleep(1) 

    def send_string(self, data: Message):
        self.string_stream.send(data, self.client.tcp_transport)
        message = "[{}] [{}]: {}".format(datetime.now().strftime('%m/%d/%Y %H:%M:%S'), "You", data.message) 
        self.client.users_chat_map[data.receiver]['messages'].append(message)

    def send_image(self, frame, size = 65536): 
        encoded, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
        frames = base64.b64encode(buffer)

        chunks = [frames[i:i+size] for i in range(0,len(frames), size)] 
        for i, chunk in enumerate(chunks):
            data = Message(image=chunk, 
                            image_index=i, 
                            image_len=len(chunks) - 1,  
                            sender=self.client.username, 
                            receiver=self.to_user, 
                            timestamp=datetime.now().strftime('%m/%d/%Y %H:%M:%S'), 
                            type=MessageType.MESSAGE) 
                                
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) 
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, size)
            self.socket.sendto(pickle.dumps(data), self.client.udp_peername)
    
    def send_audio(self, frame, size: int = 65536):
        data = Message(audio=frame, 
                        sender=self.client.username, 
                        receiver=self.to_user, 
                        timestamp=datetime.now().strftime('%m/%d/%Y %H:%M:%S'), 
                        type=MessageType.MESSAGE) 
        
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) 
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, size)
        self.socket.sendto(pickle.dumps(data), self.client.udp_peername)

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
            "profile-fonts-Drift" : {
                "font-obj" : None,
                "font-size" : 35,
                "font-path" : ROOT_DIR + "/assets/Drift.ttf"
            },
            "profile-fonts-Maladewa" : {
                "font-obj" : None,
                "font-size" : 40,
                "font-path" : ROOT_DIR + "/assets/Maladewa.ttf"
            }
        } 

        return fonts_map

    def chat_box(self): 
        imgui.begin('mainwindow', flags=imgui.WINDOW_MENU_BAR | imgui.WINDOW_NO_TITLE_BAR | imgui.WINDOW_NO_RESIZE)
        if imgui.begin_menu_bar():
            if imgui.begin_menu('Options'):
                click_back, _ = imgui.menu_item('Back')
                click_audio_call, _ = imgui.menu_item('Audio Call')
                click_video_call, _ = imgui.menu_item('Video Call')

                if click_back:
                    self.display_chatbox = False
                elif click_audio_call:
                    pass
                elif click_video_call:
                    pass
                imgui.end_menu()

            imgui.end_menu_bar()

        imgui.set_cursor_pos_y(18)
        imgui.push_font(self.fonts_map['profile-fonts-Maladewa']['font-obj'])
        imgui.text_wrapped(self.to_user)
        imgui.pop_font()  

        changed, text_val = imgui.input_text("Message", "", 100, flags=imgui.INPUT_TEXT_ENTER_RETURNS_TRUE)
        if changed: 
            data = Message(message=text_val, 
                            sender=self.client.username, 
                            receiver=self.to_user, 
                            timestamp=datetime.now().strftime('%m/%d/%Y %H:%M:%S'), 
                            sender_peername=self.client.sockname, 
                            type=MessageType.MESSAGE)
            self.send_string(data)
            imgui.set_keyboard_focus_here()

        imgui.begin_child('chatbox', border=True)
        for user, value in self.client.users_chat_map.items():
            if user == self.to_user: 
                for data in value['messages']:
                    imgui.text_wrapped(data)
                if not value['images'].empty():
                    image = value['images'].get() 
                    imgui.begin_child('Video')
                    imgui_cv.image(image)
                    imgui.end_child()

        imgui.end_child()
        imgui.end()

    def profile(self):
        imgui.begin_child("secondarywindow", border=False)
        if not len(self.client.users_map):
            imgui.push_font(self.fonts_map['profile-fonts-Drift']['font-obj'])
            imgui.push_style_color(imgui.COLOR_TEXT, 1, 0, 0, 1)
            text = "no friends online!"
            text_width = imgui.calc_text_size(text)[0]
            window_width = imgui.get_window_size()[0]
            text_height = imgui.calc_text_size(text)[1]
            window_height = imgui.get_window_size()[1]
            imgui.set_cursor_pos_x((window_width - text_width) * 0.5)
            imgui.set_cursor_pos_y((window_height - text_height) * 0.5)
            imgui.text_wrapped(text)
            imgui.pop_style_color()
            imgui.pop_font()
        else:
            changed, text_val = imgui.input_text("Search", "", 20, flags=imgui.INPUT_TEXT_ENTER_RETURNS_TRUE | imgui.INPUT_TEXT_ALWAYS_INSERT_MODE)
            if changed:
                imgui.set_keyboard_focus_here()

            for i, (key, value) in enumerate(self.client.users_map.items()):
                if str(text_val).casefold() in key.casefold():
                    imgui.push_font(self.fonts_map['profile-fonts-Drift']['font-obj'])

                    if value['online']:
                        imgui.push_style_color(imgui.COLOR_TEXT, 0, 1, 0, 1)
                    else:
                        imgui.push_style_color(imgui.COLOR_TEXT, 1, 0, 0, 1)

                    imgui.set_cursor_pos_x(5)
                    imgui.push_id(key)
                    clicked, _ = imgui.selectable(label=key[0], flags=imgui.SELECTABLE_SPAN_ALL_COLUMNS | imgui.SELECTABLE_DONT_CLOSE_POPUPS)
                    if clicked:
                        self.to_user = key
                        self.display_chatbox = True
                    imgui.pop_id()

                    imgui.pop_font()
                    imgui.pop_style_color()

                    imgui.same_line()
                    imgui.set_cursor_pos_x(40)
                    imgui.push_font(self.fonts_map['profile-fonts-Bebas']['font-obj'])
                    imgui.text_wrapped("{}\n{}".format(key, value['last-message']))
                    imgui.pop_font()
                    imgui.same_line()

                    if value['new-message']:
                        imgui.push_font(self.fonts_map['profile-fonts-Montserrat']['font-obj'])
                        imgui.push_style_color(imgui.COLOR_TEXT, 135 / 255, 206 / 255, 235 / 255, 1)
                        imgui.bullet()
                        imgui.pop_style_color()
                        imgui.pop_font()

                    imgui.separator()
        imgui.end_child()

    def user_login(self):
        if not self.login:
            imgui.set_next_window_position((self.window_width / 2) - 150, (self.window_height / 2) - 50)
            imgui.set_next_window_size(300, 100)
            imgui.open_popup("Login")
        if imgui.begin_popup_modal(title="Login", visible=None, flags=imgui.WINDOW_ALWAYS_AUTO_RESIZE | imgui.WINDOW_NO_MOVE)[0]:
            imgui.text("Username:")
            imgui.same_line()
            ret, value = imgui.input_text(label=" ", value=self.client.username, buffer_length=20, flags=imgui.INPUT_TEXT_ENTER_RETURNS_TRUE)
            if not ret:
                self.client.username = value
            imgui.text("Password:")
            imgui.same_line()
            ret, value = imgui.input_text(label="  ", value=self.password, buffer_length=20, flags=imgui.INPUT_TEXT_ENTER_RETURNS_TRUE | imgui.INPUT_TEXT_PASSWORD)
            if not ret:
                self.password = value

            imgui.set_cursor_pos_y(73)
            imgui.set_cursor_pos_x(100)
            if imgui.button("Login", width=50):
                pass
            imgui.same_line()
            if imgui.button("Exit", width=50):
                pass

            if ret and self.client.username != "" and self.password != "":
                self.login = True
                self.user = self.client.username
                imgui.close_current_popup()
            imgui.end_popup()
    
    def frame_commands(self): 
        imgui.set_next_window_size(self.window_width, self.window_height)
        imgui.set_next_window_position(0, 0)
        if self.display_chatbox:
            self.chat_box()
        else:
            imgui.get_style().window_rounding = 0
            imgui.begin("mainwindow", flags=imgui.WINDOW_NO_TITLE_BAR | imgui.WINDOW_NO_RESIZE | imgui.WINDOW_NO_COLLAPSE)
            self.user_login() 
            if self.login:
                imgui.text(self.client.username)
                self.profile()   
            imgui.end()

    def show_frames(self):
        self.is_display_frame = self.display_frames(self.fonts_map)
        if self.login:
            self.client.stop()

if __name__ == "__main__":   
    client = AppClient(host='192.168.1.2')
    client.start()