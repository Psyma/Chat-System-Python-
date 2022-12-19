from __future__ import annotations 
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

Base = declarative_base()

class User(Base):
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

class Status(Base):
    __tablename__ = "status"  
    username = Column(String, primary_key=True)
    isonline = Column(Integer)
    message = Column(String)
    new_message = Column(Integer)
    fullname = Column(String)

    def __init__(self, **kwargs) -> None: 
        self.username = kwargs['username']
        self.isonline = kwargs['isonline']
        self.message = kwargs['message']
        self.new_message = kwargs['new_message']
        self.fullname = kwargs['fullname']

class Chats(Base):
    __tablename__ = "chats"
    id = Column(Integer, primary_key=True, autoincrement=True)
    sender = Column(String)
    receiver = Column(String)
    message = Column(String)
    filename = Column(String)
    file_reference = Column(String)
    timestamp = Column(String)
    peername = Column(String)
    
    def __init__(self, **kwargs) -> None:
        self.sender = kwargs['sender']
        self.receiver = kwargs['receiver']
        self.message = kwargs['message']
        self.filename = kwargs['filename']
        self.file_reference = kwargs['file_reference']
        self.timestamp = kwargs['timestamp']
        self.peername = kwargs['peername']
        
class Repository:
    def __init__(self):
        engine = create_engine("sqlite:///database.db")
        Base.metadata.create_all(engine)
        self.session = sessionmaker(bind=engine)()

    def save(self, model, **kwargs):
        obj = model(**kwargs)
        self.session.add(obj)
        self.session.commit()

    def find(self, id, model) -> User | Status | Chats: 
        return self.session.query(model).get(id)

    def list(self, model) -> list[User | Status | Chats]:
        return self.session.query(model).all()

    def update(self, key, model, **fields):
        obj = self.find(key, model)
        for field, value in fields.items():
            obj.__setattr__(field, value)
        self.session.commit()

    def delete(self, id):
        obj = self.find(id)
        self.session.delete(obj)
        self.session.commit() 
