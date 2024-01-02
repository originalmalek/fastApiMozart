from sqlalchemy import Column, String, Integer, ForeignKey


from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()




class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column('username', String(60), unique=True)
    password = Column('password', String(60))

class ExchangeKeys(Base):
    __tablename__ = 'exchange_key'
    id_user = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), primary_key=True)
    api_key = Column('api_key',String(200))
    api_secret = Column('api_secret', String(200))
