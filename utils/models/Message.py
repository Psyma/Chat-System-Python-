from utils.models.MessageType import MessageType
from utils.database.Repository import User, Status, Chats 

class Message(object):
    def __init__(self, 
            image: bytes = None, 
            image_index: int = 0, 
            image_len: int = 0,  
            audio: bytes = None,
            message: str = None,
            message_id: int = None, 
            profile_picture: str = None,
            users: list[User] = [],
            upload_filebytes: bytes = None,  
            upload_filename: str = None,
            upload_file_percent: int = None,
            upload_filesize: int = None, 
            download_file_id: str = None, 
            download_filebytes: bytes = None,
            download_file_percent: int = None,
            download_filesize: int = None,
            download_filename: str = None,
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
            connected_users: list[Status] = [],
            history_messages: list[Chats] = [],
            type: MessageType = MessageType.DEFAULT) -> None:
            
        self.users = users
        self.image = image
        self.image_index = image_index
        self.image_len = image_len 
        self.audio = audio
        self.message = message
        self.message_id = message_id
        self.profile_picture = profile_picture
        self.upload_filebytes = upload_filebytes 
        self.upload_filename = upload_filename
        self.upload_file_percent = upload_file_percent
        self.upload_filesize = upload_filesize 
        self.download_filebytes = download_filebytes
        self.download_file_id = download_file_id
        self.download_file_percent = download_file_percent
        self.download_filesize = download_filesize
        self.download_filename = download_filename
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