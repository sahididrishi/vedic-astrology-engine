"""Multi-LLM Router — tries free providers first, auto-fallback with circuit breaker."""

import os
import time
from typing import Optional

import httpx

from app.utils.logger import logger

MAX_TOKENS = 2000
TEMPERATURE = 0.4
CIRCUIT_BREAK_SECONDS = 300  # 5 min cooldown after 3 consecutive failures


class QuotaExceededError(Exception):
    pass


class AllProvidersFailedError(Exception):
    pass


class ProviderCircuitBreaker:
    def __init__(self):
        self.failures: dict[str, int] = {}
        self.disabled_until: dict[str, float] = {}

    def record_failure(self, name: str):
        self.failures[name] = self.failures.get(name, 0) + 1
        if self.failures[name] >= 3:
            self.disabled_until[name] = time.time() + CIRCUIT_BREAK_SECONDS
            logger.warning(f"Circuit breaker tripped for {name} — disabled for 5 min")

    def record_success(self, name: str):
        self.failures[name] = 0
        self.disabled_until.pop(name, None)

    def is_available(self, name: str) -> bool:
        until = self.disabled_until.get(name, 0)
        if time.time() < until:
            return False
        if time.time() >= until and name in self.disabled_until:
            # Recovery window — reset
            del self.disabled_until[name]
            self.failures[name] = 0
        return True


class LLMRouter:
    def __init__(self):
        self.breaker = ProviderCircuitBreaker()
        self.providers = self._build_provider_list()
        self.last_provider_used: str = ""

    def _build_provider_list(self) -> list[dict]:
        candidates = [
            {
                "name": "gemini",
                "key_env": "GEMINI_API_KEY",
                "model": "gemini-2.0-flash",
                "handler": self._call_gemini,
                "free": True,
            },
            {
                "name": "groq",
                "key_env": "GROQ_API_KEY",
                "model": "llama-3.3-70b-versatile",
                "handler": self._call_groq,
                "free": True,
            },
            {
                "name": "together",
                "key_env": "TOGETHER_API_KEY",
                "model": "meta-llama/Llama-3.3-70B-Instruct-Turbo",
                "handler": self._call_together,
                "free": True,
            },
            {
                "name": "openrouter",
                "key_env": "OPENROUTER_API_KEY",
                "model": "mistralai/mistral-7b-instruct",
                "handler": self._call_openrouter,
                "free": True,
            },
            {
                "name": "anthropic",
                "key_env": "ANTHROPIC_API_KEY",
                "model": "claude-haiku-4-5-20251001",
                "handler": self._call_anthropic,
                "free": False,
            },
            {
                "name": "openai",
                "key_env": "OPENAI_API_KEY",
                "model": "gpt-4o-mini",
                "handler": self._call_openai,
                "free": False,
            },
        ]

        preferred = os.getenv("LLM_PREFERRED_PROVIDER", "").strip().lower()
        active = [p for p in candidates if os.getenv(p["key_env"])]

        if not active:
            logger.warning(
                "No LLM API keys found. Add at least one of: "
                "GEMINI_API_KEY, GROQ_API_KEY, TOGETHER_API_KEY, OPENROUTER_API_KEY, "
                "ANTHROPIC_API_KEY, OPENAI_API_KEY"
            )
            return []

        if preferred:
            active.sort(key=lambda p: 0 if p["name"] == preferred else 1)

        logger.info(f"LLM provider order: {[p['name'] for p in active]}")
        return active

    async def complete(self, system_prompt: str, user_prompt: str) -> str:
        if not self.providers:
            raise AllProvidersFailedError("No LLM providers configured")

        last_error: Optional[Exception] = None
        for provider in list(self.providers):  # snapshot to avoid race with set_preferred
            name = provider["name"]
            if not self.breaker.is_available(name):
                logger.debug(f"Skipping {name} — circuit breaker active")
                continue
            try:
                logger.info(f"Trying LLM provider: {name} ({provider['model']})")
                result = await provider["handler"](
                    system_prompt=system_prompt,
                    user_prompt=user_prompt,
                    model=provider["model"],
                    api_key=os.getenv(provider["key_env"]),
                )
                self.breaker.record_success(name)
                self.last_provider_used = name
                logger.info(f"LLM response from {name}")
                return result
            except QuotaExceededError as e:
                logger.warning(f"{name} quota exceeded: {e}")
                self.breaker.record_failure(name)
                last_error = e
            except Exception as e:
                logger.warning(f"{name} failed: {e}")
                self.breaker.record_failure(name)
                last_error = e

        raise AllProvidersFailedError(f"All LLM providers failed. Last error: {last_error}")

    def set_preferred(self, provider_name: str):
        # Atomic replacement instead of in-place sort to avoid race conditions
        self.providers = sorted(
            self.providers, key=lambda p: 0 if p["name"] == provider_name else 1
        )
        logger.info(f"Preferred provider set to {provider_name}")

    def get_status(self) -> list[dict]:
        return [
            {
                "name": p["name"],
                "model": p["model"],
                "free": p["free"],
                "key_set": bool(os.getenv(p["key_env"])),
                "available": self.breaker.is_available(p["name"]),
                "failures": self.breaker.failures.get(p["name"], 0),
            }
            for p in self.providers
        ]

    # ── Provider Handlers ────────────────────────────────────────────────

    async def _call_gemini(self, system_prompt, user_prompt, model, api_key) -> str:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
        payload = {
            "system_instruction": {"parts": [{"text": system_prompt}]},
            "contents": [{"parts": [{"text": user_prompt}]}],
            "generationConfig": {"temperature": TEMPERATURE, "maxOutputTokens": MAX_TOKENS},
        }
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(url, json=payload, params={"key": api_key})
            _check_quota(resp, "gemini")
            resp.raise_for_status()
            data = resp.json()
            return data["candidates"][0]["content"]["parts"][0]["text"]

    async def _call_groq(self, system_prompt, user_prompt, model, api_key) -> str:
        return await self._call_openai_compat(
            "https://api.groq.com/openai/v1/chat/completions",
            system_prompt, user_prompt, model, api_key, "groq",
        )

    async def _call_together(self, system_prompt, user_prompt, model, api_key) -> str:
        return await self._call_openai_compat(
            "https://api.together.xyz/v1/chat/completions",
            system_prompt, user_prompt, model, api_key, "together",
        )

    async def _call_openrouter(self, system_prompt, user_prompt, model, api_key) -> str:
        url = "https://openrouter.ai/api/v1/chat/completions"
        payload = {
            "model": model,
            "temperature": TEMPERATURE,
            "max_tokens": MAX_TOKENS,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        }
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(url, json=payload, headers={
                "Authorization": f"Bearer {api_key}",
                "HTTP-Referer": "https://vedic-engine.app",
                "X-Title": "Vedic Astrology Engine",
            })
            _check_quota(resp, "openrouter")
            resp.raise_for_status()
            return resp.json()["choices"][0]["message"]["content"]

    async def _call_anthropic(self, system_prompt, user_prompt, model, api_key) -> str:
        url = "https://api.anthropic.com/v1/messages"
        payload = {
            "model": model,
            "max_tokens": MAX_TOKENS,
            "temperature": TEMPERATURE,
            "system": system_prompt,
            "messages": [{"role": "user", "content": user_prompt}],
        }
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(url, json=payload, headers={
                "x-api-key": api_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            })
            _check_quota(resp, "anthropic")
            resp.raise_for_status()
            return resp.json()["content"][0]["text"]

    async def _call_openai(self, system_prompt, user_prompt, model, api_key) -> str:
        return await self._call_openai_compat(
            "https://api.openai.com/v1/chat/completions",
            system_prompt, user_prompt, model, api_key, "openai",
        )

    async def _call_openai_compat(
        self, url, system_prompt, user_prompt, model, api_key, provider_name
    ) -> str:
        payload = {
            "model": model,
            "temperature": TEMPERATURE,
            "max_tokens": MAX_TOKENS,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        }
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                url, json=payload, headers={"Authorization": f"Bearer {api_key}"}
            )
            _check_quota(resp, provider_name)
            resp.raise_for_status()
            return resp.json()["choices"][0]["message"]["content"]


def _check_quota(resp: httpx.Response, provider: str):
    if resp.status_code == 429:
        raise QuotaExceededError(f"{provider} returned 429 — quota exceeded or rate limited")


# Module-level singleton
router = LLMRouter()
