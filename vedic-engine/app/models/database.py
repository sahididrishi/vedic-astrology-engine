import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import JSON, String, func
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from app.config import get_settings
from app.utils.logger import logger

settings = get_settings()

# Use JSONB for PostgreSQL, plain JSON for SQLite (testing)
_is_postgres = "postgresql" in settings.DATABASE_URL

_engine_kwargs = {"echo": False}
if _is_postgres:
    _engine_kwargs.update({
        "pool_size": 5,
        "max_overflow": 10,
        "pool_recycle": 3600,
        "pool_pre_ping": True,
    })

engine = create_async_engine(settings.DATABASE_URL, **_engine_kwargs)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

# Track whether DB is available
_db_available: bool = True


class Base(DeclarativeBase):
    pass


if _is_postgres:
    from sqlalchemy.dialects.postgresql import JSONB
    _json_type = JSONB
else:
    _json_type = JSON


class ReadingRecord(Base):
    __tablename__ = "readings"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    birth_input_json: Mapped[Optional[dict]] = mapped_column(_json_type, nullable=True)
    enriched_context_json: Mapped[Optional[dict]] = mapped_column(_json_type, nullable=True)
    reading_response_json: Mapped[Optional[dict]] = mapped_column(_json_type, nullable=True)
    llm_provider_used: Mapped[str] = mapped_column(String(50), default="unknown")
    processing_time_ms: Mapped[int] = mapped_column(default=0)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())


async def get_session():
    async with async_session() as session:
        yield session


async def store_reading(reading_id: str, birth_input: dict, response_json: dict,
                        provider: str = "unknown", processing_ms: int = 0) -> bool:
    """Store a reading in the database. Returns True on success, False on failure."""
    global _db_available
    try:
        async with async_session() as session:
            record = ReadingRecord(
                id=reading_id,
                birth_input_json=birth_input,
                reading_response_json=response_json,
                llm_provider_used=provider,
                processing_time_ms=processing_ms,
            )
            session.add(record)
            await session.commit()
            _db_available = True
            return True
    except Exception as e:
        _db_available = False
        logger.warning(f"Failed to store reading in DB: {e}")
        return False


async def fetch_reading(reading_id: str) -> Optional[dict]:
    """Fetch a reading from the database. Returns None if not found or DB unavailable."""
    try:
        async with async_session() as session:
            record = await session.get(ReadingRecord, reading_id)
            if record and record.reading_response_json:
                return record.reading_response_json
    except Exception as e:
        logger.warning(f"Failed to fetch reading from DB: {e}")
    return None
