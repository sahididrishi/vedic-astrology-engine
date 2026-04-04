"""Reading endpoints — full AI pipeline and retrieval."""

import time
import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Request

from app.models.schemas import BirthInput, ReadingResponse
from app.services.ai_client import generate_reading
from app.services.orchestrator import DataOrchestrator
from app.utils.auth import verify_api_key
from app.utils.cache import Cache
from app.utils.logger import logger
from app.utils.rate_limiter import check_rate_limit

router = APIRouter(prefix="/api/v1", tags=["reading"])

# In-memory store for readings (replace with DB in production)
_readings_store: dict[str, dict] = {}


def _get_orchestrator(request: Request) -> DataOrchestrator:
    redis = getattr(request.app.state, "redis", None)
    return DataOrchestrator(cache=Cache(redis))


@router.post("/reading", response_model=ReadingResponse)
async def create_reading(
    birth_input: BirthInput,
    request: Request,
    _token: str = Depends(verify_api_key),
):
    await check_rate_limit(request)
    start_time = time.time()

    try:
        orchestrator = _get_orchestrator(request)

        # Run enrichment pipeline
        birth_dict = birth_input.model_dump(mode="json")
        enriched = await orchestrator.process(birth_dict)

        # Generate AI reading
        ai_result = await generate_reading(enriched, birth_input.reading_type)

        processing_ms = int((time.time() - start_time) * 1000)
        reading_id = uuid.uuid4()

        response = ReadingResponse(
            reading_id=reading_id,
            created_at=datetime.utcnow(),
            subject_name=birth_input.full_name,
            reading_type=birth_input.reading_type,
            overview=ai_result.get("overview", ""),
            sections=[
                {"title": s.get("title", ""), "insight": s.get("insight", ""), "actions": s.get("actions", [])}
                for s in ai_result.get("sections", [])
            ],
            key_periods=[
                {"period": kp.get("period", ""), "theme": kp.get("theme", ""), "guidance": kp.get("guidance", "")}
                for kp in ai_result.get("key_periods", [])
            ],
            closing=ai_result.get("closing", ""),
            chart_summary={
                "ascendant": enriched.get("chart", {}).get("ascendant_sign", ""),
                "moon_sign": enriched.get("chart", {}).get("moon_sign", ""),
                "sun_sign": enriched.get("chart", {}).get("sun_sign", ""),
                "yoga_count": len(enriched.get("yogas", [])),
                "dosha_count": len(enriched.get("doshas", [])),
            },
            processing_time_ms=processing_ms,
        )

        # Store reading
        _readings_store[str(reading_id)] = response.model_dump(mode="json")

        return response

    except ValueError as e:
        raise HTTPException(status_code=422, detail={
            "error_code": "INVALID_BIRTH_DATA",
            "message": str(e),
            "suggestion": "Check input fields for invalid characters or values.",
        })
    except Exception as e:
        logger.error(f"Reading pipeline error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail={
            "error_code": "PIPELINE_ERROR",
            "message": "Failed to generate reading",
            "suggestion": "Please retry. If this persists, contact support.",
        })


@router.get("/reading/{reading_id}")
async def get_reading(reading_id: str):
    reading = _readings_store.get(reading_id)
    if not reading:
        raise HTTPException(status_code=404, detail={
            "error_code": "NOT_FOUND",
            "message": "Reading not found",
            "suggestion": "Check the reading ID and try again.",
        })
    return reading
