import re
import uuid
from datetime import date, datetime, time
from typing import Literal, Optional

from pydantic import BaseModel, Field, field_validator

SAFE_TEXT = re.compile(r"^[a-zA-Z\s'\-\.]{1,100}$")


class BirthInput(BaseModel):
    full_name: str = Field(..., min_length=2, max_length=100)
    birth_date: date
    birth_time: time
    birth_city: str = Field(..., min_length=2, max_length=100)
    birth_country: str = Field(..., min_length=2, max_length=100)
    gender: Optional[Literal["male", "female", "other"]] = None
    reading_type: Literal["career", "relationships", "health", "finance", "general"] = (
        "general"
    )

    @field_validator("full_name", "birth_city", "birth_country")
    @classmethod
    def no_injection(cls, v: str) -> str:
        if not SAFE_TEXT.match(v):
            raise ValueError("Contains invalid characters")
        return v.strip()

    @field_validator("birth_date")
    @classmethod
    def reasonable_date(cls, v: date) -> date:
        if v.year < 1900 or v > date.today():
            raise ValueError("Birth date must be between 1900 and today")
        return v


class LocationData(BaseModel):
    latitude: float
    longitude: float
    timezone_id: str
    utc_offset: float
    dst_active: bool = False


class PlanetPosition(BaseModel):
    planet: str
    sign: str
    sign_index: int  # 1-12 (Aries=1)
    degree: float  # 0-29.99 within sign
    absolute_degree: float  # 0-359.99 sidereal longitude
    nakshatra: str
    nakshatra_index: int  # 0-26
    nakshatra_pada: int  # 1-4
    house: int  # 1-12
    is_retrograde: bool = False
    strength_score: float = 5.0
    dignity: str = "neutral"
    special_notes: list[str] = Field(default_factory=list)
    source: str = "api"


class ChartData(BaseModel):
    ascendant_sign: str
    ascendant_sign_index: int  # 1-12
    ascendant_degree: float
    moon_sign: str
    sun_sign: str
    planets: list[PlanetPosition]
    source: str = "api"


class YogaResult(BaseModel):
    name: str
    yoga_type: str
    strength: Literal["strong", "moderate", "mild"]
    forming_planets: list[str]
    description: str
    life_area_impact: list[str]


class DoshaResult(BaseModel):
    name: str
    is_present: bool
    severity: Literal["high", "moderate", "mild", "cancelled"]
    description: str
    remediation_category: str
    details: dict = Field(default_factory=dict)


class DashaPeriod(BaseModel):
    lord: str
    start: str  # ISO datetime
    end: str
    years: float


class DashaInfo(BaseModel):
    current_mahadasha: DashaPeriod
    current_antardasha: DashaPeriod
    mahadasha_narrative: str
    transitions_within_12_months: list[dict] = Field(default_factory=list)
    dasha_sequence: list[DashaPeriod] = Field(default_factory=list)


class AreaAnalysis(BaseModel):
    domain: str
    relevant_houses: list[dict]
    summary_strength: float
    summary: str = ""


class EnrichedContext(BaseModel):
    birth_input: BirthInput
    location: LocationData
    chart: ChartData
    planetary_strengths: dict  # {planet_name: {score, dignity, dig_bala, ...}}
    yogas: list[YogaResult]
    doshas: list[DoshaResult]
    dasha: DashaInfo
    area_analysis: dict  # {domain: AreaAnalysis}


class ReadingSection(BaseModel):
    title: str
    insight: str
    actions: list[str] = Field(default_factory=list)


class KeyPeriod(BaseModel):
    period: str
    theme: str
    guidance: str


class ReadingResponse(BaseModel):
    reading_id: uuid.UUID = Field(default_factory=uuid.uuid4)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    subject_name: str
    reading_type: str
    overview: str
    sections: list[ReadingSection]
    key_periods: list[KeyPeriod] = Field(default_factory=list)
    closing: str
    chart_summary: dict = Field(default_factory=dict)
    processing_time_ms: int = 0


class APIError(BaseModel):
    error_code: str
    message: str
    suggestion: str = ""
    request_id: str = ""
