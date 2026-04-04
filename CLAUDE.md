# Vedic Astrology Predictive Engine

## What This Is

A production-grade **Logic-Driven AI pipeline** (NOT a chatbot) that transforms birth data into consulting-quality Vedic astrological readings.

**Pipeline:** Birth data → Geocoding → Ephemeris/Astrology API → Vedic Rules Engine → Structured Brief → LLM → Validated JSON Reading → REST API

## Tech Stack

- **Language:** Python 3.11+
- **Framework:** FastAPI (async, Pydantic v2)
- **LLM:** Multi-provider router with free-tier priority (Gemini → Groq → Together → OpenRouter → Anthropic → OpenAI)
- **HTTP Client:** httpx (async)
- **Cache:** Redis
- **Database:** PostgreSQL + SQLAlchemy 2.0 (async) + Alembic
- **Ephemeris:** pyswisseph (Swiss Ephemeris) as offline fallback
- **Deployment:** Docker + Docker Compose
- **CI/CD:** GitHub Actions

## Project Structure

```
vedic-engine/
├── app/
│   ├── main.py                          # FastAPI app, CORS, exception handlers
│   ├── config.py                        # Pydantic Settings, .env loading
│   ├── models/
│   │   ├── schemas.py                   # Pydantic models (BirthInput, ReadingResponse, APIError)
│   │   └── database.py                  # SQLAlchemy models, async engine
│   ├── services/
│   │   ├── orchestrator.py              # DataOrchestrator — geocoding, chart API, enrichment
│   │   ├── logic_engine.py              # VedicLogicEngine — yogas, doshas, dasha, strength scoring
│   │   ├── prompt_architect.py          # PromptArchitect — builds structured AI prompts
│   │   ├── ai_client.py                 # AI call wrapper with JSON retry/fallback
│   │   ├── llm_router.py               # Multi-provider LLM router with circuit breaker
│   │   └── ephemeris_fallback.py        # Swiss Ephemeris wrapper (sidereal/Lahiri)
│   ├── api/v1/
│   │   ├── reading.py                   # POST /api/v1/reading, GET /api/v1/reading/{id}
│   │   ├── chart.py                     # POST /api/v1/chart (raw enriched data)
│   │   └── admin.py                     # Admin endpoints (LLM provider switching)
│   └── utils/
│       ├── cache.py                     # Redis caching
│       ├── auth.py                      # Bearer token auth (SHA-256 compare)
│       ├── rate_limiter.py              # Redis-backed rate limiting
│       └── logger.py                    # Structured JSON logging
├── tests/
├── alembic/
├── demo/index.html                      # Standalone demo UI
├── wordpress-plugin/vedic-engine-widget/ # WordPress shortcode plugin
├── ephe/                                # Swiss Ephemeris .se1 data files
├── docker-compose.yml
├── Dockerfile
├── .env.example
└── requirements.txt
```

## Key Architecture Decisions

- **Logic engine is pure Python** — no AI calls in the rules layer. Yogas, doshas, planetary strength, and dasha interpretation are all deterministic.
- **AI receives a structured brief**, not raw data. The PromptArchitect assembles an analytical brief from enriched context.
- **LLM Router tries free tiers first** (Gemini, Groq, Together, OpenRouter) before paid providers (Anthropic, OpenAI). Circuit breaker disables a provider after 3 consecutive failures for 5 minutes.
- **Swiss Ephemeris is the offline fallback** when the primary astrology API is down or quota-exceeded. Uses Lahiri ayanamsa (sidereal).
- **All AI output must be valid JSON** matching the ReadingResponse schema. Retry up to 3 times with escalating prompts; last-resort fallback parser extracts paragraphs.
- **Token budget:** Prompt must stay under 4000 tokens. `truncate_to_budget()` trims lower-priority sections.

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/v1/reading` | Full pipeline: birth data → AI reading (auth required) |
| GET | `/api/v1/reading/{id}` | Retrieve stored reading by UUID |
| POST | `/api/v1/chart` | Raw enriched chart data only (no AI) |
| GET | `/api/v1/health` | Service status, API connectivity, Redis status |
| POST | `/admin/llm/prefer/{provider}` | Switch preferred LLM provider at runtime |
| GET | `/admin/llm/status` | LLM provider status and circuit breaker state |

## Core Classes

- **`DataOrchestrator`** — Resolves location, fetches Vedic chart, triggers enrichment. Falls back to Swiss Ephemeris on API failure.
- **`VedicLogicEngine`** — Pure-Python rules engine: planetary strength scorer, yoga detector (Raj/Dhana/Viparita/Gaja Kesari/Kemadruma), dosha checker (Mangal/Shani/Kaal Sarpa), dasha interpreter, area-specific analyzer.
- **`PromptArchitect`** — Converts EnrichedContext into a structured analytical brief for the AI. Token-aware truncation.
- **`LLMRouter`** — Multi-provider client with priority ordering, circuit breaker, and automatic fallback.

## Rules Engine Modules

1. **Planetary Strength Scorer** — Dig Bala + simplified Shadbala (exalted/own/friendly/enemy/debilitated) + retrograde flag → 0-10 score per planet
2. **Yoga Detector** — Raj Yoga, Dhana Yoga, Viparita Raja Yoga, Gaja Kesari Yoga, Kemadruma Yoga → strength rating + life-area impact
3. **Dosha Checker** — Mangal Dosha, Shani Dosha (Sade Sati), Kaal Sarpa Dosha → severity + remediation category
4. **Dasha Interpreter** — Maps Vimshottari Dasha lord to natal position/strength, generates narrative, flags transitions within 12 months
5. **Area-Specific Analyzer** — Career (10th house), Relationships (7th house), Finance (2nd/11th), Health (1st/6th/8th)

## Security

- Bearer token auth with constant-time comparison
- Redis-backed rate limiting (10 req/min per key)
- Input sanitization: regex whitelist on text fields, date range validation
- Prompt injection guard: blocks known injection patterns before prompt assembly
- CORS restricted to configured origins
- Structured error responses with error codes (no stack traces to clients)

## Development Commands

```bash
# Local dev with Docker
docker compose up -d
# API docs
open http://localhost:8000/docs
# Run tests
pytest tests/ -v --cov=app
# Demo UI
cd demo && python -m http.server 3000
```

## Environment Variables

All config via `.env` — see `.env.example`. Key groups:
- **LLM keys:** GEMINI_API_KEY, GROQ_API_KEY, TOGETHER_API_KEY, OPENROUTER_API_KEY, ANTHROPIC_API_KEY, OPENAI_API_KEY (at least one required)
- **External APIs:** ASTROLOGY_API_KEY, GEOCODING_API_KEY
- **Infrastructure:** REDIS_URL, DATABASE_URL
- **App config:** API_KEY, ALLOWED_ORIGINS, EPHE_PATH, LLM_PREFERRED_PROVIDER, LLM_FALLBACK_MODE

## Conventions

- Async everywhere — all external calls use `httpx.AsyncClient`
- Pydantic v2 models for all request/response schemas
- Structured JSON logging only (no `print()`)
- Retry logic: 3 attempts with exponential backoff for all external API calls
- All astrology calculations use **sidereal zodiac (Lahiri ayanamsa)**
- AI temperature locked at 0.4 (analytical, not creative)
- Whole Sign house system
