import os
import sys 
import imgui 

CUR_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.join(CUR_DIR, '..')
sys.path.append(ROOT_DIR)

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from threading import Thread
from utils.frontend.Gui import Gui
from utils.backend.Server import Server
from utils.models.UserModel import UserModel
from utils.models.ChatsModel import ChatsModel
from utils.models.StatusModel import StatusModel
from utils.database.UserDatabase import UserDatabase
from utils.database.ChatsDatabase import ChatsDatabase
from utils.database.StatusDatabase import StatusDatabase

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
        engine = create_engine('sqlite:///database.sqlite', echo=True)
        Session = sessionmaker(bind=engine)
        session = Session()
        
        self.userdb = UserDatabase(session=session, engine=engine)
        self.chatsdb = ChatsDatabase(session=session, engine=engine)
        self.statusdb = StatusDatabase(session=session, engine=engine) 
        Thread(target=self.show_frames, args=()).start()

    def frame_commands(self):
        imgui.begin("Video")
        for logs in self.server.server_logs:
            imgui.text_wrapped(logs)
        imgui.end()

    def show_frames(self, fonts_map: dict = {}):  
        ret = self.display_frames(fonts_map)
        self.server.stop()

    def start(self):
        self.server.start()
        
if __name__ == "__main__": 
    app = AppServer(host='192.168.1.8') 
    app.start() 