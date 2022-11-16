class ChatsModel(object):
    def __init__(self, 
            username: str, 
            message: str
        ) -> None:
        self.username = username
        self.message = message