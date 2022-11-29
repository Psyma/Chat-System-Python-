from enum import Enum

class MessageType(Enum):
    DEFAULT = 0,
    FILE = 1
    IMAGE = 2,
    AUDIO = 3,
    LOGIN = 4,
    MESSAGE = 5, 
    REGISTER = 6,
    CONNECTED = 7, 
    DISCONNECTED = 8,
    LOGIN_FAILED = 9,
    CHATS_HISTORY = 10,
    LOGIN_SUCCESS = 11,
    CONNECTED_USERS = 12,
    REGISTER_SUCESS = 13,
    REGISTER_FAILED = 14,