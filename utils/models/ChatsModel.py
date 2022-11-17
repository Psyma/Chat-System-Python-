class ChatsModel(object):
    def __init__(self, 
            sender: str,
            receiver: str, 
            message: str,
            timestamp: str,
            peername: str
        ) -> None:
        self.sender = sender
        self.receiver = receiver
        self.message = message
        self.timestamp = timestamp
        self.peername = peername