from utils.models.MessageType import MessageType

class Message(object):
    def __init__(self, 
            image: bytes = None, 
            image_index: int = 0, 
            image_len: int = 0,  
            audio: bytes = None,
            message: str = None, 
            sender: str = None, 
            receiver: str = None, 
            timestamp: str = None, 
            sender_peername: tuple = None, 
            type: MessageType = MessageType.DEFAULT) -> None:
            
        self.image = image
        self.image_index = image_index
        self.image_len = image_len 
        self.audio = audio
        self.message = message
        self.sender = sender
        self.receiver = receiver
        self.timestamp = timestamp
        self.sender_peername = sender_peername 
        self.type = type