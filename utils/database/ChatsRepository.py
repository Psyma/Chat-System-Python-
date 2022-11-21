from utils.database.Repository import Repository

from sqlalchemy import create_engine
from sqlalchemy import Column, String, Integer
from sqlalchemy.ext.declarative import declarative_base
Base = declarative_base()

class ChatsModel(Base):
    __tablename__ = "chats"
    id = Column(Integer, primary_key=True, autoincrement=True)
    sender = Column(String)
    receiver = Column(String)
    message = Column(String)
    timestamp = Column(String)
    peername = Column(String)
    
    def __init__(self, **kwargs) -> None:
        self.sender = kwargs['sender']
        self.receiver = kwargs['receiver']
        self.message = kwargs['message']
        self.timestamp = kwargs['timestamp']
        self.peername = kwargs['peername']

class ChatsRepository(Repository):
    def __init__(self) -> None: 
        super().__init__(ChatsModel)
        Base.metadata.create_all(self.engine_factory())

    def list(self) -> list[ChatsModel]:
        return super().list()

    def get(self, key) -> ChatsModel:
        return super().get(key)
    
    def engine_factory(self):
        return create_engine('sqlite:///database.sqlite', echo=True)