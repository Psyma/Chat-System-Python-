from sqlalchemy.orm import Session
from sqlalchemy import Column, String, Integer
from sqlalchemy.ext.declarative import declarative_base

from utils.models.ChatsModel import ChatsModel 
Base = declarative_base()

class ChatsTable(Base):
    __tablename__ = "chats"
    id = Column(Integer, primary_key=True, autoincrement=True)
    sender = Column(String)
    receiver = Column(String)
    message = Column(String)
    timestamp = Column(String)
    peername = Column(String)

    def __init__(self, model: ChatsModel) -> None:
        self.sender = model.sender
        self.receiver = model.receiver
        self.message = model.message
        self.timestamp = model.timestamp
        self.peername = model.peername

class ChatsDatabase(): 
    def __init__(self, session, engine) -> None:
        Base.metadata.create_all(engine)
        self.session: Session = session
        self.model = ChatsTable

    def create(self, model: ChatsModel):
        obj = self.model(model)
        self.session.add(obj)
        self.session.commit()

    def list(self) -> list[ChatsTable]:
        return list(self.session.query(self.model))

    def get(self, id: int) -> ChatsTable:
        return self.session.query(self.model).get(id)

    def update(self, id: int, **fields):
        obj = self.get(id)
        for field, value in fields.items():
            obj.__setattr__(field, value)
        self.session.commit()

    def delete(self, id):
        self.session.delete(self.get(id))
        self.session.commit()