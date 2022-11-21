from __future__ import annotations  
from sqlalchemy.orm import Session 

class Repository():
    def __init__(self, model) -> None: 
        self.model = model
        engine = self.engine_factory()
        self.session = Session(bind=engine)

    def insert(self, **kwargs):
        obj = self.model(**kwargs)
        self.session.add(obj)
        self.session.commit()

    def list(self):
        return list(self.session.query(self.model))

    def get(self, key):
        return self.session.query(self.model).get(key)

    def update(self, key, **fields):
        obj = self.get(key)
        for field, value in fields.items():
            obj.__setattr__(field, value)
        self.session.commit()

    def delete(self, id):
        self.session.delete(self.get(id))
        self.session.commit()

    def engine_factory(self):
        return NotImplementedError