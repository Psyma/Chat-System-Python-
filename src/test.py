from sqlalchemy.orm import Session, sessionmaker
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

class Repository():
    def __init__(self, session: Session, engine, model) -> None:
        Base.metadata.create_all(engine)
        self.session: Session = session
        self.model = model

    def insert(self, **kwargs):
        obj = self.model(**kwargs)
        self.session.add(obj)
        self.session.commit()

if __name__ == "__main__":
    engine = create_engine('sqlite:///test.sqlite', echo=True)
    Session = sessionmaker(bind=engine)
    session = Session()

    userdb = Repository(session=session, engine=engine, model=UserModel)
    statusdb = Repository(session=session, engine=engine, model=StatusModel)
    #user = {
    #    'username': 'test1',
    #    'password': 'test1',
    #    'firstname': 'test1',
    #    'middlename': 'test1',
    #    'lastname': 'test1',
    #}
    #userdb.insert(**user)
