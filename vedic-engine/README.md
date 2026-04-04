# Vedic Astrology Predictive Engine

A production-grade AI system that transforms birth data into human-quality Vedic astrological insights.

## What this is

NOT a chatbot. A Logic-Driven Predictive Pipeline:

birth data → geocode → ephemeris → rules engine → structured brief → AI → consulting-quality reading

## Architecture

```mermaid
graph LR
  A[Birth Input] --> B[Geocoding API]
  B --> C[Astrology API / Swiss Ephemeris fallback]
  C --> D[Vedic Logic Engine]
  D --> E[Prompt Architect]
  E --> F[LLM Router - Free tiers first]
  F --> G[Validated JSON Reading]
  G --> H[REST API Response]
```

## Tech stack

Python 3.11, FastAPI, Multi-LLM Router (Gemini/Groq/Together/OpenRouter/Claude/GPT), Redis, PostgreSQL, Docker, Swiss Ephemeris (pyswisseph), WordPress PHP plugin

## Key features

- DST-corrected birth charts via geocoding API — timezone accuracy
- Swiss Ephemeris offline fallback — zero downtime on API quota
- Custom rules engine: 5 yoga detectors, 3 dosha checkers, Dasha interpreter
- Multi-LLM router with free-tier priority and circuit breaker
- AI persona locked to experienced consultant (temperature 0.4)
- Structured JSON output — every reading machine-readable and renderable
- Production security: rate limiting, input sanitization, prompt injection guard
- WordPress shortcode plugin for zero-friction client site integration

## API usage

```bash
curl -X POST http://localhost:8000/api/v1/reading \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "full_name": "Arjun Sharma",
    "birth_date": "1990-06-15",
    "birth_time": "14:30",
    "birth_city": "Mumbai",
    "birth_country": "India",
    "reading_type": "career"
  }'
```

### Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/v1/reading` | Full AI reading pipeline |
| GET | `/api/v1/reading/{id}` | Retrieve stored reading |
| POST | `/api/v1/chart` | Raw enriched chart data (no AI) |
| GET | `/api/v1/health` | Service status |
| POST | `/admin/llm/prefer/{provider}` | Switch LLM provider |
| GET | `/admin/llm/status` | LLM provider status |

## Local setup

```bash
git clone <repo>
cd vedic-engine
cp .env.example .env   # fill in at least one LLM API key
docker compose up -d
open http://localhost:8000/docs
```

### Demo UI

```bash
cd demo
python -m http.server 3000
open http://localhost:3000
```

### Run tests

```bash
pip install -r requirements.txt
pytest tests/ -v --cov=app
```

## LLM Provider Priority

| Priority | Provider | Free tier | Model |
|----------|----------|-----------|-------|
| 1 | Google Gemini | Yes — 1500 req/day | gemini-2.0-flash |
| 2 | Groq | Yes — 14,400 req/day | llama-3.3-70b-versatile |
| 3 | Together AI | Yes — $1 free credit | Llama-3.3-70B-Turbo |
| 4 | OpenRouter | Yes — $1 free credit | mistral-7b-instruct |
| 5 | Anthropic | Paid | claude-haiku-4-5 |
| 6 | OpenAI | Paid | gpt-4o-mini |

The router tries free tiers first. If a provider fails 3 times, it's disabled for 5 minutes (circuit breaker).

## WordPress integration

1. Upload `wordpress-plugin/vedic-engine-widget/` to `/wp-content/plugins/`
2. Activate in WordPress admin
3. Set API URL + key in Settings → Vedic Engine
4. Add `[vedic_reading]` shortcode to any page
