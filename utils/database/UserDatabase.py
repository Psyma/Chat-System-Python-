from sqlalchemy.orm import Session
from sqlalchemy import Column, String, Integer
from sqlalchemy.ext.declarative import declarative_base

from utils.models.UserModel import UserModel 
Base = declarative_base()

class UserTable(Base):
    __tablename__ = "user"
    username = Column(String, primary_key=True)
    password = Column(String)
    firstname = Column(String)
    middlename = Column(String)
    lastname = Column(String)

    def __init__(self, model: UserModel) -> None:
        self.username = model.username
        self.password = model.password
        self.firstname = model.firstname
        self.middlename = model.middlename
        self.lastname = model.lastname

class UserDatabase(): 
    def __init__(self, session, engine) -> None:
        Base.metadata.create_all(engine)
        self.session: Session = session
        self.model = UserTable

    def create(self, model: UserModel):
        obj = self.model(model)
        self.session.add(obj)
        self.session.commit()

    def list(self) -> list[UserTable]:
        return list(self.session.query(self.model))

    def get(self, id) -> UserTable:
        return self.session.query(self.model).get(id)

    def update(self, id, **fields):
        obj = self.get(id)
        for field, value in fields.items():
            obj.__setattr__(field, value)
        self.session.commit()

    def delete(self, id):
        self.session.delete(self.get(id))
        self.session.commit()