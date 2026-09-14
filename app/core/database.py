# app/core/database.py
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy import create_engine
from app.core.config import settings

Base = declarative_base()

# Async engine — used by FastAPI routes
async_engine = create_async_engine(settings.DATABASE_URL, echo=False)
AsyncSessionLocal = async_sessionmaker(async_engine, expire_on_commit=False)

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session

# Sync engine — used by Celery tasks (Celery workers are sync by default)
sync_engine = create_engine(settings.SYNC_DATABASE_URL, echo=False)
SessionLocal = sessionmaker(bind=sync_engine)