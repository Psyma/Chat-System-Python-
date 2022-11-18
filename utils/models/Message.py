from utils.models.MessageType import MessageType
from utils.database.StatusDatabase import StatusTable
from utils.database.ChatsDatabase import ChatsTable

class Message(object):
    def __init__(self, 
            image: bytes = None, 
            image_index: int = 0, 
            image_len: int = 0,  
            audio: bytes = None,
            message: str = None, 
            sender: str = None, 
            password: str = None,
            receiver: str = None, 
            timestamp: str = None, 
            sender_peername: tuple = None, 
            register_username: str = None,
            register_password: str = None,
            register_firstname: str = None,
            register_middlename: str = None,
            register_lastname: str = None,
            connected_users: list[StatusTable] = [],
            history_messages: list[ChatsTable] = [],
            type: MessageType = MessageType.DEFAULT) -> None:
            
        self.image = image
        self.image_index = image_index
        self.image_len = image_len 
        self.audio = audio
        self.message = message
        self.sender = sender
        self.receiver = receiver
        self.password = password
        self.timestamp = timestamp
        self.sender_peername = sender_peername 
        self.register_username = register_username
        self.register_password = register_password 
        self.register_firstname = register_firstname
        self.register_middlename = register_middlename
        self.register_lastname = register_lastname
        self.connected_users = connected_users
        self.history_messages = history_messages
        self.type = type