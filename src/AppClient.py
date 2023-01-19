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
import imutils
import numpy as np

from threading import Thread 
from datetime import datetime 
from imgui_datascience import *
from imgui_datascience.example import *

CUR_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.join(CUR_DIR, '..')
sys.path.append(ROOT_DIR)

from queue import Queue
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
        self.is_audio_call: bool = False
        self.video_stream = VideoStream(0) 
        self.is_display_frame: bool = True
        self.string_stream = StringStream()
        self.is_display_chatbox: bool = False
        self.audio_stream = AudioStream(MS, RATE, AUDIO, FORMAT, CHANNELS)    
        self.client = Client(host=host, tcp_port=tcp_port, udp_port=udp_port)
        self.fonts_map: dict[str, dict[str, None | int | str]] = self.set_fonts()

        self.password: str = ""  
        self.is_login: bool = False
        self.is_register: bool = False
        self.register_username: str = ""
        self.register_password: str = ""
        self.register_password_confirm: str = ""
        self.register_firstname: str = ""
        self.register_middlename: str = ""
        self.register_lastname: str = ""  

        self.delay_counter: int = 1
        self.loading_delay: int = 4
        self.upload_limit: int = 300
        self.uploadingQs: Queue = Queue()
        self.downloadingQs: Queue = Queue()
        self.is_connected: bool = False 
        self.loading_delay_counter: int = 1
        self.sending_files_map: dict[str, str] = {}
        self.downloading_files_map: dict[str, str] = {}
        self.is_show_image: bool = False
        self.show_filepath: str = None
        self.is_click_file: bool = False
        self.click_filename: str = None
        self.download_confirmation_data: Message = None
        self.func_download_confirmation = None

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
                sender_peername = self.client.string_sockname,
                timestamp = datetime.now().strftime('%m/%d/%Y %H:%M:%S.%f'), 
                type = MessageType.CONNECTED
            )  
            self.send_string(data)

        self.upload_files_Qs()
        self.download_files_Qs()
        self.profile() 
        if self.is_display_chatbox:
            self.chatbox()
        #self.view_image()
        self.download_confirmation()
        self.loading()   

    def download_confirmation(self):
        if self.is_click_file:
            imgui.set_next_window_focus() 
            imgui.set_next_window_size(250, 120)
            imgui.set_next_window_position((self.window_width - 200) * .50, (self.window_height - 120) * .50) 
            imgui.push_id('info-4')
            imgui.open_popup("[INFO]")
            if imgui.begin_popup_modal("[INFO]", flags=imgui.WINDOW_NO_RESIZE)[0]:   
                text = "Do you want to download " + self.click_filename + " ?"
                width, height = imgui.get_window_size() 
                imgui.set_cursor_pos_y(35)  
                imgui.text_wrapped(text) 
                imgui.invisible_button("btn", height=5, width=5)
                imgui.set_cursor_pos_x((width - (70 * 2)) * 0.5)
                if imgui.button("Continue", width=70):
                    self.client.downloading_files_map[self.download_confirmation_data.download_filename] = 0
                    self.downloadingQs.put(self.func_download_confirmation)
                    self.downloading_files_map[self.download_confirmation_data.download_filename] = self.func_download_confirmation
                    self.is_click_file = False
                imgui.same_line()
                if imgui.button("Cancel", width=70): 
                    self.is_click_file = False
                imgui.end_popup()
                imgui.pop_id()

    def view_image(self):
        if self.is_show_image:
            frame = cv2.imread(self.show_filepath)
            image = frame.copy()
            width = image.shape[1]
            height = image.shape[0]

            if width >= 1024:
                width = 740
            if height >= 768:
                height = 580

            imgui.set_next_window_focus()  
            imgui.begin("Image", flags=imgui.WINDOW_ALWAYS_AUTO_RESIZE) 
            imgui_cv.image(image, width=width, height=height)
            width, height = imgui.get_window_size()
            imgui.set_cursor_pos_x((width - 50) * .50)
            if imgui.button("Close", width=50):
                self.is_show_image = False
            imgui.end()

    def uploading(self): 
        width, height = imgui.get_window_size()
        x, y = imgui.get_window_position() 
        imgui.set_next_window_focus() 
        imgui.set_next_window_size(width / 2, height)
        imgui.set_next_window_position(x, y)
        imgui.begin("Uploading files", flags=imgui.WINDOW_NO_FOCUS_ON_APPEARING) 
        imgui.columns(3, 'upload_list') 
        imgui.set_column_width(1, 85)
        imgui.set_column_width(2, 120)
        imgui.separator()
        imgui.text("Filename")
        imgui.next_column()
        imgui.text("Percentage")
        imgui.next_column()  
        imgui.text("Action")
        imgui.next_column()  
        imgui.separator() 
        
        for filename, func in list(self.sending_files_map.items()):
            stem = pathlib.Path(filename).stem
            suffix = pathlib.Path(filename).suffix
            name = "{}...{}{}".format(stem[:3], stem[-2:], suffix)
            imgui.text(name)
            if imgui.is_item_hovered():
                imgui.set_tooltip(filename)
            imgui.next_column()  
            if self.client.uploading_files_map[filename] == "Failed":
                imgui.push_style_color(imgui.COLOR_TEXT, 1, 0, 0)
            else:
                imgui.push_style_color(imgui.COLOR_TEXT, 0, 1, 0)
            imgui.text("{}%".format(self.client.uploading_files_map[filename]) if str(self.client.uploading_files_map[filename]).isnumeric() else self.client.uploading_files_map[filename])
            imgui.pop_style_color()
            imgui.next_column()  
            imgui.push_id(filename + "Resend")
            if imgui.button("Resend"):
                if self.client.can_upload_file:
                    self.client.can_upload_file = False
                    func()
            imgui.pop_id()
            imgui.same_line()
            imgui.push_id(filename + "Remove")
            if imgui.button("Remove"):
                if self.client.uploading_files_map[filename] == 100 or self.client.uploading_files_map[filename] == "Failed":
                    del self.sending_files_map[filename]
            imgui.pop_id()
            imgui.next_column()  
        imgui.columns(1)
        imgui.end() 
    
    def downloading(self):
        width, height = imgui.get_window_size()
        x, y = imgui.get_window_position() 
        imgui.set_next_window_focus() 
        imgui.set_next_window_size(width / 2, height)
        imgui.set_next_window_position(x + (width / 2), y)
        imgui.begin("Downloading files")
        imgui.columns(3, 'download_list') 
        imgui.set_column_width(1, 85)
        imgui.set_column_width(2, 120)
        imgui.separator()
        imgui.text("Filename")
        imgui.next_column()
        imgui.text("Percentage")
        imgui.next_column()  
        imgui.text("Action")
        imgui.next_column()  
        imgui.separator() 

        for filename, func in list(self.downloading_files_map.items()):
            stem = pathlib.Path(filename).stem
            suffix = pathlib.Path(filename).suffix
            name = "{}...{}{}".format(stem[:3], stem[-2:], suffix)
            imgui.text(name)
            if imgui.is_item_hovered():
                imgui.set_tooltip(filename)
            imgui.next_column()  
            if self.client.downloading_files_map[filename] == "Failed":
                imgui.push_style_color(imgui.COLOR_TEXT, 1, 0, 0)
            else:
                imgui.push_style_color(imgui.COLOR_TEXT, 0, 1, 0)
            imgui.text("{}%".format(self.client.downloading_files_map[filename]) if str(self.client.downloading_files_map[filename]).isnumeric() else self.client.downloading_files_map[filename])
            imgui.pop_style_color()
            imgui.next_column()  
            imgui.push_id(filename + "Resend")
            if imgui.button("Resend"):
                if self.client.can_download_file:
                    self.client.can_download_file = False
                    func()
            imgui.pop_id()
            imgui.same_line()
            imgui.push_id(filename + "Remove")
            if imgui.button("Remove"):
                if self.client.downloading_files_map[filename] == 100 or self.client.downloading_files_map[filename] == "Failed":
                    del self.downloading_files_map[filename]
            imgui.pop_id()
            imgui.next_column()

        imgui.columns(1)
        imgui.end()

    def upload_files_Qs(self):
        if not self.uploadingQs.empty() and self.client.can_upload_file:
            self.client.can_upload_file = False
            func = self.uploadingQs.get()
            func()

    def download_files_Qs(self):
        if not self.downloadingQs.empty() and self.client.can_download_file:
            self.client.can_download_file = False
            func = self.downloadingQs.get()
            func()

    def loading(self):
        imgui.set_next_window_focus() 
        imgui.set_next_window_size(165, 100)
        imgui.set_next_window_position((self.window_width - 165) * .50, (self.window_height - 100) * .50)
        if not self.is_connected:
            imgui.push_id('info-3')
            imgui.open_popup("[INFO]")
            self.client.can_upload_file = True 
            self.client.can_download_file = True
            for filename, percentage in self.sending_files_map.items():
                if self.client.uploading_files_map[filename] != 100:
                    self.client.uploading_files_map[filename] = "Failed" 
            for filename, percentage in self.downloading_files_map.items():
                if self.client.downloading_files_map[filename] != 100:
                    self.client.downloading_files_map[filename] = "Failed"
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
                if i == self.loading_delay_counter: 
                    imgui.push_style_color(imgui.COLOR_TEXT, 0, 1, 0)  
                    imgui.bullet()
                    imgui.pop_style_color()
                else:
                    imgui.bullet()

            if self.loading_delay_counter == 7:
                if self.delay_counter == self.loading_delay:
                    self.loading_delay_counter = 0
            if self.delay_counter == self.loading_delay:
                self.delay_counter = 0
                self.loading_delay_counter = self.loading_delay_counter + 1
            
            imgui.end_popup()
            imgui.pop_id()

    def send_string(self, data: Message):
        self.string_stream.send(data, self.client.string_transport) 
        
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
                timestamp=datetime.now().strftime('%m/%d/%Y %H:%M:%S.%f'), 
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
            timestamp=datetime.now().strftime('%m/%d/%Y %H:%M:%S.%f'), 
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
            "profile-fonts-ArialUnicodeMS" : {
                "font-obj" : None,
                "font-size" : 14.5,
                "font-path" : ROOT_DIR + "/assets/ArialUnicodeMS.ttf"
            },
        } 

        return fonts_map

    def chatbox(self): 
        imgui.set_next_window_size(self.window_width - 299, self.window_height)
        imgui.set_next_window_position(299, 0)
        imgui.begin("Chatbox", flags=imgui.WINDOW_NO_COLLAPSE)
        
        if True:
            imgui.begin_child("1", border=False, height=65, flags=imgui.WINDOW_NO_SCROLLBAR)
            if self.to_user in self.client.profile_pictures:
                image = self.client.profile_pictures[self.to_user]
                image = np.frombuffer(image, np.uint8)
                image = cv2.imdecode(image, cv2.IMREAD_COLOR)
                imgui_cv.image(image, width=65, height=64) 
            else: 
                image = cv2.imread(ROOT_DIR + "/assets/default_profile.png")  
                imgui_cv.image(image, width=65, height=64)  
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
                        timestamp = datetime.now().strftime('%m/%d/%Y %H:%M:%S.%f'), 
                        sender_peername = self.client.string_sockname, 
                        type = MessageType.MESSAGE
                    ) 
                     
                    self.send_string(data)

                imgui.set_keyboard_focus_here()
            imgui.same_line()
            if imgui.button("Add files"):
                filepath = easygui.fileopenbox() 
                if filepath != None:
                    filesize = os.path.getsize(filepath)
                    if round(filesize / 1_000_000) <= self.upload_limit: 
                        with open(filepath, 'rb') as file: 
                            filename = pathlib.Path(filepath).name
                            data = Message(
                                sender=self.client.username,
                                upload_filebytes = file.read(),  
                                upload_filename = filename,
                                upload_filesize = filesize, 
                                receiver = self.to_user, 
                                timestamp = datetime.now().strftime('%m/%d/%Y %H:%M:%S.%f'), 
                                sender_peername = self.client.string_sockname, 
                                type = MessageType.FILE
                            )

                            def upload(data: Message, client: Client):
                                client.upload_filename = data.upload_filename
                                data = pickle.dumps(data)
                                client.upload_filesize = len(data)
                                client.upload_transport.write(data)

                            self.client.uploading_files_map[data.upload_filename] = 0
                            self.uploadingQs.put(lambda: upload(data, self.client))
                            self.sending_files_map[data.upload_filename] = lambda: upload(data, self.client)
                    else: 
                        pass # TODO: info message
            imgui.same_line()
            if imgui.button("Stickers"):
                pass
            imgui.same_line()
            if imgui.button("GIF"):
                pass
            
            imgui.begin_child("3", border=True)   
            self.uploading()
            self.downloading()
            imgui.invisible_button("Button", 200, 10)
            if True: 
                for user, value in self.client.users_chat_map.items():
                    if user == self.to_user:   
                        for i in range(len(value['messages']) - 1, -1, -1):
                            id = value['messages'][i]['id']
                            name = value['messages'][i]['name'] 
                            message = value['messages'][i]['message'] 
                            timestamp = value['messages'][i]['timestamp'] 
                            filename = value['messages'][i]['filename']
                            filesize = value['messages'][i]['filesize']
                            if str(search_text_val).casefold() in str(message).casefold() or str(search_text_val).casefold() in str(filename).casefold():
                                if filename:
                                    stem = pathlib.Path(filename).stem
                                    suffix = pathlib.Path(filename).suffixes
                                message = "[{}] [{}]: {}".format(timestamp, name.split(" ")[0], message if not filename else filename if len(filename) < 15 else stem[:15] + "..." + stem[-5:] + suffix[len(suffix) - 1])
                                if "] [You]:" in message: 
                                    imgui.push_style_color(imgui.COLOR_TEXT, 1, 1, 1) 
                                else:
                                    imgui.push_style_color(imgui.COLOR_TEXT, 0, 106 / 255, 1) 
                                imgui.text_wrapped(message)  
                                imgui.pop_style_color()   
                                if filename and imgui.is_item_hovered():
                                    imgui.set_tooltip(filename)
                                    if imgui.core.is_item_clicked(0):   
                                        self.is_show_image = True
                                        self.is_click_file = True
                                        self.click_filename = filename
                                        data = Message(
                                            download_file_id=id,
                                            download_filename=filename,
                                            download_filesize=filesize,
                                            sender=self.client.username,
                                            receiver=self.to_user,
                                            timestamp = timestamp, 
                                            sender_peername = self.client.download_sockname, 
                                            type=MessageType.DOWNLOAD
                                        ) 

                                        def download(data: Message, client: Client):
                                            client.download_filename = data.download_filename
                                            client.download_filesize = data.download_filesize
                                            data = pickle.dumps(data)
                                            client.string_transport.write(data) 
                                        
                                        self.download_confirmation_data = data
                                        self.func_download_confirmation = lambda: download(data, self.client) 
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
            if self.client.username in self.client.profile_pictures:
                image = self.client.profile_pictures[self.client.username]
                image = np.frombuffer(image, np.uint8)
                image = cv2.imdecode(image, cv2.IMREAD_COLOR)
                imgui_cv.image(image, width=65, height=64) 
            else: 
                image = cv2.imread(ROOT_DIR + "/assets/default_profile.png")  
                imgui_cv.image(image, width=65, height=64)  
            if imgui.core.is_item_clicked(0):
                filepath = easygui.fileopenbox(title="Select Image")
                if filetype.is_image(filepath):  
                    image = cv2.imread(filepath)
                    image = imutils.resize(image, width=65, height=65)
                    success, image = cv2.imencode('.jpg', image)
                    image = image.tobytes()
                    
                    data = Message( 
                        profile_picture = image,
                        sender = self.client.username, 
                        receiver = self.to_user, 
                        timestamp = datetime.now().strftime('%m/%d/%Y %H:%M:%S.%f'), 
                        sender_peername = self.client.string_sockname, 
                        type = MessageType.PROFILE_PICTURE
                    ) 
                     
                    self.send_string(data)

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
    # TODO: share screen
    # TODO: video & audio call  
    host = '127.0.0.1'
    login = Login(host=host)
    login.start() 
    if login.is_login_success:
        client = AppClient(host=host, is_resizeable=True)
        client.client.username = login.login_username 
        client.start() 