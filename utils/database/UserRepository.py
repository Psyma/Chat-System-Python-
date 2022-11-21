from utils.database.Repository import Repository

from sqlalchemy import create_engine
from sqlalchemy import Column, String, Integer
from sqlalchemy.ext.declarative import declarative_base
Base = declarative_base()

class UserModel(Base):
    __tablename__ = "user" 
    username = Column(String, primary_key=True)
    password = Column(String)
    firstname = Column(String)
    middlename = Column(String)
    lastname = Column(String)

    def __init__(self, **kwargs) -> None:
        self.username = kwargs['username']
        self.password = kwargs['password']
        self.firstname = kwargs['firstname']
        self.middlename = kwargs['middlename']
        self.lastname = kwargs['lastname']

class UserRepository(Repository):
    def __init__(self) -> None: 
        super().__init__(UserModel)
        Base.metadata.create_all(self.engine_factory())

    def list(self) -> list[UserModel]:
        return super().list()

    def get(self, key) -> UserModel:
        return super().get(key)

    def engine_factory(self):
        return create_engine('sqlite:///database.sqlite', echo=True)
        