class UserModel(object):
    def __init__(self, 
            username: str, 
            password: str, 
            firstname: str, 
            middlename: str, 
            lastname: str
        ) -> None:
        self.username = username
        self.password = password
        self.firstname = firstname
        self.middlename = middlename
        self.lastname = lastname