"""Admin endpoints — LLM provider management."""

import os

from fastapi import APIRouter, Depends, HTTPException

from app.services.llm_router import router as llm_router
from app.utils.auth import verify_api_key

router = APIRouter(tags=["admin"])

VALID_PROVIDERS = ["gemini", "groq", "together", "openrouter", "anthropic", "openai"]


@router.post("/admin/llm/prefer/{provider}")
async def set_preferred_provider(
    provider: str,
    _token: str = Depends(verify_api_key),
):
    if provider not in VALID_PROVIDERS:
        raise HTTPException(400, f"Unknown provider. Valid: {VALID_PROVIDERS}")
    os.environ["LLM_PREFERRED_PROVIDER"] = provider
    llm_router.set_preferred(provider)
    return {"message": f"Preferred provider set to {provider}"}


@router.get("/admin/llm/status")
async def llm_status(_token: str = Depends(verify_api_key)):
    return {"providers": llm_router.get_status()}
