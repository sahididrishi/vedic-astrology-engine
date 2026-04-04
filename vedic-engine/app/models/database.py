import uuid
from datetime import datetime

from sqlalchemy import func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from app.config import get_settings

settings = get_settings()

engine = create_async_engine(settings.DATABASE_URL, echo=False)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


class ReadingRecord(Base):
    __tablename__ = "readings"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    birth_input_json: Mapped[dict] = mapped_column(JSONB)
    enriched_context_json: Mapped[dict] = mapped_column(JSONB, nullable=True)
    reading_response_json: Mapped[dict] = mapped_column(JSONB)
    llm_provider_used: Mapped[str] = mapped_column(default="unknown")
    processing_time_ms: Mapped[int] = mapped_column(default=0)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())


async def get_session():
    async with async_session() as session:
        yield session
