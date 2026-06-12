from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from ..config import settings

try:
    engine = create_async_engine(settings.DATABASE_URL, echo=False, future=True)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    _db_available = True
except Exception as e:
    print(f"Database not available (running without DB): {e}")
    engine = None
    async_session = None
    _db_available = False

async def get_db():
    if async_session is None:
        raise RuntimeError("Database not configured")
    async with async_session() as session:
        yield session

def is_db_available() -> bool:
    return _db_available
