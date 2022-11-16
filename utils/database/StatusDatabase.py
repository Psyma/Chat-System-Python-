from sqlalchemy.orm import Session
from sqlalchemy import Column, String, Integer
from sqlalchemy.ext.declarative import declarative_base

from utils.models.StatusModel import StatusModel 
Base = declarative_base()

class StatusTable(Base):
    __tablename__ = "status"
    id = Column(Integer, primary_key=True, auto_increment=True)
    username = Column(String)
    isonline = Column(Integer)
    message = Column(Integer)

    def __init__(self, model: StatusModel) -> None:
        self.username = model.username
        self.isonline = model.isonline
        self.message = model.message

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

    def get(self, id) -> StatusTable:
        return self.session.query(self.model).get(id)

    def update(self, id, **fields):
        obj = self.get(id)
        for field, value in fields.items():
            obj.__setattr__(field, value)
        self.session.commit()

    def delete(self, id):
        self.session.delete(self.get(id))
        self.session.commit()