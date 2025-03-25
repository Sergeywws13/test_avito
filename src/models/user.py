from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from src.models.base import Base
from src.models.chat import Chat

class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, unique=True, nullable=False)
    client_id = Column(String, nullable=False)
    client_secret = Column(String, nullable=False)
    telegram_chat_id = Column(Integer, nullable=True)

    chats = relationship("Chat", back_populates="user") 

    