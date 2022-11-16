class StatusModel(object):
    def __init__(self, 
            username: str, 
            isonline: int, 
            message: int
        ) -> None:
        self.username = username
        self.isonline = isonline
        self.message = message