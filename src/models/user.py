from sqlalchemy import Column, Integer, String
from src.models.base import Base

class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, unique=True, nullable=False)
    client_id = Column(String, nullable=False)
    client_secret = Column(String, nullable=False)
    telegram_chat_id = Column(Integer, nullable=True)
    avito_user_id = Column(String, nullable=True)


    