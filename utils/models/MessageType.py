from enum import Enum

class MessageType(Enum):
    DEFAULT = 0,
    IMAGE = 1,
    AUDIO = 2,
    MESSAGE = 3, 
    REGISTER = 4,
    CONNECTED = 5, 
    DISCONNECTED = 6,
    LOGIN = 7,
    CONNECTED_USERS = 8,
    CHATS_HISTORY = 9