import os
import sys 
import imgui 

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
        for logs in self.server.server_logs:
            imgui.text_wrapped(logs)
        imgui.end()

    def show_frames(self, fonts_map: dict = {}):  
        ret = self.display_frames(fonts_map)
        self.server.stop()

    def start(self):
        self.server.start()
        
if __name__ == "__main__":    
    #import cv2
    #import numpy as np
#
    #image = cv2.imread(r"D:\PORTFOLIO\Chat System (Python)\assets\default_profile.png") 
    #
    #image = cv2.resize(image, (50, 50))
    #mask = np.zeros(image.shape, dtype=np.uint8)
    #x,y = int(image.shape[0] / 2), int(image.shape[1] / 2)
    #r = int(image.shape[0] * .5)
    #cv2.circle(mask, (x,y), r, (255,255,255), -1)
#
    ## Bitwise-and for ROI
    #ROI = cv2.bitwise_and(image, mask)
#
    ## Crop mask and turn background white
    #mask = cv2.cvtColor(mask, cv2.COLOR_BGR2GRAY)
    #x,y,w,h = cv2.boundingRect(mask)
    #result = ROI[y:y+h,x:x+w]
    #mask = mask[y:y+h,x:x+w]
    #result[mask==0] = (255,255,255)
#
    #cv2.imshow('result', result)
    #cv2.waitKey(0)
    #cv2.destroyAllWindows()
    #exit(1)
    app = AppServer(host='192.168.1.8') 
    app.start() 