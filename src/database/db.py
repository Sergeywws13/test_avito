from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from src.models.base import Base


DATABASE_URL = "sqlite+aiosqlite:///./database.db"

# Создание движка для базы данных
engine = create_async_engine(DATABASE_URL, echo=True)
async_session = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


# Создание сессии
Session = sessionmaker(bind=engine)
session = Session()