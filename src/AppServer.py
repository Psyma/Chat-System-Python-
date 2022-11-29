import os
import sys 
import imgui 
import logging
logging.disable(logging.WARNING)

CUR_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.join(CUR_DIR, '..')
sys.path.append(ROOT_DIR)

from threading import Thread
from utils.frontend.Gui import Gui
from utils.backend.Server import Server

class AppServer(Gui):
    def __init__(self, 
                window_name="", 
                window_width=800, 
                window_height=600, 
                is_resizeable=False, 
                host="127.0.0.1", 
                tcp_port=9999, 
                udp_port=6666) -> None: 
        super().__init__(window_name, window_width, window_height, is_resizeable)

        self.server = Server(host=host, tcp_port=tcp_port, udp_port=udp_port) 
        Thread(target=self.show_frames, args=()).start()

    def frame_commands(self):
        imgui.begin("Video")
        for i in range(len(self.server.server_logs) - 1, -1, -1): 
            imgui.text_wrapped(self.server.server_logs[i])
        imgui.end()

    def show_frames(self, fonts_map: dict = {}):  
        ret = self.display_frames(fonts_map)
        self.server.stop()

    def start(self):
        self.server.start()
        
if __name__ == "__main__":    
    app = AppServer(host='127.0.0.1') 
    app.start() 