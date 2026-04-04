"""Vedic Logic Engine — pure Python rules engine. No AI calls. Deterministic."""

from datetime import datetime, timedelta
from typing import Optional


def _ordinal(n: int) -> str:
    """Return ordinal string for a number (1st, 2nd, 3rd, 4th, etc.)."""
    if 11 <= (n % 100) <= 13:
        return f"{n}th"
    return f"{n}{['th','st','nd','rd','th','th','th','th','th','th'][n % 10]}"

from app.services.vedic_data import (
    DIG_BALA,
    DEBILITATION_SIGNS,
    DOMAIN_TO_HOUSES,
    DUSTHANA_HOUSES,
    EXALTATION_SIGNS,
    HOUSE_DOMAINS,
    KENDRA_HOUSES,
    MOOLATRIKONA_SIGNS,
    NAKSHATRA_LORDS,
    NAKSHATRA_SPAN,
    NATURAL_BENEFICS,
    NATURAL_FRIENDS,
    OWN_SIGNS,
    Planet,
    Relationship,
    SIGN_LORDS,
    SIGN_NAMES,
    Sign,
    TRIKONA_HOUSES,
    VIMSHOTTARI_LORDS,
    VIMSHOTTARI_TOTAL,
)


class VedicLogicEngine:
    """Pure-Python Vedic astrology rules engine."""

    # ── Public entry point ────────────────────────────────────────────────

    def enrich(
        self,
        chart_data: dict,
        current_saturn_sign: Optional[int] = None,
        reference_dt: Optional[datetime] = None,
    ) -> dict:
        """Main entry point. Takes raw chart dict, returns enriched context dict."""
        ref_dt = reference_dt or datetime.utcnow()
        planets = chart_data["planets"]
        asc_index = chart_data["ascendant_sign_index"]

        strengths = self.score_all_planets(planets, asc_index)
        yogas = self.detect_all_yogas(planets, asc_index)
        doshas = self.check_all_doshas(planets, asc_index, current_saturn_sign)
        dasha = self.calculate_dasha(planets, chart_data, ref_dt)
        areas = {
            domain: self.analyze_area(domain, planets, asc_index, strengths)
            for domain in DOMAIN_TO_HOUSES
        }

        return {
            "planetary_strengths": strengths,
            "yogas": yogas,
            "doshas": doshas,
            "dasha": dasha,
            "area_analysis": areas,
        }

    # ── Helpers ───────────────────────────────────────────────────────────

    def _get_house_lord(self, house: int, asc_sign: int) -> Planet:
        """Given house (1-12) and ascendant sign index (1-12), return ruling planet."""
        sign_of_house = ((asc_sign - 1 + house - 1) % 12) + 1
        return SIGN_LORDS[sign_of_house]

    def _get_planet_house(self, planet_sign_index: int, asc_sign: int) -> int:
        """Given planet's sign index (1-12) and ascendant, return house (1-12)."""
        return ((planet_sign_index - asc_sign) % 12) + 1

    def _find_planet(self, name: str, planets: list[dict]) -> Optional[dict]:
        """Find a planet by name in the planets list."""
        for p in planets:
            if p["planet"] == name:
                return p
        return None

    def _planet_enum(self, name: str) -> Optional[Planet]:
        """Convert planet name string to Planet enum."""
        try:
            return Planet(name)
        except ValueError:
            return None

    def _planets_in_house(self, house: int, planets: list[dict], asc_sign: int) -> list[dict]:
        """Return all planets occupying a given house."""
        return [
            p for p in planets
            if self._get_planet_house(p["sign_index"], asc_sign) == house
        ]

    def _houses_ruled_by(self, planet: Planet, asc_sign: int) -> list[int]:
        """Return list of houses (1-12) ruled by a planet given the ascendant."""
        houses = []
        for h in range(1, 13):
            if self._get_house_lord(h, asc_sign) == planet:
                houses.append(h)
        return houses

    # ── Module 1: Planetary Strength Scorer ───────────────────────────────

    def _get_dignity(self, planet: Planet, sign_index: int) -> str:
        """Determine the dignity of a planet in a given sign."""
        if EXALTATION_SIGNS.get(planet) == sign_index:
            return "exalted"
        if DEBILITATION_SIGNS.get(planet) == sign_index:
            return "debilitated"
        if MOOLATRIKONA_SIGNS.get(planet) == sign_index:
            return "moolatrikona"
        if sign_index in OWN_SIGNS.get(planet, []):
            return "own_sign"

        sign_lord = SIGN_LORDS.get(sign_index)
        if sign_lord and sign_lord != planet:
            friendships = NATURAL_FRIENDS.get(planet, {})
            rel = friendships.get(sign_lord, Relationship.NEUTRAL)
            if rel == Relationship.FRIEND:
                return "friendly"
            elif rel == Relationship.ENEMY:
                return "enemy"
        return "neutral"

    def score_planet(self, planet_data: dict, asc_sign: int) -> dict:
        """Score a single planet. Returns {score, dignity, dig_bala, notes}."""
        name = planet_data["planet"]
        planet_enum = self._planet_enum(name)
        if not planet_enum:
            return {"score": 5.0, "dignity": "unknown", "dig_bala": False, "notes": []}

        sign_index = planet_data["sign_index"]
        house = self._get_planet_house(sign_index, asc_sign)
        is_retro = planet_data.get("is_retrograde", False)

        # Base score
        score = 5.0

        # Dignity modifier
        dignity = self._get_dignity(planet_enum, sign_index)
        dignity_mods = {
            "exalted": 4.0,
            "moolatrikona": 3.0,
            "own_sign": 2.0,
            "friendly": 1.0,
            "neutral": 0.0,
            "enemy": -1.0,
            "debilitated": -2.0,
        }
        score += dignity_mods.get(dignity, 0.0)

        # Dig Bala
        dig_bala = False
        if DIG_BALA.get(planet_enum) == house:
            score += 1.5
            dig_bala = True

        # House placement bonus
        if house in KENDRA_HOUSES:
            score += 0.5
        elif house in TRIKONA_HOUSES:
            score += 0.3

        # Retrograde modifier
        notes = []
        if is_retro and planet_enum not in (Planet.RAHU, Planet.KETU):
            if planet_enum in NATURAL_BENEFICS:
                score -= 0.5
                notes.append("Retrograde benefic — introspective energy")
            else:
                score += 0.5
                notes.append("Retrograde malefic — intensified energy")

        score = max(0.0, min(10.0, round(score, 1)))

        return {
            "score": score,
            "dignity": dignity,
            "dig_bala": dig_bala,
            "house": house,
            "notes": notes,
        }

    def score_all_planets(self, planets: list[dict], asc_sign: int) -> dict:
        """Score all planets. Returns {planet_name: {score, dignity, ...}}."""
        return {
            p["planet"]: self.score_planet(p, asc_sign) for p in planets
        }

    # ── Module 2: Yoga Detector ──────────────────────────────────────────

    def _yoga_strength(self, planet_enum: Planet, sign_index: int) -> str:
        dignity = self._get_dignity(planet_enum, sign_index)
        if dignity in ("exalted", "own_sign", "moolatrikona"):
            return "strong"
        elif dignity in ("friendly", "neutral"):
            return "moderate"
        return "mild"

    def detect_raj_yogas(self, planets: list[dict], asc_sign: int) -> list[dict]:
        yogas = []
        trikonas = [1, 5, 9]
        kendras = [1, 4, 7, 10]

        for trik_h in trikonas:
            trik_lord = self._get_house_lord(trik_h, asc_sign)
            trik_pos = self._find_planet(trik_lord.value, planets)
            if not trik_pos:
                continue
            trik_house = self._get_planet_house(trik_pos["sign_index"], asc_sign)

            if trik_house in kendras and trik_house != trik_h:
                strength = self._yoga_strength(trik_lord, trik_pos["sign_index"])
                yogas.append({
                    "name": "Raj Yoga",
                    "yoga_type": "raj",
                    "strength": strength,
                    "forming_planets": [trik_lord.value],
                    "description": (
                        f"Lord of {_ordinal(trik_h)} house "
                        f"({trik_lord.value}) placed in {_ordinal(trik_house)} house (kendra)"
                    ),
                    "life_area_impact": ["career", "authority", "success"],
                })

        # Kendra lord in trikona
        for kend_h in [4, 7, 10]:
            kend_lord = self._get_house_lord(kend_h, asc_sign)
            kend_pos = self._find_planet(kend_lord.value, planets)
            if not kend_pos:
                continue
            kend_house = self._get_planet_house(kend_pos["sign_index"], asc_sign)

            if kend_house in [5, 9]:
                strength = self._yoga_strength(kend_lord, kend_pos["sign_index"])
                yogas.append({
                    "name": "Raj Yoga",
                    "yoga_type": "raj",
                    "strength": strength,
                    "forming_planets": [kend_lord.value],
                    "description": (
                        f"Lord of {_ordinal(kend_h)} house ({kend_lord.value}) "
                        f"placed in {_ordinal(kend_house)} house (trikona)"
                    ),
                    "life_area_impact": ["career", "authority", "success"],
                })

        return yogas

    def detect_dhana_yogas(self, planets: list[dict], asc_sign: int) -> list[dict]:
        yogas = []
        lord_2 = self._get_house_lord(2, asc_sign)
        lord_11 = self._get_house_lord(11, asc_sign)

        pos_2 = self._find_planet(lord_2.value, planets)
        pos_11 = self._find_planet(lord_11.value, planets)
        if not pos_2 or not pos_11:
            return yogas

        house_of_2 = self._get_planet_house(pos_2["sign_index"], asc_sign)
        house_of_11 = self._get_planet_house(pos_11["sign_index"], asc_sign)

        # Conjunction (same sign)
        if pos_2["sign_index"] == pos_11["sign_index"]:
            yogas.append({
                "name": "Dhana Yoga",
                "yoga_type": "dhana",
                "strength": "strong",
                "forming_planets": [lord_2.value, lord_11.value],
                "description": f"Lords of 2nd ({lord_2.value}) and 11th ({lord_11.value}) conjunct",
                "life_area_impact": ["finance", "wealth"],
            })
        # Exchange
        elif house_of_2 == 11 and house_of_11 == 2:
            yogas.append({
                "name": "Dhana Yoga",
                "yoga_type": "dhana",
                "strength": "strong",
                "forming_planets": [lord_2.value, lord_11.value],
                "description": f"Exchange between 2nd lord ({lord_2.value}) and 11th lord ({lord_11.value})",
                "life_area_impact": ["finance", "wealth"],
            })
        # One in the other's house
        elif house_of_2 == 11 or house_of_11 == 2:
            yogas.append({
                "name": "Dhana Yoga",
                "yoga_type": "dhana",
                "strength": "moderate",
                "forming_planets": [lord_2.value, lord_11.value],
                "description": f"2nd lord in 11th or 11th lord in 2nd house",
                "life_area_impact": ["finance", "wealth"],
            })

        return yogas

    def detect_viparita_yogas(self, planets: list[dict], asc_sign: int) -> list[dict]:
        yogas = []
        dusthanas = [6, 8, 12]

        for house in dusthanas:
            lord = self._get_house_lord(house, asc_sign)
            pos = self._find_planet(lord.value, planets)
            if not pos:
                continue
            lord_house = self._get_planet_house(pos["sign_index"], asc_sign)

            if lord_house in dusthanas and lord_house != house:
                yogas.append({
                    "name": "Viparita Raja Yoga",
                    "yoga_type": "viparita",
                    "strength": "moderate",
                    "forming_planets": [lord.value],
                    "description": (
                        f"Lord of {house}th (dusthana) placed in {lord_house}th "
                        f"(dusthana) — adversity converts to advantage"
                    ),
                    "life_area_impact": ["resilience", "unexpected_gains"],
                })

        return yogas

    def detect_gaja_kesari(self, planets: list[dict], asc_sign: int) -> list[dict]:
        jupiter = self._find_planet("Jupiter", planets)
        moon = self._find_planet("Moon", planets)
        if not jupiter or not moon:
            return []

        jupiter_from_moon = ((jupiter["sign_index"] - moon["sign_index"]) % 12) + 1

        if jupiter_from_moon in KENDRA_HOUSES:
            is_retro = jupiter.get("is_retrograde", False)
            return [{
                "name": "Gaja Kesari Yoga",
                "yoga_type": "gaja_kesari",
                "strength": "moderate" if is_retro else "strong",
                "forming_planets": ["Jupiter", "Moon"],
                "description": f"Jupiter in {jupiter_from_moon}th house from Moon (kendra)",
                "life_area_impact": ["wisdom", "reputation", "fortune"],
            }]
        return []

    def detect_kemadruma(self, planets: list[dict], asc_sign: int) -> list[dict]:
        moon = self._find_planet("Moon", planets)
        if not moon:
            return []

        moon_sign = moon["sign_index"]
        sign_2nd = (moon_sign % 12) + 1
        sign_12th = ((moon_sign - 2) % 12) + 1

        excluded = {"Sun", "Moon", "Rahu", "Ketu"}
        adjacent = [
            p for p in planets
            if p["planet"] not in excluded
            and p["sign_index"] in (sign_2nd, sign_12th)
        ]

        if not adjacent:
            # Check cancellation: Moon in kendra from lagna
            moon_house = self._get_planet_house(moon_sign, asc_sign)
            if moon_house in KENDRA_HOUSES:
                return []
            return [{
                "name": "Kemadruma Yoga",
                "yoga_type": "kemadruma",
                "strength": "moderate",
                "forming_planets": ["Moon"],
                "description": "No planets adjacent to Moon — indicates periods of emotional isolation",
                "life_area_impact": ["emotional_wellbeing", "social_life"],
            }]
        return []

    def detect_all_yogas(self, planets: list[dict], asc_sign: int) -> list[dict]:
        yogas = []
        yogas.extend(self.detect_raj_yogas(planets, asc_sign))
        yogas.extend(self.detect_dhana_yogas(planets, asc_sign))
        yogas.extend(self.detect_viparita_yogas(planets, asc_sign))
        yogas.extend(self.detect_gaja_kesari(planets, asc_sign))
        yogas.extend(self.detect_kemadruma(planets, asc_sign))
        return yogas

    # ── Module 3: Dosha Checker ──────────────────────────────────────────

    def check_mangal_dosha(self, planets: list[dict], asc_sign: int) -> Optional[dict]:
        mars = self._find_planet("Mars", planets)
        if not mars:
            return None

        mars_house = self._get_planet_house(mars["sign_index"], asc_sign)
        mangal_houses = {1, 2, 4, 7, 8, 12}

        if mars_house not in mangal_houses:
            return None

        severity_map = {7: "high", 8: "high", 1: "moderate", 4: "moderate", 2: "mild", 12: "mild"}
        severity = severity_map[mars_house]

        # Cancellation checks
        cancellations = []
        mars_sign = mars["sign_index"]
        if mars_sign in (Sign.ARIES, Sign.SCORPIO, Sign.CAPRICORN):
            cancellations.append("Mars in own/exalted sign")
            severity = "cancelled"

        jupiter = self._find_planet("Jupiter", planets)
        if jupiter and jupiter["sign_index"] == mars_sign:
            cancellations.append("Jupiter conjunct Mars")
            severity = "cancelled"

        return {
            "name": "Mangal Dosha",
            "is_present": severity != "cancelled",
            "severity": severity,
            "description": f"Mars in {mars_house}th house from ascendant",
            "remediation_category": "relationship" if mars_house in {7, 8} else "general",
            "details": {"mars_house": mars_house, "cancellations": cancellations},
        }

    def check_kaal_sarpa(self, planets: list[dict], asc_sign: int) -> Optional[dict]:
        rahu = self._find_planet("Rahu", planets)
        ketu = self._find_planet("Ketu", planets)
        if not rahu or not ketu:
            return None

        rahu_deg = rahu["absolute_degree"]
        ketu_deg = ketu["absolute_degree"]

        other_planets = [
            p for p in planets if p["planet"] not in ("Rahu", "Ketu")
        ]

        def all_between(start: float, end: float) -> bool:
            if not other_planets:
                return False  # Cannot form Kaal Sarpa without planets to hem
            for p in other_planets:
                deg = p["absolute_degree"]
                if start < end:
                    if not (start <= deg <= end):
                        return False
                else:
                    if not (deg >= start or deg <= end):
                        return False
            return True

        if all_between(rahu_deg, ketu_deg) or all_between(ketu_deg, rahu_deg):
            return {
                "name": "Kaal Sarpa Dosha",
                "is_present": True,
                "severity": "high",
                "description": "All planets hemmed between Rahu-Ketu axis",
                "remediation_category": "spiritual",
                "details": {},
            }
        return None

    def check_sade_sati(
        self, planets: list[dict], asc_sign: int, current_saturn_sign: Optional[int] = None
    ) -> Optional[dict]:
        if current_saturn_sign is None:
            return None

        moon = self._find_planet("Moon", planets)
        if not moon:
            return None

        moon_sign = moon["sign_index"]
        sign_12th = ((moon_sign - 2) % 12) + 1
        sign_1st = moon_sign
        sign_2nd = (moon_sign % 12) + 1

        phase = None
        if current_saturn_sign == sign_12th:
            phase = "rising"
        elif current_saturn_sign == sign_1st:
            phase = "peak"
        elif current_saturn_sign == sign_2nd:
            phase = "setting"

        if phase:
            return {
                "name": "Sade Sati",
                "is_present": True,
                "severity": "high" if phase == "peak" else "moderate",
                "description": f"Saturn transiting {phase} phase over natal Moon",
                "remediation_category": "saturn",
                "details": {"phase": phase},
            }
        return None

    def check_all_doshas(
        self, planets: list[dict], asc_sign: int, current_saturn_sign: Optional[int] = None
    ) -> list[dict]:
        doshas = []
        for checker in [
            lambda: self.check_mangal_dosha(planets, asc_sign),
            lambda: self.check_kaal_sarpa(planets, asc_sign),
            lambda: self.check_sade_sati(planets, asc_sign, current_saturn_sign),
        ]:
            result = checker()
            if result and result.get("is_present", True):
                doshas.append(result)
        return doshas

    # ── Module 4: Dasha Interpreter ──────────────────────────────────────

    def calculate_dasha(
        self, planets: list[dict], chart_data: dict, reference_dt: datetime
    ) -> dict:
        moon = self._find_planet("Moon", planets)
        if not moon:
            return self._empty_dasha()

        moon_longitude = moon["absolute_degree"]
        nak_index = int(moon_longitude / NAKSHATRA_SPAN)
        nak_index = min(nak_index, 26)

        starting_lord = NAKSHATRA_LORDS[nak_index]

        # Find lord in vimshottari sequence
        try:
            lord_idx = next(
                i for i, (p, _) in enumerate(VIMSHOTTARI_LORDS)
                if p == starting_lord
            )
        except StopIteration:
            return self._empty_dasha()

        # Fraction of nakshatra elapsed at birth
        degree_in_nak = moon_longitude % NAKSHATRA_SPAN
        fraction_elapsed = degree_in_nak / NAKSHATRA_SPAN

        total_years = VIMSHOTTARI_LORDS[lord_idx][1]
        remaining_years = total_years * (1 - fraction_elapsed)

        # Parse birth datetime
        birth_dt = self._parse_birth_dt(chart_data)

        # Build dasha sequence
        dasha_sequence = []
        current_start = birth_dt

        # First (partial) dasha
        dasha_end = current_start + timedelta(days=remaining_years * 365.25)
        dasha_sequence.append({
            "lord": starting_lord.value,
            "start": current_start.isoformat(),
            "end": dasha_end.isoformat(),
            "years": round(remaining_years, 2),
        })
        current_start = dasha_end

        # Full dashas (cycle through all 9)
        for i in range(1, 10):
            idx = (lord_idx + i) % 9
            planet, years = VIMSHOTTARI_LORDS[idx]
            dasha_end = current_start + timedelta(days=years * 365.25)
            dasha_sequence.append({
                "lord": planet.value,
                "start": current_start.isoformat(),
                "end": dasha_end.isoformat(),
                "years": years,
            })
            current_start = dasha_end

        # Find current mahadasha
        current_md = self._find_current_period(dasha_sequence, reference_dt)
        if not current_md:
            current_md = dasha_sequence[-1]

        # Calculate bhuktis for current mahadasha
        bhuktis = self._calculate_bhuktis(current_md)
        current_bhukti = self._find_current_period(bhuktis, reference_dt)
        if not current_bhukti:
            current_bhukti = bhuktis[0]

        # Find upcoming transitions within 12 months
        future_limit = reference_dt + timedelta(days=365)
        transitions = []
        for period in dasha_sequence + bhuktis:
            period_end = datetime.fromisoformat(period["end"])
            if reference_dt < period_end <= future_limit:
                transitions.append({
                    "type": "mahadasha" if period in dasha_sequence else "antardasha",
                    "lord": period["lord"],
                    "date": period["end"],
                })

        # Generate narrative
        asc_sign = chart_data["ascendant_sign_index"]
        narrative = self._dasha_narrative(current_md, current_bhukti, planets, asc_sign)

        return {
            "current_mahadasha": current_md,
            "current_antardasha": current_bhukti,
            "mahadasha_narrative": narrative,
            "transitions_within_12_months": transitions[:5],
            "dasha_sequence": dasha_sequence,
        }

    def _calculate_bhuktis(self, mahadasha: dict) -> list[dict]:
        md_lord_name = mahadasha["lord"]
        md_lord_idx = next(
            i for i, (p, _) in enumerate(VIMSHOTTARI_LORDS)
            if p.value == md_lord_name
        )
        md_years = mahadasha["years"]
        md_start = datetime.fromisoformat(mahadasha["start"])

        bhuktis = []
        bhukti_start = md_start
        for i in range(9):
            idx = (md_lord_idx + i) % 9
            planet, planet_years = VIMSHOTTARI_LORDS[idx]
            bhukti_years = (md_years * planet_years) / VIMSHOTTARI_TOTAL
            bhukti_end = bhukti_start + timedelta(days=bhukti_years * 365.25)
            bhuktis.append({
                "lord": planet.value,
                "start": bhukti_start.isoformat(),
                "end": bhukti_end.isoformat(),
                "years": round(bhukti_years, 2),
            })
            bhukti_start = bhukti_end

        return bhuktis

    def _find_current_period(self, periods: list[dict], ref_dt: datetime) -> Optional[dict]:
        for period in periods:
            start = datetime.fromisoformat(period["start"])
            end = datetime.fromisoformat(period["end"])
            if start <= ref_dt < end:
                return period
        return None

    def _dasha_narrative(
        self, mahadasha: dict, bhukti: dict, planets: list[dict], asc_sign: int
    ) -> str:
        md_lord_name = mahadasha["lord"]
        md_planet = self._find_planet(md_lord_name, planets)
        if not md_planet:
            return f"You are in {md_lord_name} Mahadasha."

        md_enum = self._planet_enum(md_lord_name)
        md_house = self._get_planet_house(md_planet["sign_index"], asc_sign)
        ruled = self._houses_ruled_by(md_enum, asc_sign) if md_enum else []
        dignity = self._get_dignity(md_enum, md_planet["sign_index"]) if md_enum else "neutral"

        # Gather life domains
        domains = set()
        for h in [md_house] + ruled:
            domains.update(HOUSE_DOMAINS.get(h, []))

        tone = "favorable" if dignity in ("exalted", "own_sign", "friendly", "moolatrikona") else \
               "challenging" if dignity in ("enemy", "debilitated") else "mixed"

        narrative = (
            f"You are in {md_lord_name} Mahadasha / {bhukti['lord']} Antardasha. "
            f"{md_lord_name} rules house(s) {', '.join(str(h) for h in ruled)} "
            f"and sits in the {md_house}th house ({dignity}). "
            f"This is a {tone} period activating themes of "
            f"{', '.join(sorted(domains)[:5])}."
        )
        return narrative

    def _parse_birth_dt(self, chart_data: dict) -> datetime:
        """Try to extract birth datetime from chart data or birth input."""
        for key in ("birth_datetime", "birth_date"):
            if key in chart_data:
                val = chart_data[key]
                if isinstance(val, datetime):
                    return val
                try:
                    return datetime.fromisoformat(str(val))
                except (ValueError, TypeError) as e:
                    import logging
                    logging.getLogger(__name__).warning(
                        f"Could not parse birth datetime from '{key}': {val!r} — {e}"
                    )
        import logging
        logging.getLogger(__name__).error(
            "No valid birth_datetime in chart_data; dasha anchored to fallback 1990-01-01"
        )
        return datetime(1990, 1, 1)

    def _empty_dasha(self) -> dict:
        return {
            "current_mahadasha": {"lord": "Unknown", "start": "", "end": "", "years": 0},
            "current_antardasha": {"lord": "Unknown", "start": "", "end": "", "years": 0},
            "mahadasha_narrative": "Dasha calculation requires Moon position data.",
            "transitions_within_12_months": [],
            "dasha_sequence": [],
        }

    # ── Module 5: Area-Specific Analyzer ─────────────────────────────────

    def analyze_area(
        self, domain: str, planets: list[dict], asc_sign: int, strengths: dict
    ) -> dict:
        houses = DOMAIN_TO_HOUSES.get(domain, [1])
        relevant = []

        for house_num in houses:
            lord = self._get_house_lord(house_num, asc_sign)
            lord_pos = self._find_planet(lord.value, planets)
            lord_house = (
                self._get_planet_house(lord_pos["sign_index"], asc_sign)
                if lord_pos else 0
            )
            lord_score = strengths.get(lord.value, {}).get("score", 5.0)

            occupants = self._planets_in_house(house_num, planets, asc_sign)

            relevant.append({
                "house": house_num,
                "sign_index": ((asc_sign - 1 + house_num - 1) % 12) + 1,
                "lord": lord.value,
                "lord_placed_in_house": lord_house,
                "lord_strength": lord_score,
                "occupants": [
                    {"planet": p["planet"], "strength": strengths.get(p["planet"], {}).get("score", 5.0)}
                    for p in occupants
                ],
            })

        lord_scores = [h["lord_strength"] for h in relevant]
        avg = round(sum(lord_scores) / len(lord_scores), 1) if lord_scores else 5.0

        return {
            "domain": domain,
            "relevant_houses": relevant,
            "summary_strength": avg,
        }
