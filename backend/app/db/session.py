"""
CHC Pro AI — Database Session
SQLAlchemy async engine + session factory.
"""
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool
from config import get_settings

settings = get_settings()

# Convert postgresql:// -> postgresql+asyncpg:// if needed
_url = settings.DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)

# NullPool does not support pool_size or max_overflow
engine = create_async_engine(
    _url,
    echo=settings.APP_ENV == "development",
    pool_pre_ping=True,
    poolclass=NullPool,
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


async def get_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise