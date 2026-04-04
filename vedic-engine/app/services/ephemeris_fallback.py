from datetime import datetime

import swisseph as swe

from app.config import get_settings
from app.utils.logger import logger

settings = get_settings()

swe.set_ephe_path(settings.EPHE_PATH)
swe.set_sid_mode(swe.SIDM_LAHIRI)

PLANET_IDS = {
    "Sun": swe.SUN,
    "Moon": swe.MOON,
    "Mercury": swe.MERCURY,
    "Venus": swe.VENUS,
    "Mars": swe.MARS,
    "Jupiter": swe.JUPITER,
    "Saturn": swe.SATURN,
    "Rahu": swe.MEAN_NODE,
    "Ketu": swe.MEAN_NODE,
}

VEDIC_SIGNS = [
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
]

NAKSHATRA_NAMES = [
    "Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashira", "Ardra",
    "Punarvasu", "Pushya", "Ashlesha", "Magha", "Purva Phalguni", "Uttara Phalguni",
    "Hasta", "Chitra", "Swati", "Vishakha", "Anuradha", "Jyeshtha",
    "Mula", "Purva Ashadha", "Uttara Ashadha", "Shravana", "Dhanishta",
    "Shatabhisha", "Purva Bhadrapada", "Uttara Bhadrapada", "Revati",
]

NAKSHATRA_SPAN = 360.0 / 27.0  # 13.3333... degrees


def get_julian_day(dt: datetime) -> float:
    hour_decimal = dt.hour + dt.minute / 60.0 + dt.second / 3600.0
    return swe.julday(dt.year, dt.month, dt.day, hour_decimal)


def _get_nakshatra(longitude: float) -> tuple[str, int, int]:
    """Returns (nakshatra_name, nakshatra_index, pada)."""
    nak_index = int(longitude / NAKSHATRA_SPAN)
    nak_index = min(nak_index, 26)
    degree_in_nak = longitude % NAKSHATRA_SPAN
    pada = int(degree_in_nak / (NAKSHATRA_SPAN / 4)) + 1
    pada = min(pada, 4)
    return NAKSHATRA_NAMES[nak_index], nak_index, pada


def calculate_planet_positions(utc_dt: datetime, lat: float, lng: float) -> dict:
    """Calculate all planet positions using Swiss Ephemeris (sidereal/Lahiri)."""
    jd = get_julian_day(utc_dt)
    results = {}

    for name, pid in PLANET_IDS.items():
        pos, ret_flag = swe.calc_ut(jd, pid, swe.FLG_SIDEREAL | swe.FLG_SPEED)
        longitude = pos[0]
        speed = pos[3]

        if name == "Ketu":
            longitude = (longitude + 180) % 360
            speed = -speed

        sign_index = int(longitude / 30)
        degree_in_sign = longitude % 30
        nak_name, nak_index, pada = _get_nakshatra(longitude)

        results[name] = {
            "planet": name,
            "longitude": round(longitude, 4),
            "sign": VEDIC_SIGNS[sign_index],
            "sign_index": sign_index + 1,  # 1-indexed
            "degree": round(degree_in_sign, 2),
            "absolute_degree": round(longitude, 4),
            "nakshatra": nak_name,
            "nakshatra_index": nak_index,
            "nakshatra_pada": pada,
            "is_retrograde": speed < 0,
            "source": "swiss_ephemeris",
        }

    # Ascendant and houses (Whole Sign)
    house_cusps, ascmc = swe.houses(jd, lat, lng, b"W")
    ayanamsa = swe.get_ayanamsa_ut(jd)
    asc_sidereal = (ascmc[0] - ayanamsa) % 360

    asc_sign_index = int(asc_sidereal / 30)
    asc_degree = asc_sidereal % 30

    # Assign houses to planets (Whole Sign: ascendant sign = house 1)
    for name, pdata in results.items():
        planet_sign_idx = pdata["sign_index"] - 1  # 0-indexed
        house = ((planet_sign_idx - asc_sign_index) % 12) + 1
        pdata["house"] = house

    results["_ascendant"] = {
        "sign": VEDIC_SIGNS[asc_sign_index],
        "sign_index": asc_sign_index + 1,
        "degree": round(asc_degree, 2),
        "longitude": round(asc_sidereal, 4),
        "source": "swiss_ephemeris",
    }

    return results


def get_current_saturn_sign() -> int:
    """Get Saturn's current sidereal sign index (1-12) for Sade Sati check."""
    jd = get_julian_day(datetime.utcnow())
    pos, _ = swe.calc_ut(jd, swe.SATURN, swe.FLG_SIDEREAL)
    return int(pos[0] / 30) + 1


def build_chart_data(utc_dt: datetime, lat: float, lng: float) -> dict:
    """Build a ChartData-compatible dict from Swiss Ephemeris calculations."""
    raw = calculate_planet_positions(utc_dt, lat, lng)
    asc = raw.pop("_ascendant")

    # Find Moon and Sun signs
    moon_sign = raw["Moon"]["sign"]
    sun_sign = raw["Sun"]["sign"]

    planets = list(raw.values())

    return {
        "ascendant_sign": asc["sign"],
        "ascendant_sign_index": asc["sign_index"],
        "ascendant_degree": asc["degree"],
        "moon_sign": moon_sign,
        "sun_sign": sun_sign,
        "planets": planets,
        "source": "swiss_ephemeris",
    }
