from utils.database.Repository import Repository

from sqlalchemy import create_engine
from sqlalchemy import Column, String, Integer
from sqlalchemy.ext.declarative import declarative_base
Base = declarative_base()

class StatusModel(Base):
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

class StatusRepository(Repository):
    def __init__(self) -> None: 
        super().__init__(StatusModel)
        Base.metadata.create_all(self.engine_factory())

    def list(self) -> list[StatusModel]:
        return super().list()
    
    def get(self, key) -> StatusModel:
        return super().get(key)

    def engine_factory(self):
        return create_engine('sqlite:///database.sqlite', echo=True)