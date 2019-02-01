from sqlalchemy import create_engine
from sqlalchemy import Column, Integer
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from config import url
Base = declarative_base()


class User(Base):
    __tablename__ = 'users'

    user_id = Column(Integer, primary_key=True)
    msg_count = Column(Integer)
    ro_level = Column(Integer)

    def __init__(self, user_id):
        self.user_id = user_id
        self.msg_count = 0
        self.ro_level = 0

    def __repr__(self):
        return "User ID: {0}\nMessage count: {1}\nRO level: {2}\n". \
            format(self.user_id, self.msg_count, self.ro_level)


engine = create_engine(url)
Base.metadata.create_all(bind=engine)
Session = sessionmaker(bind=engine)
