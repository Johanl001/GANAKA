"""
KP (Krishnamurti Paddhati) Chart Calculation Engine

Computes Vedic astrology charts using Swiss Ephemeris (pysweph).
KP layer: KP ayanamsa, Placidus house cusps, Vimshottari dasha, 249 sub-divisions.

Usage:
    from chart import compute_chart
    chart = compute_chart(
        year=1990, month=5, day=15, hour=14, minute=30, second=0,
        latitude=19.0760, longitude=72.8777,
        timezone="Asia/Kolkata",
        ayanamsa="KP"
    )
"""

from __future__ import annotations

import json
import math
from dataclasses import dataclass, field
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
from typing import Optional

import swisseph as swe

# ---------------------------------------------------------------------------
# Swiss Ephemeris setup
# ---------------------------------------------------------------------------

# Point to ephemeris data directory. Must contain .se1 files (seas_18.se1, sepl_18.se1, etc.)
# Download from https://www.astro.com/ftp/swisseph/ephe/
EPHE_PATH = "ephe"
swe.set_ephe_path(EPHE_PATH)

# Planet constants (Swiss Ephemeris)
PLANETS = {
    "Sun": swe.SUN,
    "Moon": swe.MOON,
    "Mars": swe.MARS,
    "Mercury": swe.MERCURY,
    "Jupiter": swe.JUPITER,
    "Venus": swe.VENUS,
    "Saturn": swe.SATURN,
    "Rahu": swe.TRUE_NODE,   # True North Node
    "Ketu": swe.MEAN_NODE,   # Mean South Node (approximation)
}

# Vimshottari dasha lord order (9 lords)
DHASA_LORDS = ["Ketu", "Venus", "Sun", "Moon", "Mars", "Rahu", "Jupiter", "Saturn", "Mercury"]

# Vimshottari full years for each lord (total 120)
DHASA_YEARS = {
    "Ketu": 7,
    "Venus": 20,
    "Sun": 6,
    "Moon": 10,
    "Mars": 7,
    "Rahu": 18,
    "Jupiter": 16,
    "Saturn": 19,
    "Mercury": 17,
}

# Nakshatra lords in Vimshottari order (27 nakshatras)
NAKSHATRA_LORDS = [
    "Ketu", "Venus", "Sun", "Moon", "Mars", "Rahu", "Jupiter", "Saturn", "Mercury",
    "Ketu", "Venus", "Sun", "Moon", "Mars", "Rahu", "Jupiter", "Saturn", "Mercury",
    "Ketu", "Venus", "Sun", "Moon", "Mars", "Rahu", "Jupiter", "Saturn", "Mercury",
]

# Zodiac signs (30 degrees each)
SIGNS = [
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
]

# Sign lords (rulers)
SIGN_LORDS = {
    "Aries": "Mars", "Taurus": "Venus", "Gemini": "Mercury", "Cancer": "Moon",
    "Leo": "Sun", "Virgo": "Mercury", "Libra": "Venus", "Scorpio": "Mars",
    "Sagittarius": "Jupiter", "Capricorn": "Saturn", "Aquarius": "Saturn", "Pisces": "Jupiter",
}


# ---------------------------------------------------------------------------
# Time utilities
# ---------------------------------------------------------------------------

def local_to_utc(
    year: int, month: int, day: int,
    hour: int, minute: int, second: int,
    tz_name: str,
) -> datetime:
    """Convert local birth time to UTC using IANA timezone (handles historical DST)."""
    tz = ZoneInfo(tz_name)
    dt_local = datetime(year, month, day, hour, minute, second, tzinfo=tz)
    dt_utc = dt_local.astimezone(timezone.utc)
    return dt_utc


def julday_from_utc(dt_utc: datetime) -> float:
    """Compute Julian Day from a UTC datetime."""
    return swe.julday(
        dt_utc.year, dt_utc.month, dt_utc.day,
        dt_utc.hour + dt_utc.minute / 60 + dt_utc.second / 3600,
    )


# ---------------------------------------------------------------------------
# Ayanamsa
# ---------------------------------------------------------------------------

def set_ayanamsa(mode: str = "KP") -> None:
    """Set sidereal mode in Swiss Ephemeris."""
    if mode.upper() == "KP":
        swe.set_sid_mode(swe.SIDM_KP)
    elif mode.upper() == "LAHIRI":
        swe.set_sid_mode(swe.SIDM_LAHIRI)
    else:
        raise ValueError(f"Unknown ayanamsa mode: {mode}")


def get_ayanamsa(jd_ut: float) -> float:
    """Return ayanamsa value in degrees for the given Julian Day (UT)."""
    return swe.get_ayanamsa_ut(jd_ut)


# ---------------------------------------------------------------------------
# Planetary positions
# ---------------------------------------------------------------------------

@dataclass
class PlanetPosition:
    name: str
    tropical_longitude: float
    sidereal_longitude: float
    sign: str
    sign_degree: float
    nakshatra: str
    nakshatra_pada: int
    star_lord: str
    sub_lord: str
    sub_sub_lord: str
    house: int
    speed: float
    is_retrograde: bool


def sign_from_longitude(lon: float) -> tuple[str, float]:
    """Return (sign_name, degree_within_sign) from a longitude (0-360)."""
    sign_index = int(lon // 30) % 12
    degree = lon % 30
    return SIGNS[sign_index], degree


def nakshatra_from_longitude(lon: float) -> tuple[str, int, str]:
    """Return (nakshatra_name, pada, lord) from sidereal longitude.

    Each nakshatra = 13°20' (800 arc-minutes). 4 padas of 3°20' each.
    """
    lon_norm = lon % 360
    nak_index = int(lon_norm // (360 / 27))  # 0-26
    nak_start = nak_index * (360 / 27)
    pos_in_nak = lon_norm - nak_start
    pada = int(pos_in_nak // ((360 / 27) / 4)) + 1  # 1-4
    lord = NAKSHATRA_LORDS[nak_index]
    return f"Nakshatra {nak_index + 1}", pada, lord


def sub_lord_from_longitude(sidereal_lon: float, star_lord: str) -> tuple[str, str]:
    """Compute sub-lord and sub-sub-lord from sidereal longitude.

    Each nakshatra (13°20') is divided into 9 sub-portions in Vimshottari order.
    Sub-arc = (lord's years / 120) * 800 arc-minutes.
    """
    lon_norm = sidereal_lon % 360
    nak_index = int(lon_norm // (360 / 27))
    nak_start = nak_index * (360 / 27)
    pos_in_nak = lon_norm - nak_start  # degrees within nakshatra

    # Sub-lords start from the nakshatra's own lord and go in Vimshottari order
    start_lord_index = DHASA_LORDS.index(NAKSHATRA_LORDS[nak_index])
    pos_in_arcmin = pos_in_nak * 60  # arc-minutes

    current = 0.0
    sub_lord = None
    sub_start = 0.0
    for i in range(9):
        lord = DHASA_LORDS[(start_lord_index + i) % 9]
        sub_arc_arcmin = (DHASA_YEARS[lord] / 120) * 800
        if pos_in_arcmin < current + sub_arc_arcmin:
            sub_lord = lord
            sub_start = current
            break
        current += sub_arc_arcmin

    if sub_lord is None:
        sub_lord = DHASA_LORDS[(start_lord_index + 8) % 9]
        sub_start = current

    # Sub-sub-lord: divide the sub segment further in Vimshottari order starting from sub_lord
    pos_in_sub = pos_in_arcmin - sub_start
    sub_sub_start_lord_index = DHASA_LORDS.index(sub_lord)
    current2 = 0.0
    sub_sub_lord = None
    for i in range(9):
        lord = DHASA_LORDS[(sub_sub_start_lord_index + i) % 9]
        # Sub-sub arc: proportional within the sub segment
        sub_sub_arc_arcmin = (DHASA_YEARS[lord] / 120) * 800 / 9
        if pos_in_sub < current2 + sub_sub_arc_arcmin:
            sub_sub_lord = lord
            break
        current2 += sub_sub_arc_arcmin

    if sub_sub_lord is None:
        sub_sub_lord = DHASA_LORDS[(sub_sub_start_lord_index + 8) % 9]

    return sub_lord, sub_sub_lord


def compute_planet_positions(
    jd_ut: float,
    ayanamsa: float,
) -> dict[str, PlanetPosition]:
    """Compute sidereal positions for all planets."""
    positions: dict[str, PlanetPosition] = {}

    for name, planet_id in PLANETS.items():
        # Get tropical position
        result, ret = swe.calc_ut(jd_ut, planet_id)
        if ret < 0:
            continue

        tropical_lon = result[0]  # ecliptic longitude
        speed = result[3]         # longitude speed (degrees/day)
        is_retrograde = speed < 0

        # Convert to sidereal
        sidereal_lon = (tropical_lon - ayanamsa) % 360

        sign_name, sign_degree = sign_from_longitude(sidereal_lon)
        nak_name, pada, star_lord = nakshatra_from_longitude(sidereal_lon)
        sub_lord, sub_sub_lord = sub_lord_from_longitude(sidereal_lon, star_lord)

        positions[name] = PlanetPosition(
            name=name,
            tropical_longitude=tropical_lon,
            sidereal_longitude=sidereal_lon,
            sign=sign_name,
            sign_degree=sign_degree,
            nakshatra=nak_name,
            nakshatra_pada=pada,
            star_lord=star_lord,
            sub_lord=sub_lord,
            sub_sub_lord=sub_sub_lord,
            house=0,  # set later by house assignment
            speed=speed,
            is_retrograde=is_retrograde,
        )

    return positions


# ---------------------------------------------------------------------------
# Houses (Placidus)
# ---------------------------------------------------------------------------

@dataclass
class HouseCusp:
    house: int
    longitude: float
    sign: str
    sign_degree: float
    sub_lord: str
    sub_sub_lord: str


def compute_houses(
    jd_ut: float,
    latitude: float,
    longitude: float,
    ayanamsa: float,
) -> tuple[list[HouseCusp], dict]:
    """Compute Placidus house cusps and return cusp list + asc/mc info."""
    cusps, ascmc = swe.houses(jd_ut, latitude, longitude, b"P")

    # cusps is a 13-float tuple (cusp 1-12 + extra)
    # ascmc is 8 floats: ascendant, MC, etc.
    asc = ascmc[0]
    mc = ascmc[1]

    house_cusps: list[HouseCusp] = []
    for i in range(12):
        cusp_lon_sidereal = (cusps[i] - ayanamsa) % 360
        sign_name, sign_degree = sign_from_longitude(cusp_lon_sidereal)
        _, _, star_lord = nakshatra_from_longitude(cusp_lon_sidereal)
        sub_lord, sub_sub_lord = sub_lord_from_longitude(cusp_lon_sidereal, star_lord)

        house_cusps.append(HouseCusp(
            house=i + 1,
            longitude=cusp_lon_sidereal,
            sign=sign_name,
            sign_degree=sign_degree,
            sub_lord=sub_lord,
            sub_sub_lord=sub_sub_lord,
        ))

    return house_cusps, {"ascendant": asc, "mc": mc, "ascendant_sidereal": (asc - ayanamsa) % 360}


def assign_planets_to_houses(
    positions: dict[str, PlanetPosition],
    house_cusps: list[HouseCusp],
) -> dict[str, PlanetPosition]:
    """Assign each planet to a house by cusp-degree comparison (KP method).

    A planet is in house N if its longitude >= cusp N longitude and < cusp N+1 longitude.
    Handles wraparound at 360/0.
    """
    for name, pos in positions.items():
        lon = pos.sidereal_longitude
        assigned_house = 12  # default

        for i, cusp in enumerate(house_cusps):
            next_cusp = house_cusps[(i + 1) % 12]
            cusp_lon = cusp.longitude
            next_lon = next_cusp.longitude

            if cusp_lon <= next_lon:
                # Normal case: no wraparound
                if cusp_lon <= lon < next_lon:
                    assigned_house = cusp.house
                    break
            else:
                # Wraparound case: e.g., cusp at 350, next at 10
                if lon >= cusp_lon or lon < next_lon:
                    assigned_house = cusp.house
                    break

        pos.house = assigned_house

    return positions


# ---------------------------------------------------------------------------
# Significators (KP ABCD method)
# ---------------------------------------------------------------------------

@dataclass
class Significator:
    planet: str
    house_of_position: int
    house_of_sign_lord: int
    star_lord_house: int
    star_lord_sign_lord_house: int
    sub_lord_house: int
    sub_lord_sign_lord_house: int
    sub_sub_lord_house: int
    all_signified_houses: set[int] = field(default_factory=set)


def compute_significators(
    positions: dict[str, PlanetPosition],
    house_cusps: list[HouseCusp],
) -> dict[str, Significator]:
    """Compute KP significators (ABCD) for each planet.

    A planet signifies:
    A: House where it is posited (cusp-based)
    B: House(s) owned by its sign lord
    C: House(s) where its star lord is posited + houses owned by star lord's sign
    D: House(s) where its sub lord is posited + houses owned by sub lord's sign
    """
    # Map: house -> list of planets in that house
    house_occupants: dict[int, list[str]] = {i: [] for i in range(1, 13)}
    for name, pos in positions.items():
        house_occupants[pos.house].append(name)

    # Map: planet -> house where that planet is posited
    planet_house: dict[str, int] = {name: pos.house for name, pos in positions.items()}

    significators: dict[str, Significator] = {}

    for name, pos in positions.items():
        # A: House of position
        house_of_position = pos.house

        # B: House(s) owned by sign lord
        sign_lord = SIGN_LORDS.get(pos.sign, "Mars")
        # Find houses where sign_lord is the cusp sign lord
        house_of_sign_lord = _houses_owned_by(sign_lord, house_cusps)

        # C: Star lord houses
        star_lord_name = pos.star_lord
        star_lord_house = planet_house.get(star_lord_name, 1)
        star_lord_sign = positions[star_lord_name].sign if star_lord_name in positions else pos.sign
        star_lord_sign_lord = SIGN_LORDS.get(star_lord_sign, "Mars")
        star_lord_sign_lord_house = _houses_owned_by(star_lord_sign_lord, house_cusps)

        # D: Sub lord houses
        sub_lord_name = pos.sub_lord
        sub_lord_house = planet_house.get(sub_lord_name, 1)
        sub_lord_sign = positions[sub_lord_name].sign if sub_lord_name in positions else pos.sign
        sub_lord_sign_lord = SIGN_LORDS.get(sub_lord_sign, "Mars")
        sub_lord_sign_lord_house = _houses_owned_by(sub_lord_sign_lord, house_cusps)

        # Sub-sub lord
        sub_sub_lord_name = pos.sub_sub_lord
        sub_sub_lord_house = planet_house.get(sub_sub_lord_name, 1)

        # Collect all signified houses
        all_houses: set[int] = set()
        all_houses.add(house_of_position)
        all_houses.update(house_of_sign_lord)
        all_houses.add(star_lord_house)
        all_houses.update(star_lord_sign_lord_house)
        all_houses.add(sub_lord_house)
        all_houses.update(sub_lord_sign_lord_house)
        all_houses.add(sub_sub_lord_house)

        significators[name] = Significator(
            planet=name,
            house_of_position=house_of_position,
            house_of_sign_lord=house_of_sign_lord[0] if house_of_sign_lord else 1,
            star_lord_house=star_lord_house,
            star_lord_sign_lord_house=star_lord_sign_lord_house[0] if star_lord_sign_lord_house else 1,
            sub_lord_house=sub_lord_house,
            sub_lord_sign_lord_house=sub_lord_sign_lord_house[0] if sub_lord_sign_lord_house else 1,
            sub_sub_lord_house=sub_sub_lord_house,
            all_signified_houses=all_houses,
        )

    return significators


def _houses_owned_by(planet: str, house_cusps: list[HouseCusp]) -> list[int]:
    """Find houses whose cusp sign is ruled by the given planet."""
    owned = []
    for cusp in house_cusps:
        sign_lord = SIGN_LORDS.get(cusp.sign, "Mars")
        if sign_lord == planet:
            owned.append(cusp.house)
    return owned


# ---------------------------------------------------------------------------
# Main chart computation
# ---------------------------------------------------------------------------

@dataclass
class ChartOutput:
    subject_id: str
    birth_datetime_utc: str
    julian_day: float
    ayanamsa: float
    ayanamsa_mode: str
    planets: dict[str, dict]
    houses: list[dict]
    angles: dict
    significators: dict[str, dict]
    house_cusps: list[dict]


def compute_chart(
    subject_id: str,
    year: int,
    month: int,
    day: int,
    hour: int,
    minute: int,
    second: int,
    latitude: float,
    longitude: float,
    timezone_name: str,
    ayanamsa_mode: str = "KP",
) -> ChartOutput:
    """Compute a complete KP chart for the given birth data.

    Returns a ChartOutput with all planetary positions, house cusps,
    and KP significators.
    """
    # 1. Convert local time to UTC
    dt_utc = local_to_utc(year, month, day, hour, minute, second, timezone_name)
    jd_ut = julday_from_utc(dt_utc)

    # 2. Set ayanamsa
    set_ayanamsa(ayanamsa_mode)
    ayanamsa_val = get_ayanamsa(jd_ut)

    # 3. Compute planet positions
    positions = compute_planet_positions(jd_ut, ayanamsa_val)

    # 4. Compute houses (Placidus)
    house_cusps, angles = compute_houses(jd_ut, latitude, longitude, ayanamsa_val)

    # 5. Assign planets to houses
    positions = assign_planets_to_houses(positions, house_cusps)

    # 6. Compute significators
    significators = compute_significators(positions, house_cusps)

    # Build output dicts
    planets_dict: dict[str, dict] = {}
    for name, pos in positions.items():
        planets_dict[name] = {
            "name": pos.name,
            "tropical_longitude": round(pos.tropical_longitude, 4),
            "sidereal_longitude": round(pos.sidereal_longitude, 4),
            "sign": pos.sign,
            "sign_degree": round(pos.sign_degree, 4),
            "nakshatra": pos.nakshatra,
            "nakshatra_pada": pos.nakshatra_pada,
            "star_lord": pos.star_lord,
            "sub_lord": pos.sub_lord,
            "sub_sub_lord": pos.sub_sub_lord,
            "house": pos.house,
            "speed": round(pos.speed, 4),
            "is_retrograde": pos.is_retrograde,
        }

    houses_dict: list[dict] = []
    for cusp in house_cusps:
        houses_dict.append({
            "house": cusp.house,
            "longitude": round(cusp.longitude, 4),
            "sign": cusp.sign,
            "sign_degree": round(cusp.sign_degree, 4),
            "sub_lord": cusp.sub_lord,
            "sub_sub_lord": cusp.sub_sub_lord,
        })

    sig_dict: dict[str, dict] = {}
    for name, sig in significators.items():
        sig_dict[name] = {
            "planet": sig.planet,
            "house_of_position": sig.house_of_position,
            "house_of_sign_lord": sig.house_of_sign_lord,
            "star_lord_house": sig.star_lord_house,
            "star_lord_sign_lord_house": sig.star_lord_sign_lord_house,
            "sub_lord_house": sig.sub_lord_house,
            "sub_lord_sign_lord_house": sig.sub_lord_sign_lord_house,
            "sub_sub_lord_house": sig.sub_sub_lord_house,
            "all_signified_houses": sorted(sig.all_signified_houses),
        }

    return ChartOutput(
        subject_id=subject_id,
        birth_datetime_utc=dt_utc.isoformat(),
        julian_day=jd_ut,
        ayanamsa=round(ayanamsa_val, 4),
        ayanamsa_mode=ayanamsa_mode,
        planets=planets_dict,
        houses=houses_dict,
        angles={
            "ascendant": round(angles["ascendant"], 4),
            "mc": round(angles["mc"], 4),
            "ascendant_sidereal": round(angles["ascendant_sidereal"], 4),
        },
        significators=sig_dict,
        house_cusps=houses_dict,
    )


def chart_to_json(chart: ChartOutput) -> str:
    """Serialize chart to JSON string."""
    return json.dumps({
        "subject_id": chart.subject_id,
        "birth_datetime_utc": chart.birth_datetime_utc,
        "julian_day": chart.julian_day,
        "ayanamsa": chart.ayanamsa,
        "ayanamsa_mode": chart.ayanamsa_mode,
        "planets": chart.planets,
        "houses": chart.houses,
        "angles": chart.angles,
        "significators": chart.significators,
        "house_cusps": chart.house_cusps,
    }, indent=2)


if __name__ == "__main__":
    # Example: Mumbai, India
    chart = compute_chart(
        subject_id="P001",
        year=1990, month=5, day=15, hour=14, minute=30, second=0,
        latitude=19.0760, longitude=72.8777,
        timezone_name="Asia/Kolkata",
        ayanamsa_mode="KP",
    )
    print(chart_to_json(chart))
