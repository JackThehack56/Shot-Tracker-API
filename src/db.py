from collections.abc import AsyncGenerator
import uuid 
from dotenv import load_dotenv
import os
load_dotenv()
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
import datetime

DATABASE_URL = os.getenv("DATABASE_URL")

class Base(DeclarativeBase):
    pass

class RoundRow(Base):
    __tablename__ = "round"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    created_at = Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc))
    is_finished = Column(Boolean)
    data = Column(JSON, nullable=False)  

engine = create_async_engine(DATABASE_URL)
async_session_maker = async_sessionmaker(engine, expire_on_commit=False)

async def create_db_and_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_maker() as session:
        yield session 
# Is it yield so it can return the newest current session instead 
# of returning a session and then that session becoming out of date?