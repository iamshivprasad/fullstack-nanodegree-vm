from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy import create_engine, func
from passlib.apps import custom_app_context as pwd_context
from sqlalchemy.orm import aliased
import random
import string
import datetime
from itsdangerous import (TimedJSONWebSignatureSerializer as
                          Serializer, BadSignature, SignatureExpired)

Base = declarative_base()
secret_key = ''.join(random.choice(string.ascii_uppercase + string.digits)
                     for x in range(32))


class User(Base):
    __tablename__ = 'user'

    id = Column(Integer, primary_key=True)
    username = Column(String(32), nullable=False)
    picture = Column(String)
    email = Column(String)


class Category(Base):
    __tablename__ = 'category'

    id = Column(Integer, primary_key=True)
    name = Column(String(32), nullable=False)
    user_id = Column(Integer, ForeignKey('user.id'))
    user = relationship(User)

    @property
    def serialize(self):
        return
        {
            "name": self.name,
            "id": self.id
        }


class Item(Base):
    __tablename__ = 'item'

    id = Column(Integer, primary_key=True)
    title = Column(String(32), nullable=False)
    desc = Column(String(250))
    cat_id = Column(Integer, ForeignKey('category.id'))
    lastupdated = Column(DateTime, server_default=func.now(),
                         onupdate=func.now(), nullable=False)
    category = relationship(Category)

    @property
    def serialize(self):
        return
        {
            "cat_id": self.id,
            "description": self.desc,
            "id": self.id,
            "title": self.title
        }


engine = create_engine('sqlite:///itemcatalog.db')
Base.metadata.create_all(engine)
