from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from users.models import Base as UserBase


engine = create_engine('sqlite:///mydatabase.db', echo=True)
session = sessionmaker(bind=engine)()


def create_db():
    UserBase.metadata.create_all(engine)

if __name__ == '__main__':
    create_db()
