from sqlalchemy import Column, ForeignKey, Integer, String
from src.models.base import Base
from sqlalchemy.orm import relationship
from src.models.message import Message


class Chat(Base):
    __tablename__ = 'chats'

    id = Column(Integer, primary_key=True, autoincrement=True)
    chat_id = Column(String, nullable=False)  # ID чата из API Avito
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)  # Связь с пользователем

    user = relationship("User", back_populates="chats")  # Используем строковую ссылку
    messages = relationship("Message", back_populates="chat")