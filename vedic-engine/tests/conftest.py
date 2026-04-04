"""Shared test fixtures with mock chart data for known astrological scenarios."""

import os
import pytest

# Set required env vars before any app imports
os.environ.setdefault("API_KEY", "test-api-key")


@pytest.fixture
def settings_override():
    """Override settings for testing."""
    from app.config import Settings

    return Settings(
        API_KEY="test-api-key",
        REDIS_URL="redis://localhost:6379/1",
        DATABASE_URL="sqlite+aiosqlite:///test.db",
        EPHE_PATH="./ephe",
    )


@pytest.fixture
def aries_ascendant_chart():
    """Aries ascendant chart with Raj Yoga: Jupiter (lord of 9th) in 1st house."""
    return {
        "ascendant_sign": "Aries",
        "ascendant_sign_index": 1,
        "ascendant_degree": 15.0,
        "moon_sign": "Taurus",
        "sun_sign": "Leo",
        "birth_datetime": "1990-06-15T14:30:00",
        "planets": [
            {"planet": "Sun", "sign": "Leo", "sign_index": 5, "degree": 0.5, "absolute_degree": 120.5, "nakshatra": "Magha", "nakshatra_index": 9, "nakshatra_pada": 1, "house": 5, "is_retrograde": False},
            {"planet": "Moon", "sign": "Taurus", "sign_index": 2, "degree": 10.0, "absolute_degree": 40.0, "nakshatra": "Rohini", "nakshatra_index": 3, "nakshatra_pada": 3, "house": 2, "is_retrograde": False},
            {"planet": "Mars", "sign": "Capricorn", "sign_index": 10, "degree": 28.0, "absolute_degree": 298.0, "nakshatra": "Dhanishta", "nakshatra_index": 22, "nakshatra_pada": 3, "house": 10, "is_retrograde": False},
            {"planet": "Mercury", "sign": "Cancer", "sign_index": 4, "degree": 15.0, "absolute_degree": 105.0, "nakshatra": "Pushya", "nakshatra_index": 7, "nakshatra_pada": 3, "house": 4, "is_retrograde": False},
            {"planet": "Jupiter", "sign": "Aries", "sign_index": 1, "degree": 5.0, "absolute_degree": 5.0, "nakshatra": "Ashwini", "nakshatra_index": 0, "nakshatra_pada": 2, "house": 1, "is_retrograde": False},
            {"planet": "Venus", "sign": "Gemini", "sign_index": 3, "degree": 20.0, "absolute_degree": 80.0, "nakshatra": "Punarvasu", "nakshatra_index": 6, "nakshatra_pada": 3, "house": 3, "is_retrograde": False},
            {"planet": "Saturn", "sign": "Aquarius", "sign_index": 11, "degree": 5.0, "absolute_degree": 305.0, "nakshatra": "Dhanishta", "nakshatra_index": 22, "nakshatra_pada": 4, "house": 11, "is_retrograde": True},
            {"planet": "Rahu", "sign": "Sagittarius", "sign_index": 9, "degree": 15.0, "absolute_degree": 255.0, "nakshatra": "Purva Ashadha", "nakshatra_index": 19, "nakshatra_pada": 2, "house": 9, "is_retrograde": True},
            {"planet": "Ketu", "sign": "Gemini", "sign_index": 3, "degree": 15.0, "absolute_degree": 75.0, "nakshatra": "Ardra", "nakshatra_index": 5, "nakshatra_pada": 2, "house": 3, "is_retrograde": True},
        ],
        "source": "test",
    }


@pytest.fixture
def mangal_dosha_chart():
    """Chart with Mars in 7th house (Libra) from Aries ascendant — high severity Mangal Dosha."""
    return {
        "ascendant_sign": "Aries",
        "ascendant_sign_index": 1,
        "ascendant_degree": 10.0,
        "moon_sign": "Cancer",
        "sun_sign": "Libra",
        "birth_datetime": "1992-10-05T08:00:00",
        "planets": [
            {"planet": "Sun", "sign": "Libra", "sign_index": 7, "degree": 18.0, "absolute_degree": 198.0, "nakshatra": "Swati", "nakshatra_index": 14, "nakshatra_pada": 2, "house": 7, "is_retrograde": False},
            {"planet": "Moon", "sign": "Cancer", "sign_index": 4, "degree": 12.0, "absolute_degree": 102.0, "nakshatra": "Pushya", "nakshatra_index": 7, "nakshatra_pada": 3, "house": 4, "is_retrograde": False},
            {"planet": "Mars", "sign": "Libra", "sign_index": 7, "degree": 5.0, "absolute_degree": 185.0, "nakshatra": "Chitra", "nakshatra_index": 13, "nakshatra_pada": 3, "house": 7, "is_retrograde": False},
            {"planet": "Mercury", "sign": "Virgo", "sign_index": 6, "degree": 20.0, "absolute_degree": 170.0, "nakshatra": "Hasta", "nakshatra_index": 12, "nakshatra_pada": 4, "house": 6, "is_retrograde": False},
            {"planet": "Jupiter", "sign": "Virgo", "sign_index": 6, "degree": 10.0, "absolute_degree": 160.0, "nakshatra": "Hasta", "nakshatra_index": 12, "nakshatra_pada": 1, "house": 6, "is_retrograde": False},
            {"planet": "Venus", "sign": "Scorpio", "sign_index": 8, "degree": 15.0, "absolute_degree": 225.0, "nakshatra": "Anuradha", "nakshatra_index": 16, "nakshatra_pada": 2, "house": 8, "is_retrograde": False},
            {"planet": "Saturn", "sign": "Capricorn", "sign_index": 10, "degree": 20.0, "absolute_degree": 290.0, "nakshatra": "Shravana", "nakshatra_index": 21, "nakshatra_pada": 4, "house": 10, "is_retrograde": False},
            {"planet": "Rahu", "sign": "Sagittarius", "sign_index": 9, "degree": 25.0, "absolute_degree": 265.0, "nakshatra": "Purva Ashadha", "nakshatra_index": 19, "nakshatra_pada": 4, "house": 9, "is_retrograde": True},
            {"planet": "Ketu", "sign": "Gemini", "sign_index": 3, "degree": 25.0, "absolute_degree": 85.0, "nakshatra": "Punarvasu", "nakshatra_index": 6, "nakshatra_pada": 4, "house": 3, "is_retrograde": True},
        ],
        "source": "test",
    }


@pytest.fixture
def gaja_kesari_chart():
    """Chart with Gaja Kesari Yoga: Moon in Aries, Jupiter in Cancer (4th from Moon)."""
    return {
        "ascendant_sign": "Leo",
        "ascendant_sign_index": 5,
        "ascendant_degree": 20.0,
        "moon_sign": "Aries",
        "sun_sign": "Capricorn",
        "birth_datetime": "1988-01-20T06:30:00",
        "planets": [
            {"planet": "Sun", "sign": "Capricorn", "sign_index": 10, "degree": 5.0, "absolute_degree": 275.0, "nakshatra": "Uttara Ashadha", "nakshatra_index": 20, "nakshatra_pada": 3, "house": 6, "is_retrograde": False},
            {"planet": "Moon", "sign": "Aries", "sign_index": 1, "degree": 15.0, "absolute_degree": 15.0, "nakshatra": "Bharani", "nakshatra_index": 1, "nakshatra_pada": 2, "house": 9, "is_retrograde": False},
            {"planet": "Mars", "sign": "Scorpio", "sign_index": 8, "degree": 12.0, "absolute_degree": 222.0, "nakshatra": "Anuradha", "nakshatra_index": 16, "nakshatra_pada": 1, "house": 4, "is_retrograde": False},
            {"planet": "Mercury", "sign": "Sagittarius", "sign_index": 9, "degree": 25.0, "absolute_degree": 265.0, "nakshatra": "Purva Ashadha", "nakshatra_index": 19, "nakshatra_pada": 4, "house": 5, "is_retrograde": False},
            {"planet": "Jupiter", "sign": "Cancer", "sign_index": 4, "degree": 8.0, "absolute_degree": 98.0, "nakshatra": "Pushya", "nakshatra_index": 7, "nakshatra_pada": 2, "house": 12, "is_retrograde": False},
            {"planet": "Venus", "sign": "Aquarius", "sign_index": 11, "degree": 10.0, "absolute_degree": 310.0, "nakshatra": "Shatabhisha", "nakshatra_index": 23, "nakshatra_pada": 3, "house": 7, "is_retrograde": False},
            {"planet": "Saturn", "sign": "Sagittarius", "sign_index": 9, "degree": 2.0, "absolute_degree": 242.0, "nakshatra": "Mula", "nakshatra_index": 18, "nakshatra_pada": 1, "house": 5, "is_retrograde": True},
            {"planet": "Rahu", "sign": "Virgo", "sign_index": 6, "degree": 20.0, "absolute_degree": 170.0, "nakshatra": "Hasta", "nakshatra_index": 12, "nakshatra_pada": 4, "house": 2, "is_retrograde": True},
            {"planet": "Ketu", "sign": "Pisces", "sign_index": 12, "degree": 20.0, "absolute_degree": 350.0, "nakshatra": "Revati", "nakshatra_index": 26, "nakshatra_pada": 4, "house": 8, "is_retrograde": True},
        ],
        "source": "test",
    }


@pytest.fixture
def kemadruma_chart():
    """Chart with Kemadruma Yoga: Moon in Leo, no planets in Cancer (12th) or Virgo (2nd from Moon)."""
    return {
        "ascendant_sign": "Pisces",
        "ascendant_sign_index": 12,
        "ascendant_degree": 5.0,
        "moon_sign": "Leo",
        "sun_sign": "Aries",
        "birth_datetime": "1995-04-10T12:00:00",
        "planets": [
            {"planet": "Sun", "sign": "Aries", "sign_index": 1, "degree": 26.0, "absolute_degree": 26.0, "nakshatra": "Bharani", "nakshatra_index": 1, "nakshatra_pada": 4, "house": 2, "is_retrograde": False},
            {"planet": "Moon", "sign": "Leo", "sign_index": 5, "degree": 15.0, "absolute_degree": 135.0, "nakshatra": "Purva Phalguni", "nakshatra_index": 10, "nakshatra_pada": 2, "house": 6, "is_retrograde": False},
            {"planet": "Mars", "sign": "Scorpio", "sign_index": 8, "degree": 10.0, "absolute_degree": 220.0, "nakshatra": "Anuradha", "nakshatra_index": 16, "nakshatra_pada": 1, "house": 9, "is_retrograde": False},
            {"planet": "Mercury", "sign": "Pisces", "sign_index": 12, "degree": 5.0, "absolute_degree": 335.0, "nakshatra": "Uttara Bhadrapada", "nakshatra_index": 25, "nakshatra_pada": 4, "house": 1, "is_retrograde": False},
            {"planet": "Jupiter", "sign": "Sagittarius", "sign_index": 9, "degree": 15.0, "absolute_degree": 255.0, "nakshatra": "Purva Ashadha", "nakshatra_index": 19, "nakshatra_pada": 2, "house": 10, "is_retrograde": False},
            {"planet": "Venus", "sign": "Aquarius", "sign_index": 11, "degree": 20.0, "absolute_degree": 320.0, "nakshatra": "Purva Bhadrapada", "nakshatra_index": 24, "nakshatra_pada": 3, "house": 12, "is_retrograde": False},
            {"planet": "Saturn", "sign": "Aquarius", "sign_index": 11, "degree": 5.0, "absolute_degree": 305.0, "nakshatra": "Dhanishta", "nakshatra_index": 22, "nakshatra_pada": 4, "house": 12, "is_retrograde": True},
            {"planet": "Rahu", "sign": "Libra", "sign_index": 7, "degree": 10.0, "absolute_degree": 190.0, "nakshatra": "Swati", "nakshatra_index": 14, "nakshatra_pada": 1, "house": 8, "is_retrograde": True},
            {"planet": "Ketu", "sign": "Aries", "sign_index": 1, "degree": 10.0, "absolute_degree": 10.0, "nakshatra": "Ashwini", "nakshatra_index": 0, "nakshatra_pada": 3, "house": 2, "is_retrograde": True},
        ],
        "source": "test",
    }


@pytest.fixture
def kaal_sarpa_chart():
    """Chart where all 7 planets are between Rahu (Taurus 60°) and Ketu (Scorpio 240°)."""
    return {
        "ascendant_sign": "Aries",
        "ascendant_sign_index": 1,
        "ascendant_degree": 15.0,
        "moon_sign": "Gemini",
        "sun_sign": "Cancer",
        "birth_datetime": "1985-07-15T10:00:00",
        "planets": [
            {"planet": "Sun", "sign": "Cancer", "sign_index": 4, "degree": 28.0, "absolute_degree": 118.0, "nakshatra": "Ashlesha", "nakshatra_index": 8, "nakshatra_pada": 4, "house": 4, "is_retrograde": False},
            {"planet": "Moon", "sign": "Gemini", "sign_index": 3, "degree": 15.0, "absolute_degree": 75.0, "nakshatra": "Ardra", "nakshatra_index": 5, "nakshatra_pada": 2, "house": 3, "is_retrograde": False},
            {"planet": "Mars", "sign": "Gemini", "sign_index": 3, "degree": 5.0, "absolute_degree": 65.0, "nakshatra": "Mrigashira", "nakshatra_index": 4, "nakshatra_pada": 4, "house": 3, "is_retrograde": False},
            {"planet": "Mercury", "sign": "Cancer", "sign_index": 4, "degree": 10.0, "absolute_degree": 100.0, "nakshatra": "Pushya", "nakshatra_index": 7, "nakshatra_pada": 1, "house": 4, "is_retrograde": False},
            {"planet": "Jupiter", "sign": "Leo", "sign_index": 5, "degree": 20.0, "absolute_degree": 140.0, "nakshatra": "Purva Phalguni", "nakshatra_index": 10, "nakshatra_pada": 4, "house": 5, "is_retrograde": True},
            {"planet": "Venus", "sign": "Leo", "sign_index": 5, "degree": 10.0, "absolute_degree": 130.0, "nakshatra": "Magha", "nakshatra_index": 9, "nakshatra_pada": 4, "house": 5, "is_retrograde": False},
            {"planet": "Saturn", "sign": "Libra", "sign_index": 7, "degree": 5.0, "absolute_degree": 185.0, "nakshatra": "Chitra", "nakshatra_index": 13, "nakshatra_pada": 3, "house": 7, "is_retrograde": False},
            {"planet": "Rahu", "sign": "Taurus", "sign_index": 2, "degree": 0.0, "absolute_degree": 30.0, "nakshatra": "Krittika", "nakshatra_index": 2, "nakshatra_pada": 1, "house": 2, "is_retrograde": True},
            {"planet": "Ketu", "sign": "Scorpio", "sign_index": 8, "degree": 0.0, "absolute_degree": 210.0, "nakshatra": "Vishakha", "nakshatra_index": 15, "nakshatra_pada": 4, "house": 8, "is_retrograde": True},
        ],
        "source": "test",
    }


@pytest.fixture
def mangal_dosha_cancelled_chart():
    """Chart with Mars in Aries (own sign) in 1st house — Mangal Dosha cancelled."""
    return {
        "ascendant_sign": "Aries",
        "ascendant_sign_index": 1,
        "ascendant_degree": 10.0,
        "moon_sign": "Leo",
        "sun_sign": "Sagittarius",
        "birth_datetime": "1993-12-01T09:00:00",
        "planets": [
            {"planet": "Sun", "sign": "Sagittarius", "sign_index": 9, "degree": 15.0, "absolute_degree": 255.0, "nakshatra": "Purva Ashadha", "nakshatra_index": 19, "nakshatra_pada": 2, "house": 9, "is_retrograde": False},
            {"planet": "Moon", "sign": "Leo", "sign_index": 5, "degree": 20.0, "absolute_degree": 140.0, "nakshatra": "Purva Phalguni", "nakshatra_index": 10, "nakshatra_pada": 4, "house": 5, "is_retrograde": False},
            {"planet": "Mars", "sign": "Aries", "sign_index": 1, "degree": 15.0, "absolute_degree": 15.0, "nakshatra": "Bharani", "nakshatra_index": 1, "nakshatra_pada": 2, "house": 1, "is_retrograde": False},
            {"planet": "Mercury", "sign": "Scorpio", "sign_index": 8, "degree": 25.0, "absolute_degree": 235.0, "nakshatra": "Jyeshtha", "nakshatra_index": 17, "nakshatra_pada": 3, "house": 8, "is_retrograde": False},
            {"planet": "Jupiter", "sign": "Libra", "sign_index": 7, "degree": 10.0, "absolute_degree": 190.0, "nakshatra": "Swati", "nakshatra_index": 14, "nakshatra_pada": 1, "house": 7, "is_retrograde": False},
            {"planet": "Venus", "sign": "Capricorn", "sign_index": 10, "degree": 5.0, "absolute_degree": 275.0, "nakshatra": "Uttara Ashadha", "nakshatra_index": 20, "nakshatra_pada": 3, "house": 10, "is_retrograde": False},
            {"planet": "Saturn", "sign": "Aquarius", "sign_index": 11, "degree": 10.0, "absolute_degree": 310.0, "nakshatra": "Shatabhisha", "nakshatra_index": 23, "nakshatra_pada": 3, "house": 11, "is_retrograde": False},
            {"planet": "Rahu", "sign": "Scorpio", "sign_index": 8, "degree": 5.0, "absolute_degree": 215.0, "nakshatra": "Anuradha", "nakshatra_index": 16, "nakshatra_pada": 1, "house": 8, "is_retrograde": True},
            {"planet": "Ketu", "sign": "Taurus", "sign_index": 2, "degree": 5.0, "absolute_degree": 35.0, "nakshatra": "Krittika", "nakshatra_index": 2, "nakshatra_pada": 1, "house": 2, "is_retrograde": True},
        ],
        "source": "test",
    }
