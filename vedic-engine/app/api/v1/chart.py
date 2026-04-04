"""Chart endpoint — returns raw enriched chart data (no AI)."""

from fastapi import APIRouter, Depends, HTTPException, Request

from app.models.schemas import BirthInput
from app.services.orchestrator import DataOrchestrator
from app.utils.auth import verify_api_key
from app.utils.cache import Cache
from app.utils.logger import logger
from app.utils.rate_limiter import check_rate_limit

router = APIRouter(prefix="/api/v1", tags=["chart"])


@router.post("/chart")
async def create_chart(
    birth_input: BirthInput,
    request: Request,
    _token: str = Depends(verify_api_key),
):
    await check_rate_limit(request)

    redis = getattr(request.app.state, "redis", None)
    orchestrator = DataOrchestrator(cache=Cache(redis))

    birth_dict = birth_input.model_dump(mode="json")

    try:
        enriched = await orchestrator.process(birth_dict)
    except ValueError as e:
        raise HTTPException(status_code=422, detail={
            "error_code": "INVALID_BIRTH_DATA",
            "message": str(e),
            "suggestion": "Check input fields for invalid characters or values.",
        })
    except Exception as e:
        logger.error(f"Chart pipeline error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail={
            "error_code": "PIPELINE_ERROR",
            "message": "Failed to generate chart",
            "suggestion": "Please retry. If this persists, contact support.",
        })

    return {
        "chart": enriched.get("chart", {}),
        "planetary_strengths": enriched.get("planetary_strengths", {}),
        "yogas": enriched.get("yogas", []),
        "doshas": enriched.get("doshas", []),
        "dasha": enriched.get("dasha", {}),
        "area_analysis": enriched.get("area_analysis", {}),
    }
