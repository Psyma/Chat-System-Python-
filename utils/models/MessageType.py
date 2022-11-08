from enum import Enum

class MessageType(Enum):
    DEFAULT = 0,
    MESSAGE = 1, 
    NON_MESSAGE = 2,
    CONNECTED = 3,
    DISCONNECTED = 4,
    IMAGE = 5,
    AUDIO = 6