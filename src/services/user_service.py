from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from src.models.user import User

async def get_or_create_user(session: AsyncSession, telegram_id: int, client_id: str = None, client_secret: str = None) -> User:
    """
    Получает пользователя из базы данных или создает нового, если он не существует.
    """
    result = await session.execute(select(User).where(User.user_id == telegram_id))
    user = result.scalar_one_or_none()
    
    if not user:
        # Создаем нового пользователя с client_id и client_secret
        user = User(user_id=telegram_id, client_id=client_id, client_secret=client_secret)
        session.add(user)
        await session.commit()
    return user

