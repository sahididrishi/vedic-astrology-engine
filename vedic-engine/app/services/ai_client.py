"""AI Client — LLM call wrapper with JSON retry, escalation, and fallback parser."""

import asyncio
import json
import re

from app.services.llm_router import router as llm_router
from app.services.prompt_architect import PromptArchitect
from app.utils.logger import logger

MAX_RETRIES = 3
RETRY_DELAYS = [1, 3, 7]

prompt_architect = PromptArchitect()


async def generate_reading(enriched: dict, reading_type: str) -> dict:
    """Generate an AI reading from enriched astrological context."""
    system_prompt = prompt_architect.build_system_prompt(reading_type)
    user_prompt = prompt_architect.build_user_prompt(enriched, reading_type)

    return await call_with_retry(system_prompt, user_prompt)


async def call_with_retry(
    system_prompt: str,
    user_prompt: str,
    attempt: int = 0,
) -> dict:
    """Call LLM with retry and escalating correction on JSON failures."""
    raw: str = ""  # guard: ensures 'raw' is always bound
    try:
        raw = await llm_router.complete(system_prompt, user_prompt)
        return parse_ai_response(raw)

    except json.JSONDecodeError as e:
        logger.warning(f"JSON parse failed on attempt {attempt + 1}: {e}")
        if attempt < MAX_RETRIES - 1:
            delay = RETRY_DELAYS[min(attempt, len(RETRY_DELAYS) - 1)]
            await asyncio.sleep(delay)
            corrected_prompt = (
                user_prompt
                + "\n\nCRITICAL: Your previous response was not valid JSON. "
                "Return ONLY a valid JSON object. No prose, no markdown fences, "
                "no explanation before or after the JSON."
            )
            return await call_with_retry(system_prompt, corrected_prompt, attempt + 1)
        else:
            logger.error("All JSON retry attempts exhausted, using fallback parser")
            return fallback_extract(raw)

    except Exception as e:
        logger.error(f"LLM API error on attempt {attempt + 1}: {e}")
        if attempt < MAX_RETRIES - 1:
            delay = RETRY_DELAYS[min(attempt, len(RETRY_DELAYS) - 1)]
            await asyncio.sleep(delay)
            return await call_with_retry(system_prompt, user_prompt, attempt + 1)
        raise


def parse_ai_response(raw: str) -> dict:
    """Parse and validate AI response as JSON."""
    raw = raw.strip()
    # Strip markdown code fences
    raw = re.sub(r"^```json\s*", "", raw)
    raw = re.sub(r"^```\s*", "", raw)
    raw = re.sub(r"\s*```$", "", raw)
    raw = raw.strip()

    # Extract JSON object
    start = raw.find("{")
    end = raw.rfind("}")
    if start != -1 and end != -1:
        raw = raw[start : end + 1]

    parsed = json.loads(raw)
    validate_reading_structure(parsed)
    return parsed


def validate_reading_structure(data: dict):
    """Validate that the AI response has the required structure."""
    required = ["overview", "sections", "key_periods", "closing"]
    missing = [k for k in required if k not in data]
    if missing:
        raise json.JSONDecodeError(f"Missing required keys: {missing}", "", 0)
    if not isinstance(data["sections"], list) or len(data["sections"]) == 0:
        raise json.JSONDecodeError("sections must be a non-empty list", "", 0)


def fallback_extract(raw: str) -> dict:
    """Last-resort: extract readable content from malformed AI response."""
    logger.warning("Using fallback extraction from raw AI text")
    paragraphs = [p.strip() for p in raw.split("\n\n") if len(p.strip()) > 50]

    return {
        "overview": paragraphs[0] if paragraphs else "Reading generated with partial data.",
        "sections": [
            {"title": f"Insight {i + 1}", "insight": p, "actions": []}
            for i, p in enumerate(paragraphs[1:4])
        ]
        or [{"title": "Reading", "insight": raw[:500], "actions": []}],
        "key_periods": [],
        "closing": paragraphs[-1] if len(paragraphs) > 1 else "",
        "_fallback": True,
    }
