"""Tests for VedicLogicEngine — yoga detection, dosha checking, strength scoring, dasha."""

import pytest
from datetime import datetime

from app.services.logic_engine import VedicLogicEngine
from app.services.vedic_data import Sign

engine = VedicLogicEngine()


class TestPlanetaryStrength:
    def test_exalted_planet_high_score(self, aries_ascendant_chart):
        """Moon in Taurus (exalted) should score high."""
        planets = aries_ascendant_chart["planets"]
        asc = aries_ascendant_chart["ascendant_sign_index"]
        strengths = engine.score_all_planets(planets, asc)
        moon = strengths["Moon"]
        assert moon["dignity"] == "exalted"
        assert moon["score"] >= 8.0

    def test_mars_exalted_in_capricorn(self, aries_ascendant_chart):
        """Mars in Capricorn should be exalted."""
        planets = aries_ascendant_chart["planets"]
        asc = aries_ascendant_chart["ascendant_sign_index"]
        strengths = engine.score_all_planets(planets, asc)
        mars = strengths["Mars"]
        assert mars["dignity"] == "exalted"
        assert mars["score"] >= 8.0

    def test_dig_bala_bonus(self, aries_ascendant_chart):
        """Mars in 10th house should get dig bala bonus."""
        planets = aries_ascendant_chart["planets"]
        asc = aries_ascendant_chart["ascendant_sign_index"]
        strengths = engine.score_all_planets(planets, asc)
        mars = strengths["Mars"]
        assert mars["dig_bala"] is True

    def test_retrograde_malefic_bonus(self, aries_ascendant_chart):
        """Retrograde Saturn (malefic) should get +0.5 bonus."""
        planets = aries_ascendant_chart["planets"]
        asc = aries_ascendant_chart["ascendant_sign_index"]
        strengths = engine.score_all_planets(planets, asc)
        saturn = strengths["Saturn"]
        assert "Retrograde malefic" in saturn["notes"][0]

    def test_score_clamped_0_10(self, aries_ascendant_chart):
        planets = aries_ascendant_chart["planets"]
        asc = aries_ascendant_chart["ascendant_sign_index"]
        strengths = engine.score_all_planets(planets, asc)
        for name, data in strengths.items():
            assert 0.0 <= data["score"] <= 10.0, f"{name} score out of range: {data['score']}"


class TestYogaDetection:
    def test_raj_yoga_detected(self, aries_ascendant_chart):
        """Jupiter (9th lord for Aries) in 1st house should trigger Raj Yoga."""
        planets = aries_ascendant_chart["planets"]
        asc = aries_ascendant_chart["ascendant_sign_index"]
        yogas = engine.detect_raj_yogas(planets, asc)
        raj_yogas = [y for y in yogas if y["name"] == "Raj Yoga"]
        assert len(raj_yogas) >= 1
        assert any("Jupiter" in y["forming_planets"] for y in raj_yogas)

    def test_gaja_kesari_detected(self, gaja_kesari_chart):
        """Jupiter in Cancer (4th from Moon in Aries) should trigger Gaja Kesari."""
        planets = gaja_kesari_chart["planets"]
        asc = gaja_kesari_chart["ascendant_sign_index"]
        yogas = engine.detect_gaja_kesari(planets, asc)
        assert len(yogas) == 1
        assert yogas[0]["name"] == "Gaja Kesari Yoga"
        assert yogas[0]["strength"] == "strong"

    def test_kemadruma_detected(self, kemadruma_chart):
        """Moon in Leo with no planets in Cancer/Virgo should trigger Kemadruma."""
        planets = kemadruma_chart["planets"]
        asc = kemadruma_chart["ascendant_sign_index"]
        yogas = engine.detect_kemadruma(planets, asc)
        assert len(yogas) == 1
        assert yogas[0]["name"] == "Kemadruma Yoga"

    def test_no_false_gaja_kesari(self, aries_ascendant_chart):
        """Should NOT detect Gaja Kesari when Jupiter is not in kendra from Moon."""
        planets = aries_ascendant_chart["planets"]
        asc = aries_ascendant_chart["ascendant_sign_index"]
        yogas = engine.detect_gaja_kesari(planets, asc)
        # Jupiter in Aries (sign 1), Moon in Taurus (sign 2) -> 12th from Moon, not kendra
        assert len(yogas) == 0


class TestDoshaChecker:
    def test_mangal_dosha_high_severity(self, mangal_dosha_chart):
        """Mars in 7th house should trigger Mangal Dosha with high severity."""
        planets = mangal_dosha_chart["planets"]
        asc = mangal_dosha_chart["ascendant_sign_index"]
        result = engine.check_mangal_dosha(planets, asc)
        assert result is not None
        assert result["is_present"] is True
        assert result["severity"] == "high"
        assert result["details"]["mars_house"] == 7

    def test_mangal_dosha_cancellation(self, aries_ascendant_chart):
        """Mars in Capricorn (exalted) in 10th — not a Mangal Dosha house."""
        planets = aries_ascendant_chart["planets"]
        asc = aries_ascendant_chart["ascendant_sign_index"]
        result = engine.check_mangal_dosha(planets, asc)
        # Mars is in 10th house, not in {1,2,4,7,8,12}
        assert result is None

    def test_sade_sati_peak(self, aries_ascendant_chart):
        """Saturn transiting Moon's sign (Taurus=2) should trigger peak Sade Sati."""
        planets = aries_ascendant_chart["planets"]
        asc = aries_ascendant_chart["ascendant_sign_index"]
        result = engine.check_sade_sati(planets, asc, current_saturn_sign=2)
        assert result is not None
        assert result["is_present"] is True
        assert result["severity"] == "high"
        assert result["details"]["phase"] == "peak"

    def test_no_sade_sati_when_saturn_distant(self, aries_ascendant_chart):
        """Saturn far from Moon sign should not trigger Sade Sati."""
        planets = aries_ascendant_chart["planets"]
        asc = aries_ascendant_chart["ascendant_sign_index"]
        result = engine.check_sade_sati(planets, asc, current_saturn_sign=8)
        assert result is None


class TestDashaCalculation:
    def test_dasha_has_required_fields(self, aries_ascendant_chart):
        planets = aries_ascendant_chart["planets"]
        ref_dt = datetime(2026, 4, 1)
        result = engine.calculate_dasha(planets, aries_ascendant_chart, ref_dt)
        assert "current_mahadasha" in result
        assert "current_antardasha" in result
        assert "mahadasha_narrative" in result
        assert "dasha_sequence" in result
        assert len(result["dasha_sequence"]) == 10  # 1 partial + 9 full

    def test_dasha_sequence_covers_120_years(self, aries_ascendant_chart):
        planets = aries_ascendant_chart["planets"]
        ref_dt = datetime(2026, 4, 1)
        result = engine.calculate_dasha(planets, aries_ascendant_chart, ref_dt)
        total_years = sum(d["years"] for d in result["dasha_sequence"])
        assert abs(total_years - 120.0) < 1.0  # within 1 year of 120


class TestAreaAnalyzer:
    def test_career_analysis(self, aries_ascendant_chart):
        planets = aries_ascendant_chart["planets"]
        asc = aries_ascendant_chart["ascendant_sign_index"]
        strengths = engine.score_all_planets(planets, asc)
        result = engine.analyze_area("career", planets, asc, strengths)
        assert result["domain"] == "career"
        assert len(result["relevant_houses"]) > 0
        assert 0 <= result["summary_strength"] <= 10


class TestFullEnrich:
    def test_enrich_returns_all_sections(self, aries_ascendant_chart):
        result = engine.enrich(aries_ascendant_chart, reference_dt=datetime(2026, 4, 1))
        assert "planetary_strengths" in result
        assert "yogas" in result
        assert "doshas" in result
        assert "dasha" in result
        assert "area_analysis" in result
        assert len(result["planetary_strengths"]) == 9  # all 9 planets
