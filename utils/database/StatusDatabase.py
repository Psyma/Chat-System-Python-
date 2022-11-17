from sqlalchemy.orm import Session
from sqlalchemy import Column, String, Integer
from sqlalchemy.ext.declarative import declarative_base

from utils.models.StatusModel import StatusModel 
Base = declarative_base()

class StatusTable(Base):
    __tablename__ = "status" 
    username = Column(String, primary_key=True)
    isonline = Column(Integer)
    message = Column(String)
    new_message = Column(Integer)
    fullname = Column(String)

    def __init__(self, model: StatusModel) -> None:
        self.username = model.username
        self.isonline = model.isonline
        self.message = model.message
        self.new_message = model.new_message
        self.fullname = model.fullname

class StatusDatabase(): 
    def __init__(self, session, engine) -> None:
        Base.metadata.create_all(engine)
        self.session: Session = session
        self.model = StatusTable

    def create(self, model: StatusModel):
        obj = self.model(model)
        self.session.add(obj)
        self.session.commit()

    def list(self) -> list[StatusTable]:
        return list(self.session.query(self.model))

    def get(self, id: int) -> StatusTable:
        return self.session.query(self.model).get(id)

    def update(self, id: str, **fields):
        obj = self.get(id)
        for field, value in fields.items():
            obj.__setattr__(field, value)
        self.session.commit()

    def delete(self, id):
        self.session.delete(self.get(id))
        self.session.commit()