from sqlalchemy import Column, ForeignKey, Integer, String
from src.models.base import Base
from sqlalchemy.orm import relationship
from datetime import datetime


class Message(Base):
    __tablename__ = 'messages'

    id = Column(Integer, primary_key=True, autoincrement=True)
    chat_id = Column(Integer, ForeignKey('chats.id'), nullable=False)  # Связь с чатом
    sender_name = Column(String, nullable=False)  # Имя отправителя
    text = Column(String, nullable=False)  # Текст сообщения
    timestamp = Column(String, default=datetime.now)  # Время отправки сообщения

    # Связь с чатом
    chat = relationship("Chat", back_populates="messages")
    