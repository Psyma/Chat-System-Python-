from __future__ import annotations 
from sqlalchemy import create_engine, Column, Integer, String, BLOB
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

Base = declarative_base()

class User(Base):
    __tablename__ = "user"  
    id = Column(String)
    username = Column(String, primary_key=True)
    password = Column(String)
    firstname = Column(String)
    middlename = Column(String)
    lastname = Column(String)
    profile_picture = Column(BLOB)

    def __init__(self, **kwargs) -> None:
        self.id = kwargs['username']
        self.username = kwargs['username']
        self.password = kwargs['password']
        self.firstname = kwargs['firstname']
        self.middlename = kwargs['middlename']
        self.lastname = kwargs['lastname']
        self.profile_picture = kwargs['profile_picture']

class Status(Base):
    __tablename__ = "status"   
    id = Column(String)
    username = Column(String, primary_key=True)
    isonline = Column(Integer)
    message = Column(String)
    new_message = Column(Integer)
    fullname = Column(String)

    def __init__(self, **kwargs) -> None: 
        self.id = kwargs['username']
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
    filesize = Column(String)
    timestamp = Column(String)
    peername = Column(String)
    
    def __init__(self, **kwargs) -> None:
        self.sender = kwargs['sender']
        self.receiver = kwargs['receiver']
        self.message = kwargs['message']
        self.filename = kwargs['filename']
        self.filesize = kwargs['filesize']
        self.timestamp = kwargs['timestamp']
        self.peername = kwargs['peername']
        
class Repository:
    def __init__(self):
        engine = create_engine("sqlite:///database.db")
        Base.metadata.create_all(engine)
        self.session = sessionmaker(bind=engine)()

    def save(self, model, **kwargs):
        obj: User | Chats | Status = model(**kwargs)
        self.session.add(obj)
        self.session.commit() 
        return self.find(obj.id, model)

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
