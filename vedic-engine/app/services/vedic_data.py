"""Static Vedic astrology data tables — enums, lordships, dignities, nakshatras."""

from enum import IntEnum, Enum


class Sign(IntEnum):
    ARIES = 1
    TAURUS = 2
    GEMINI = 3
    CANCER = 4
    LEO = 5
    VIRGO = 6
    LIBRA = 7
    SCORPIO = 8
    SAGITTARIUS = 9
    CAPRICORN = 10
    AQUARIUS = 11
    PISCES = 12


SIGN_NAMES = {s: s.name.capitalize() for s in Sign}
SIGN_BY_NAME = {s.name.capitalize(): s for s in Sign}
SIGN_BY_NAME.update({s.name.title(): s for s in Sign})


class Planet(str, Enum):
    SUN = "Sun"
    MOON = "Moon"
    MARS = "Mars"
    MERCURY = "Mercury"
    JUPITER = "Jupiter"
    VENUS = "Venus"
    SATURN = "Saturn"
    RAHU = "Rahu"
    KETU = "Ketu"


class Relationship(str, Enum):
    FRIEND = "friend"
    NEUTRAL = "neutral"
    ENEMY = "enemy"


# ── Sign Lordship ──────────────────────────────────────────────────────────
SIGN_LORDS: dict[int, Planet] = {
    Sign.ARIES: Planet.MARS,
    Sign.TAURUS: Planet.VENUS,
    Sign.GEMINI: Planet.MERCURY,
    Sign.CANCER: Planet.MOON,
    Sign.LEO: Planet.SUN,
    Sign.VIRGO: Planet.MERCURY,
    Sign.LIBRA: Planet.VENUS,
    Sign.SCORPIO: Planet.MARS,
    Sign.SAGITTARIUS: Planet.JUPITER,
    Sign.CAPRICORN: Planet.SATURN,
    Sign.AQUARIUS: Planet.SATURN,
    Sign.PISCES: Planet.JUPITER,
}

# ── Own Signs ──────────────────────────────────────────────────────────────
OWN_SIGNS: dict[Planet, list[int]] = {
    Planet.SUN: [Sign.LEO],
    Planet.MOON: [Sign.CANCER],
    Planet.MARS: [Sign.ARIES, Sign.SCORPIO],
    Planet.MERCURY: [Sign.GEMINI, Sign.VIRGO],
    Planet.JUPITER: [Sign.SAGITTARIUS, Sign.PISCES],
    Planet.VENUS: [Sign.TAURUS, Sign.LIBRA],
    Planet.SATURN: [Sign.CAPRICORN, Sign.AQUARIUS],
    Planet.RAHU: [],
    Planet.KETU: [],
}

# ── Exaltation ─────────────────────────────────────────────────────────────
EXALTATION_SIGNS: dict[Planet, int] = {
    Planet.SUN: Sign.ARIES,
    Planet.MOON: Sign.TAURUS,
    Planet.MARS: Sign.CAPRICORN,
    Planet.MERCURY: Sign.VIRGO,
    Planet.JUPITER: Sign.CANCER,
    Planet.VENUS: Sign.PISCES,
    Planet.SATURN: Sign.LIBRA,
    Planet.RAHU: Sign.TAURUS,
    Planet.KETU: Sign.SCORPIO,
}

# ── Debilitation ───────────────────────────────────────────────────────────
DEBILITATION_SIGNS: dict[Planet, int] = {
    Planet.SUN: Sign.LIBRA,
    Planet.MOON: Sign.SCORPIO,
    Planet.MARS: Sign.CANCER,
    Planet.MERCURY: Sign.PISCES,
    Planet.JUPITER: Sign.CAPRICORN,
    Planet.VENUS: Sign.VIRGO,
    Planet.SATURN: Sign.ARIES,
    Planet.RAHU: Sign.SCORPIO,
    Planet.KETU: Sign.TAURUS,
}

# ── Moolatrikona Signs ─────────────────────────────────────────────────────
MOOLATRIKONA_SIGNS: dict[Planet, int] = {
    Planet.SUN: Sign.LEO,
    Planet.MOON: Sign.TAURUS,
    Planet.MARS: Sign.ARIES,
    Planet.MERCURY: Sign.VIRGO,
    Planet.JUPITER: Sign.SAGITTARIUS,
    Planet.VENUS: Sign.LIBRA,
    Planet.SATURN: Sign.AQUARIUS,
}

# ── Natural Friendships ────────────────────────────────────────────────────
_F = Relationship.FRIEND
_N = Relationship.NEUTRAL
_E = Relationship.ENEMY

NATURAL_FRIENDS: dict[Planet, dict[Planet, Relationship]] = {
    Planet.SUN: {
        Planet.MOON: _F, Planet.MARS: _F, Planet.JUPITER: _F,
        Planet.MERCURY: _N, Planet.VENUS: _E, Planet.SATURN: _E,
    },
    Planet.MOON: {
        Planet.SUN: _F, Planet.MERCURY: _F,
        Planet.MARS: _N, Planet.JUPITER: _N, Planet.VENUS: _N, Planet.SATURN: _N,
    },
    Planet.MARS: {
        Planet.SUN: _F, Planet.MOON: _F, Planet.JUPITER: _F,
        Planet.VENUS: _N, Planet.SATURN: _N, Planet.MERCURY: _E,
    },
    Planet.MERCURY: {
        Planet.SUN: _F, Planet.VENUS: _F,
        Planet.MARS: _N, Planet.JUPITER: _N, Planet.SATURN: _N,
        Planet.MOON: _E,
    },
    Planet.JUPITER: {
        Planet.SUN: _F, Planet.MOON: _F, Planet.MARS: _F,
        Planet.SATURN: _N, Planet.MERCURY: _E, Planet.VENUS: _E,
    },
    Planet.VENUS: {
        Planet.MERCURY: _F, Planet.SATURN: _F,
        Planet.MARS: _N, Planet.JUPITER: _N,
        Planet.SUN: _E, Planet.MOON: _E,
    },
    Planet.SATURN: {
        Planet.MERCURY: _F, Planet.VENUS: _F,
        Planet.JUPITER: _N,
        Planet.SUN: _E, Planet.MOON: _E, Planet.MARS: _E,
    },
}

# Rahu/Ketu friendship (simplified)
NATURAL_FRIENDS[Planet.RAHU] = {
    Planet.VENUS: _F, Planet.MERCURY: _F, Planet.SATURN: _F,
    Planet.JUPITER: _N,
    Planet.SUN: _E, Planet.MOON: _E, Planet.MARS: _E,
}
NATURAL_FRIENDS[Planet.KETU] = {
    Planet.MARS: _F, Planet.JUPITER: _F,
    Planet.SATURN: _N, Planet.MERCURY: _N,
    Planet.SUN: _E, Planet.MOON: _E, Planet.VENUS: _E,
}

# ── Dig Bala (Directional Strength) ───────────────────────────────────────
DIG_BALA: dict[Planet, int] = {
    Planet.SUN: 10,
    Planet.MARS: 10,
    Planet.JUPITER: 1,
    Planet.MERCURY: 1,
    Planet.MOON: 4,
    Planet.VENUS: 4,
    Planet.SATURN: 7,
    Planet.RAHU: 7,
    Planet.KETU: 1,
}

# ── House Categories ──────────────────────────────────────────────────────
KENDRA_HOUSES = {1, 4, 7, 10}
TRIKONA_HOUSES = {1, 5, 9}
UPACHAYA_HOUSES = {3, 6, 10, 11}
DUSTHANA_HOUSES = {6, 8, 12}
MARAKA_HOUSES = {2, 7}

# ── Benefic / Malefic ────────────────────────────────────────────────────
NATURAL_BENEFICS = {Planet.JUPITER, Planet.VENUS, Planet.MERCURY, Planet.MOON}
NATURAL_MALEFICS = {Planet.SATURN, Planet.MARS, Planet.SUN, Planet.RAHU, Planet.KETU}

# ── Vimshottari Dasha ────────────────────────────────────────────────────
VIMSHOTTARI_LORDS: list[tuple[Planet, int]] = [
    (Planet.KETU, 7),
    (Planet.VENUS, 20),
    (Planet.SUN, 6),
    (Planet.MOON, 10),
    (Planet.MARS, 7),
    (Planet.RAHU, 18),
    (Planet.JUPITER, 16),
    (Planet.SATURN, 19),
    (Planet.MERCURY, 17),
]
VIMSHOTTARI_TOTAL = 120  # years

NAKSHATRA_LORDS: list[Planet] = [lord for lord, _ in VIMSHOTTARI_LORDS] * 3
NAKSHATRA_SPAN = 360.0 / 27.0  # 13.3333...

NAKSHATRA_NAMES = [
    "Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashira", "Ardra",
    "Punarvasu", "Pushya", "Ashlesha", "Magha", "Purva Phalguni", "Uttara Phalguni",
    "Hasta", "Chitra", "Swati", "Vishakha", "Anuradha", "Jyeshtha",
    "Mula", "Purva Ashadha", "Uttara Ashadha", "Shravana", "Dhanishta",
    "Shatabhisha", "Purva Bhadrapada", "Uttara Bhadrapada", "Revati",
]

# ── House Domains ────────────────────────────────────────────────────────
HOUSE_DOMAINS: dict[int, list[str]] = {
    1: ["personality", "health", "appearance", "self"],
    2: ["wealth", "speech", "family", "food"],
    3: ["siblings", "courage", "communication", "short_travel"],
    4: ["mother", "home", "vehicles", "education", "comfort"],
    5: ["children", "intelligence", "creativity", "romance", "speculation"],
    6: ["enemies", "disease", "debt", "service", "competition"],
    7: ["marriage", "partnerships", "business", "spouse"],
    8: ["longevity", "transformation", "inheritance", "occult"],
    9: ["luck", "dharma", "father", "long_travel", "higher_education"],
    10: ["career", "reputation", "authority", "public_life"],
    11: ["gains", "income", "friends", "aspirations"],
    12: ["losses", "foreign_travel", "spirituality", "isolation", "expenses"],
}

DOMAIN_TO_HOUSES: dict[str, list[int]] = {
    "career": [10, 6, 2],
    "relationships": [7, 5, 1],
    "finance": [2, 11, 5],
    "health": [1, 6, 8],
    "general": [1, 5, 9, 10],
}
