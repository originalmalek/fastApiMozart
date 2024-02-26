from sqlalchemy import Column, String, Integer, ForeignKey


from database import Base


class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column('username', String(60), unique=True, nullable=False)
    password = Column('password', String(60), nullable=False)


class ExchangeKeys(Base):
    __tablename__ = 'exchange_key'
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), primary_key=True)
    api_key = Column('api_key',String(200))
    api_secret = Column('api_secret', String(200))
