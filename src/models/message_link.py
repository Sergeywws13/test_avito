from sqlalchemy import Column, Integer, String, ForeignKey, Index
from src.models.base import Base

class MessageLink(Base):
    __tablename__ = 'message_links'
    
    id = Column(Integer, primary_key=True)
    telegram_message_id = Column(Integer, nullable=False, unique=True)  # Оставляем unique
    avito_chat_id = Column(String(255), nullable=False)
    avito_user_id = Column(String(255), nullable=False)  # Исправлено на String
    user_id = Column(Integer, ForeignKey('users.id'))
    avito_message_id = Column(String(255))  # Все ID как строки
    
    __table_args__ = (
        Index('ix_telegram_message_id', 'telegram_message_id'),
        Index('ix_avito_chat_id', 'avito_chat_id')
    )
    