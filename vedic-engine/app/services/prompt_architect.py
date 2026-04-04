"""Prompt Architect — converts EnrichedContext into structured AI prompts."""

import re

from app.utils.logger import logger

INJECTION_PATTERNS = [
    r"ignore\s+(previous|above|all)\s+instructions",
    r"you\s+are\s+now",
    r"system\s*prompt",
    r"jailbreak",
    r"DAN\s+mode",
    r"act\s+as\s+if",
    r"pretend\s+to\s+be",
]

SYSTEM_PROMPT = """You are an elite Vedic Astrology consultant with 25 years of practical experience advising
entrepreneurs, executives, and individuals on life strategy. Your approach is:

ANALYTICAL: You derive insights from planetary positions, yogas, doshas, and dasha cycles —
never from generic descriptions. Every statement must be traceable to specific astrological
data in the brief you receive.

EMPATHETIC BUT DIRECT: You speak with warmth and respect, but you do not soften important
warnings. You tell people what they need to hear, framed constructively.

ACTION-ORIENTED: You always end each section with 1-3 specific, time-bound actions the
person can take in the next 30-90 days based on their current dasha and transits.

ANTI-GENERIC: You NEVER use vague language like "this is a good time for growth" or
"challenges may arise." Every sentence must be specific to the data in the brief.

STRUCTURED OUTPUT FORMAT:
Return your reading in the following JSON structure only — no prose outside the JSON:
{
  "overview": "2-3 sentence high-level summary",
  "sections": [
    {
      "title": "section name",
      "insight": "analytical insight paragraph",
      "actions": ["action 1", "action 2", "action 3"]
    }
  ],
  "key_periods": [
    {"period": "month/year range", "theme": "theme", "guidance": "what to do"}
  ],
  "closing": "empathetic closing statement with one overarching theme"
}

You have received a structured astrological brief. Base every sentence on that brief.
Do not add information not present in the brief."""


class PromptArchitect:
    def build_system_prompt(self, reading_type: str) -> str:
        type_addendum = {
            "career": "\nFocus on career trajectory, professional timing, and authority-building.",
            "relationships": "\nFocus on partnership dynamics, compatibility indicators, and relationship timing.",
            "finance": "\nFocus on wealth accumulation timing, investment windows, and financial risks.",
            "health": "\nFocus on vitality periods, vulnerability windows, and preventive actions.",
            "general": "",
        }
        return SYSTEM_PROMPT + type_addendum.get(reading_type, "")

    def build_user_prompt(self, enriched: dict, reading_type: str) -> str:
        """Assemble structured analytical brief from enriched context."""
        birth = enriched.get("birth_input", {})
        chart = enriched.get("chart", {})
        strengths = enriched.get("planetary_strengths", {})
        yogas = enriched.get("yogas", [])
        doshas = enriched.get("doshas", [])
        dasha = enriched.get("dasha", {})
        area = enriched.get("area_analysis", {}).get(reading_type, {})

        sections = {}

        # Section 1: Planetary Snapshot
        name = sanitize_for_prompt(str(birth.get("full_name", "Subject")))
        city = sanitize_for_prompt(str(birth.get("birth_city", "")))
        lines = [
            f"ASTROLOGICAL BRIEF FOR: {name}",
            f"READING FOCUS: {reading_type}",
            f"BIRTH: {birth.get('birth_date', '')} at {birth.get('birth_time', '')} in {city}",
            "",
            "PLANETARY SNAPSHOT:",
            f"- Ascendant: {chart.get('ascendant_sign', 'Unknown')}",
        ]
        planets = chart.get("planets", [])
        for p in planets:
            pname = p["planet"]
            s = strengths.get(pname, {})
            retro = " (R)" if p.get("is_retrograde") else ""
            lines.append(
                f"- {pname} in {p.get('sign', '?')} ({p.get('house', '?')}th house){retro} "
                f"— score {s.get('score', '?')}/10, {s.get('dignity', '?')}"
            )
        sections["planetary_snapshot"] = "\n".join(lines)

        # Section 2: Active Yogas
        if yogas:
            yoga_lines = ["", "ACTIVE YOGAS:"]
            for y in yogas:
                yoga_lines.append(
                    f"- {y['name']} ({y['strength'].title()}): "
                    f"{y.get('description', '')} → areas: {', '.join(y.get('life_area_impact', []))}"
                )
            sections["yogas"] = "\n".join(yoga_lines)

        # Section 3: Active Doshas
        if doshas:
            dosha_lines = ["", "ACTIVE DOSHAS:"]
            for d in doshas:
                dosha_lines.append(
                    f"- {d['name']} ({d['severity'].title()}): "
                    f"{d.get('description', '')} — remediation: {d.get('remediation_category', '')}"
                )
            sections["doshas"] = "\n".join(dosha_lines)

        # Section 4: Current Dasha
        md = dasha.get("current_mahadasha", {})
        ad = dasha.get("current_antardasha", {})
        narrative = dasha.get("mahadasha_narrative", "")
        dasha_text = [
            "",
            "CURRENT DASHA:",
            f"- Mahadasha: {md.get('lord', '?')} | Antardasha: {ad.get('lord', '?')}",
            f"- {narrative}",
        ]
        transitions = dasha.get("transitions_within_12_months", [])
        if transitions:
            dasha_text.append("- Upcoming transitions:")
            for t in transitions[:3]:
                dasha_text.append(f"  - {t.get('lord', '?')} {t.get('type', '')} around {t.get('date', '?')[:10]}")
        sections["dasha"] = "\n".join(dasha_text)

        # Section 5: Domain-specific analysis
        if area:
            area_lines = [f"", f"{reading_type.upper()}-SPECIFIC ANALYSIS:"]
            for h in area.get("relevant_houses", []):
                occ = ", ".join(o["planet"] for o in h.get("occupants", []))
                area_lines.append(
                    f"- House {h['house']}: lord {h['lord']} (strength {h['lord_strength']}/10) "
                    f"in {h['lord_placed_in_house']}th house"
                    + (f", occupied by {occ}" if occ else "")
                )
            area_lines.append(f"- Overall domain strength: {area.get('summary_strength', '?')}/10")
            sections["domain_analysis"] = "\n".join(area_lines)

        # Assemble with token budget
        return truncate_to_budget(sections)


def estimate_tokens(text: str) -> int:
    return int(len(text.split()) * 1.35)


def truncate_to_budget(sections: dict, max_tokens: int = 3500) -> str:
    """Assemble sections in priority order, truncating if needed."""
    priority = [
        "planetary_snapshot", "yogas", "doshas", "dasha",
        "domain_analysis", "tensions",
    ]
    result_parts = []
    used = 0

    for key in priority:
        if key not in sections:
            continue
        chunk = sections[key]
        chunk_tokens = estimate_tokens(chunk)
        if used + chunk_tokens <= max_tokens:
            result_parts.append(chunk)
            used += chunk_tokens
        else:
            remaining = max_tokens - used
            if remaining > 50:
                words = chunk.split()[:int(remaining / 1.35)]
                result_parts.append(" ".join(words) + " [truncated]")
            break

    return "\n".join(result_parts)


def sanitize_for_prompt(text: str) -> str:
    """Check for prompt injection patterns and sanitize."""
    for pattern in INJECTION_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            raise ValueError("Input contains disallowed content")
    return text.replace("{", "[").replace("}", "]").strip()
