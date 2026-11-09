"""
Vimshottari Dasha Calculation Engine

Computes Mahadasha, Bhukti, Antara, and Pratyantara periods from Moon's
nakshatra at birth.

Dasha lord order (9): Ketu, Venus, Sun, Moon, Mars, Rahu, Jupiter, Saturn, Mercury
Full years (total 120): Ketu 7, Venus 20, Sun 6, Moon 10, Mars 7, Rahu 18,
Jupiter 16, Saturn 19, Mercury 17

Usage:
    from dasha import compute_vimshottari_dasha
    dasha = compute_vimshottari_dasha(moon_longitude_sidereal, birth_julian_day)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Optional

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

DHASA_LORDS = ["Ketu", "Venus", "Sun", "Moon", "Mars", "Rahu", "Jupiter", "Saturn", "Mercury"]

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

TOTAL_YEARS = 120  # Sum of all dasha years
NAKSHATRA_SPAN_DEG = 360 / 27  # 13°20' per nakshatra


# ---------------------------------------------------------------------------
# Data models
# ---------------------------------------------------------------------------


@dataclass
class DashaPeriod:
    lord: str
    start_date: datetime
    end_date: datetime
    years: float
    days: int


@dataclass
class DashaLevel:
    mahadasha: DashaPeriod
    bhukti: list[DashaPeriod] = field(default_factory=list)


@dataclass
class VimshottariDasha:
    moon_longitude: float
    nakshatra_index: int
    nakshatra_lord: str
    balance_at_birth_years: float
    balance_at_birth_days: int
    start_lord: str
    levels: list[DashaLevel] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Core calculations
# ---------------------------------------------------------------------------


def nakshatra_from_moon_longitude(moon_lon_sidereal: float) -> tuple[int, str, float, float]:
    """Return (nakshatra_index, nakshatra_lord, nakshatra_start_deg, position_within_nakshatra).

    moon_lon_sidereal: Moon's sidereal longitude in degrees (0-360)
    """
    lon = moon_lon_sidereal % 360
    nak_index = int(lon // NAKSHATRA_SPAN_DEG)  # 0-26
    nak_start = nak_index * NAKSHATRA_SPAN_DEG
    pos_within = lon - nak_start
    lord = DHASA_LORDS[nak_index % 9]  # Nakshatra lords repeat every 9
    return nak_index, lord, nak_start, pos_within


def compute_balance_at_birth(
    moon_lon_sidereal: float,
) -> tuple[str, float, int, float, float]:
    """Compute the dasha balance at birth.

    Returns:
        start_lord: The mahadasha lord running at birth
        balance_years: Years of the starting dasha already elapsed
        balance_days: Days of the starting dasha already elapsed (integer)
        remaining_years: Years remaining in the starting dasha at birth
        percent_elapsed: Percent of the starting dasha already completed (0-1)
    """
    nak_index, nak_lord, nak_start, pos_within = nakshatra_from_moon_longitude(moon_lon_sidereal)

    # The nakshatra lord starts the mahadasha
    start_lord = nak_lord
    start_lord_years = DHASA_YEARS[start_lord]

    # Percent of nakshatra elapsed = percent of dasha elapsed
    percent_elapsed = pos_within / NAKSHATRA_SPAN_DEG

    # Balance already served
    balance_years = percent_elapsed * start_lord_years
    balance_days = int(balance_years * 365.25)

    # Remaining at birth (this is what runs first)
    remaining_years = start_lord_years - balance_years

    return start_lord, balance_years, balance_days, remaining_years, percent_elapsed


def _lord_after(lord: str) -> str:
    """Return the next lord in Vimshottari order."""
    idx = DHASA_LORDS.index(lord)
    return DHASA_LORDS[(idx + 1) % 9]


def _lords_sequence(start_lord: str, count: int = 9) -> list[str]:
    """Return a sequence of lords starting from start_lord in Vimshottari order."""
    seq = []
    idx = DHASA_LORDS.index(start_lord)
    for i in range(count):
        seq.append(DHASA_LORDS[(idx + i) % 9])
    return seq


def compute_bhukti_periods(
    mahadasha_lord: str,
    mahadasha_years: float,
    start_date: datetime,
) -> list[DashaPeriod]:
    """Compute bhukti (sub-period) periods within a mahadasha.

    Bhukti years = (bhukti lord's full years / 120) * mahadasha years.
    """
    periods = []
    current = start_date

    for lord in _lords_sequence(mahadasha_lord):
        bhukti_years = (DHASA_YEARS[lord] / 120) * mahadasha_years
        bhukti_days = int(bhukti_years * 365.25)
        end_date = current + timedelta(days=bhukti_days)

        periods.append(DashaPeriod(
            lord=lord,
            start_date=current,
            end_date=end_date,
            years=bhukti_years,
            days=bhukti_days,
        ))
        current = end_date

    return periods


def compute_antara_periods(
    bhukti_lord: str,
    bhukti_years: float,
    start_date: datetime,
) -> list[DashaPeriod]:
    """Compute antara (sub-sub) periods within a bhukti."""
    periods = []
    current = start_date

    for lord in _lords_sequence(bhukti_lord):
        antara_years = (DHASA_YEARS[lord] / 120) * bhukti_years
        antara_days = int(antara_years * 365.25)
        end_date = current + timedelta(days=antara_days)

        periods.append(DashaPeriod(
            lord=lord,
            start_date=current,
            end_date=end_date,
            years=antara_years,
            days=antara_days,
        ))
        current = end_date

    return periods


# ---------------------------------------------------------------------------
# Main dasha computation
# ---------------------------------------------------------------------------


def compute_vimshottari_dasha(
    moon_lon_sidereal: float,
    birth_julian_day: float,
) -> VimshottariDasha:
    """Compute the full Vimshottari dasha structure from birth.

    Args:
        moon_lon_sidereal: Moon's sidereal longitude at birth (degrees, 0-360)
        birth_julian_day: Julian Day of birth (UT)

    Returns:
        VimshottariDasha with all levels computed for ~120 years from birth.
    """
    start_lord, balance_years, balance_days, remaining_years, percent_elapsed = \
        compute_balance_at_birth(moon_lon_sidereal)

    nak_index, nak_lord, nak_start, pos_within = nakshatra_from_moon_longitude(moon_lon_sidereal)

    # Birth date from Julian Day
    birth_greg = swe.revjul(birth_julian_day)
    birth_date = datetime(
        int(birth_greg[0]), int(birth_greg[1]), int(birth_greg[2]),
        int(birth_greg[3]), int((birth_greg[3] % 1) * 60), 0,
    )

    # The starting mahadasha runs for remaining_years from birth
    start_lord_years = DHASA_YEARS[start_lord]
    first_md_days = int(remaining_years * 365.25)
    first_md_end = birth_date + timedelta(days=first_md_days)

    vims = VimshottariDasha(
        moon_longitude=moon_lon_sidereal,
        nakshatra_index=nak_index,
        nakshatra_lord=nak_lord,
        balance_at_birth_years=balance_years,
        balance_at_birth_days=balance_days,
        start_lord=start_lord,
    )

    # Compute full 120-year cycle starting from the first partial mahadasha
    current_date = birth_date
    remaining_cycle_years = TOTAL_YEARS - balance_years

    # First, the partial starting mahadasha
    first_level = DashaLevel(
        mahadasha=DashaPeriod(
            lord=start_lord,
            start_date=birth_date,
            end_date=first_md_end,
            years=remaining_years,
            days=first_md_days,
        ),
        bhukti=compute_bhukti_periods(start_lord, remaining_years, birth_date),
    )
    vims.levels.append(first_level)

    current_date = first_md_end
    remaining_cycle_years -= remaining_years

    # Then full mahadashas for each lord in order, starting after start_lord
    lord_idx = DHASA_LORDS.index(start_lord)
    for i in range(9):
        lord = DHASA_LORDS[(lord_idx + 1 + i) % 9]
        if remaining_cycle_years <= 0:
            break

        lord_years = DHASA_YEARS[lord]
        if lord_years > remaining_cycle_years:
            lord_years = remaining_cycle_years

        lord_days = int(lord_years * 365.25)
        lord_end = current_date + timedelta(days=lord_days)

        level = DashaLevel(
            mahadasha=DashaPeriod(
                lord=lord,
                start_date=current_date,
                end_date=lord_end,
                years=lord_years,
                days=lord_days,
            ),
            bhukti=compute_bhukti_periods(lord, lord_years, current_date),
        )
        vims.levels.append(level)

        current_date = lord_end
        remaining_cycle_years -= lord_years

    return vims


def dasha_at_date(
    vims: VimshottariDasha,
    target_date: datetime,
) -> Optional[dict]:
    """Find the running dasha/bhukti/antara at a given date.

    Returns dict with mahadasha_lord, bhukti_lord, antara_lord, or None if
    date is outside the computed range.
    """
    for level in vims.levels:
        md = level.mahadasha
        if md.start_date <= target_date < md.end_date:
            result = {
                "mahadasha_lord": md.lord,
                "mahadasha_start": md.start_date,
                "mahadasha_end": md.end_date,
            }

            # Find bhukti
            for b in level.bhukti:
                if b.start_date <= target_date < b.end_date:
                    result["bhukti_lord"] = b.lord
                    result["bhukti_start"] = b.start_date
                    result["bhukti_end"] = b.end_date

                    # Find antara
                    antara_periods = compute_antara_periods(
                        b.lord,
                        b.years,
                        b.start_date,
                    )
                    for a in antara_periods:
                        if a.start_date <= target_date < a.end_date:
                            result["antara_lord"] = a.lord
                            result["antara_start"] = a.start_date
                            result["antara_end"] = a.end_date
                            break
                    break
            return result

    return None


def dasha_summary(vims: VimshottariDasha) -> list[dict]:
    """Return a summary of all mahadasha periods."""
    return [
        {
            "lord": level.mahadasha.lord,
            "start": level.mahadasha.start_date.isoformat(),
            "end": level.mahadasha.end_date.isoformat(),
            "years": round(level.mahadasha.years, 2),
            "bhukti_count": len(level.bhukti),
        }
        for level in vims.levels
    ]


if __name__ == "__main__":
    # Example: Moon at 100 degrees sidereal
    dasha = compute_vimshottari_dasha(moon_lon_sidereal=100.0, birth_julian_day=2447989.5)
    print(f"Start lord: {dasha.start_lord}")
    print(f"Balance at birth: {dasha.balance_at_birth_years:.2f} years ({dasha.balance_at_birth_days} days)")
    print(f"Nakshatra: {dasha.nakshatra_lord} (index {dasha.nakshatra_index})")
    print(f"\nMahadasha summary:")
    for s in dasha_summary(dasha)[:5]:
        print(f"  {s['lord']}: {s['start']} to {s['end']} ({s['years']} years)")
