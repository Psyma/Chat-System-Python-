class StatusModel(object):
    def __init__(self, 
            username: str, 
            isonline: int,
            message: str, 
            new_message: int,
            fullname: str
        ) -> None:
        self.username = username
        self.isonline = isonline
        self.message = message
        self.new_message = new_message
        self.fullname = fullname