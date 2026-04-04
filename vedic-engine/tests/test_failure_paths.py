"""Failure-path tests — Redis down, LLM errors, geocoding failures, rate limits."""

import os
import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import date, time

os.environ.setdefault("API_KEY", "test-api-key")

from app.services.ai_client import call_with_retry, fallback_extract, parse_ai_response
from app.services.llm_router import ProviderCircuitBreaker, AllProvidersFailedError
from app.services.orchestrator import DataOrchestrator
from app.utils.cache import Cache


# ── LLM Retry / Fallback Tests ──────────────────────────────────────────

class TestLLMRetry:
    @pytest.mark.asyncio
    async def test_retry_succeeds_on_second_attempt(self):
        """LLM returns bad JSON first, valid JSON second."""
        valid_json = json.dumps({
            "overview": "Test", "sections": [{"title": "T", "insight": "I"}],
            "key_periods": [], "closing": "Done",
        })
        mock_complete = AsyncMock(side_effect=["not valid json {{{", valid_json])

        with patch("app.services.ai_client.llm_router") as mock_router:
            mock_router.complete = mock_complete
            # Use delay=0 for fast tests
            with patch("app.services.ai_client.RETRY_DELAYS", [0, 0, 0]):
                result = await call_with_retry("system", "user")

        assert result["overview"] == "Test"
        assert mock_complete.call_count == 2

    @pytest.mark.asyncio
    async def test_retry_exhausted_uses_fallback(self):
        """After MAX_RETRIES of bad JSON, fallback_extract is used."""
        bad_response = "This is not JSON at all, just a long paragraph of text that exceeds the minimum threshold for the fallback parser extraction logic."
        mock_complete = AsyncMock(return_value=bad_response)

        with patch("app.services.ai_client.llm_router") as mock_router:
            mock_router.complete = mock_complete
            with patch("app.services.ai_client.RETRY_DELAYS", [0, 0, 0]):
                result = await call_with_retry("system", "user")

        assert result.get("_fallback") is True
        assert "overview" in result

    @pytest.mark.asyncio
    async def test_llm_error_raises_after_max_retries(self):
        """Generic LLM errors propagate after exhausting retries."""
        mock_complete = AsyncMock(side_effect=RuntimeError("connection failed"))

        with patch("app.services.ai_client.llm_router") as mock_router:
            mock_router.complete = mock_complete
            with patch("app.services.ai_client.RETRY_DELAYS", [0, 0, 0]):
                with pytest.raises(RuntimeError, match="connection failed"):
                    await call_with_retry("system", "user")

        assert mock_complete.call_count == 3


# ── Circuit Breaker Tests ────────────────────────────────────────────────

class TestCircuitBreaker:
    def test_trips_after_3_failures(self):
        cb = ProviderCircuitBreaker()
        for _ in range(3):
            cb.record_failure("test")
        assert cb.is_available("test") is False

    def test_failure_count_capped_at_3(self):
        """Failures should not pile up past 3 during cooldown."""
        cb = ProviderCircuitBreaker()
        for _ in range(10):
            cb.record_failure("test")
        assert cb.failures["test"] == 3  # capped, not 10

    def test_resets_on_success(self):
        cb = ProviderCircuitBreaker()
        cb.record_failure("test")
        cb.record_failure("test")
        cb.record_success("test")
        assert cb.failures["test"] == 0
        assert cb.is_available("test") is True

    def test_recovers_after_cooldown(self):
        """Provider becomes available after cooldown period."""
        import time as _time
        cb = ProviderCircuitBreaker()
        for _ in range(3):
            cb.record_failure("test")
        # Simulate cooldown expiry
        cb.disabled_until["test"] = _time.time() - 1
        assert cb.is_available("test") is True


# ── Cache Failure Tests ──────────────────────────────────────────────────

class TestCacheFailure:
    @pytest.mark.asyncio
    async def test_cache_get_returns_none_on_error(self):
        """Cache.get_cached returns None when Redis raises."""
        mock_redis = AsyncMock()
        mock_redis.get = AsyncMock(side_effect=ConnectionError("Redis down"))
        cache = Cache(mock_redis)
        result = await cache.get_cached("some-key")
        assert result is None

    @pytest.mark.asyncio
    async def test_cache_set_swallows_error(self):
        """Cache.set_cached does not raise when Redis fails."""
        mock_redis = AsyncMock()
        mock_redis.set = AsyncMock(side_effect=ConnectionError("Redis down"))
        cache = Cache(mock_redis)
        # Should not raise
        await cache.set_cached("some-key", {"data": "test"}, ttl=60)

    @pytest.mark.asyncio
    async def test_cache_works_without_redis(self):
        """Cache with None redis client returns None / does nothing."""
        cache = Cache(None)
        result = await cache.get_cached("key")
        assert result is None
        await cache.set_cached("key", {"data": 1})  # should not raise


# ── Orchestrator Fallback Tests ──────────────────────────────────────────

class TestOrchestratorFallback:
    def test_fallback_location_known_city(self):
        orch = DataOrchestrator(cache=Cache(None))
        loc = orch._fallback_location("Mumbai", "India")
        assert loc["latitude"] == pytest.approx(19.076, abs=0.01)
        assert loc["timezone_id"] == "Asia/Kolkata"

    def test_fallback_location_unknown_city_returns_default(self):
        orch = DataOrchestrator(cache=Cache(None))
        loc = orch._fallback_location("Atlantis", "Unknown")
        assert loc["latitude"] == pytest.approx(28.6139, abs=0.01)  # Default (Delhi)
        assert loc["timezone_id"] == "Asia/Kolkata"

    def test_utc_conversion_with_zoneinfo(self):
        """_to_utc correctly converts using IANA timezone."""
        orch = DataOrchestrator(cache=Cache(None))
        birth_input = {
            "birth_date": date(1990, 6, 15),
            "birth_time": time(14, 30),
        }
        location = {"timezone_id": "Asia/Kolkata", "utc_offset": 5.5}
        utc_dt = orch._to_utc(birth_input, location)
        # 14:30 IST = 09:00 UTC
        assert utc_dt.hour == 9
        assert utc_dt.minute == 0

    def test_utc_conversion_handles_dst(self):
        """_to_utc correctly handles DST for New York summer."""
        orch = DataOrchestrator(cache=Cache(None))
        birth_input = {
            "birth_date": date(1990, 7, 4),  # July = EDT (UTC-4)
            "birth_time": time(14, 0),
        }
        location = {"timezone_id": "America/New_York", "utc_offset": -5.0}
        utc_dt = orch._to_utc(birth_input, location)
        # 14:00 EDT = 18:00 UTC (NOT 19:00 as static -5 would give)
        assert utc_dt.hour == 18
        assert utc_dt.minute == 0


# ── Vedic Data Integrity Tests ───────────────────────────────────────────

class TestVedicDataIntegrity:
    def test_sign_lords_complete(self):
        from app.services.vedic_data import SIGN_LORDS
        assert len(SIGN_LORDS) == 12

    def test_exaltation_debilitation_opposite(self):
        from app.services.vedic_data import EXALTATION_SIGNS, DEBILITATION_SIGNS, Planet
        for p in [Planet.SUN, Planet.MOON, Planet.MARS, Planet.MERCURY,
                  Planet.JUPITER, Planet.VENUS, Planet.SATURN]:
            diff = abs(EXALTATION_SIGNS[p] - DEBILITATION_SIGNS[p])
            assert diff == 6, f"{p.value}: exalt={EXALTATION_SIGNS[p]} debil={DEBILITATION_SIGNS[p]}"

    def test_vimshottari_total_120(self):
        from app.services.vedic_data import VIMSHOTTARI_LORDS
        assert sum(y for _, y in VIMSHOTTARI_LORDS) == 120

    def test_27_nakshatras(self):
        from app.services.vedic_data import NAKSHATRA_LORDS, NAKSHATRA_NAMES
        assert len(NAKSHATRA_LORDS) == 27
        assert len(NAKSHATRA_NAMES) == 27

    def test_all_planets_have_friendships(self):
        from app.services.vedic_data import NATURAL_FRIENDS, Planet
        for p in Planet:
            assert p in NATURAL_FRIENDS, f"{p.value} missing from NATURAL_FRIENDS"

    def test_all_domains_mapped(self):
        from app.services.vedic_data import DOMAIN_TO_HOUSES
        for domain in ["career", "relationships", "finance", "health", "general"]:
            assert domain in DOMAIN_TO_HOUSES


# ── Schema Validation Edge Cases ─────────────────────────────────────────

class TestSchemaEdgeCases:
    def test_birth_date_today_is_valid(self):
        from app.models.schemas import BirthInput
        from datetime import date, time
        bi = BirthInput(
            full_name="Test User",
            birth_date=date.today(),
            birth_time=time(12, 0),
            birth_city="Mumbai",
            birth_country="India",
        )
        assert bi.birth_date == date.today()

    def test_birth_date_1900_is_valid(self):
        from app.models.schemas import BirthInput
        from datetime import date, time
        bi = BirthInput(
            full_name="Test User",
            birth_date=date(1900, 1, 1),
            birth_time=time(12, 0),
            birth_city="Mumbai",
            birth_country="India",
        )
        assert bi.birth_date.year == 1900

    def test_name_with_spaces_stripped(self):
        from app.models.schemas import BirthInput
        from datetime import date, time
        bi = BirthInput(
            full_name="  Arjun Sharma  ",
            birth_date=date(1990, 1, 1),
            birth_time=time(12, 0),
            birth_city="  Mumbai  ",
            birth_country="India",
        )
        assert bi.full_name == "Arjun Sharma"
        assert bi.birth_city == "Mumbai"

    def test_invalid_reading_type_rejected(self):
        from app.models.schemas import BirthInput
        from datetime import date, time
        with pytest.raises(Exception):
            BirthInput(
                full_name="Test User",
                birth_date=date(1990, 1, 1),
                birth_time=time(12, 0),
                birth_city="Mumbai",
                birth_country="India",
                reading_type="invalid_type",
            )
