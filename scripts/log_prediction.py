"""
Prediction Ledger

Writes prediction records to evals/ledger.csv following schemas/prediction.schema.json.
Committed records are never edited; corrections are new records.
"""

from __future__ import annotations

import csv
import json
import os
from datetime import date, datetime
from pathlib import Path
from typing import Optional

LEDGER_PATH = Path(__file__).resolve().parent.parent / "evals" / "ledger.csv"

FIELDNAMES = [
    "prediction_id", "subject_id", "made_on", "system", "text_and_edition",
    "combined_from", "event_type", "rule_ids", "source", "evidence_tier",
    "verdict", "window_start", "window_end", "window_length_days",
    "dasha_basis", "probability", "base_rate", "miss_condition",
    "outcome", "scored_on",
]


def _ensure_ledger() -> None:
    """Create the ledger file with headers if it doesn't exist."""
    LEDGER_PATH.parent.mkdir(parents=True, exist_ok=True)
    if not LEDGER_PATH.exists():
        with open(LEDGER_PATH, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
            writer.writeheader()


def next_prediction_id() -> str:
    """Generate the next prediction ID (PR-0001, PR-0002, ...)."""
    _ensure_ledger()
    existing_ids = []
    if LEDGER_PATH.exists():
        with open(LEDGER_PATH, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                pid = row.get("prediction_id", "")
                if pid.startswith("PR-"):
                    try:
                        existing_ids.append(int(pid[3:]))
                    except ValueError:
                        pass
    next_num = max(existing_ids, default=0) + 1
    return f"PR-{next_num:04d}"


def log_prediction(
    subject_id: str,
    system: str,
    event_type: str,
    rule_ids: list[str],
    verdict: str,
    window_start: date,
    window_end: date,
    probability: float,
    base_rate: float,
    miss_condition: str,
    made_on: Optional[date] = None,
    text_and_edition: str = "",
    combined_from: Optional[list[str]] = None,
    source: str = "",
    evidence_tier: str = "C",
    dasha_basis: str = "",
    outcome: Optional[str] = None,
    scored_on: Optional[date] = None,
) -> str:
    """Write a prediction record to the ledger. Returns the prediction_id."""
    _ensure_ledger()
    prediction_id = next_prediction_id()
    made_on = made_on or date.today()
    window_length_days = (window_end - window_start).days

    row = {
        "prediction_id": prediction_id,
        "subject_id": subject_id,
        "made_on": made_on.isoformat(),
        "system": system,
        "text_and_edition": text_and_edition,
        "combined_from": ",".join(combined_from) if combined_from else "",
        "event_type": event_type,
        "rule_ids": ",".join(rule_ids),
        "source": source,
        "evidence_tier": evidence_tier,
        "verdict": verdict,
        "window_start": window_start.isoformat(),
        "window_end": window_end.isoformat(),
        "window_length_days": window_length_days,
        "dasha_basis": dasha_basis,
        "probability": probability,
        "base_rate": base_rate,
        "miss_condition": miss_condition,
        "outcome": outcome if outcome else "",
        "scored_on": scored_on.isoformat() if scored_on else "",
    }

    with open(LEDGER_PATH, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writerow(row)

    return prediction_id


def score_prediction(prediction_id: str, outcome: str, scored_on: Optional[date] = None) -> bool:
    """Score an existing prediction. outcome must be 'hit' or 'miss'."""
    if outcome not in ("hit", "miss"):
        raise ValueError("outcome must be 'hit' or 'miss'")

    _ensure_ledger()
    scored_on = scored_on or date.today()

    rows = []
    found = False
    with open(LEDGER_PATH, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row["prediction_id"] == prediction_id:
                row["outcome"] = outcome
                row["scored_on"] = scored_on.isoformat()
                found = True
            rows.append(row)

    if not found:
        return False

    with open(LEDGER_PATH, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(rows)

    return True


def get_pending_predictions() -> list[dict]:
    """Return all predictions that haven't been scored yet."""
    _ensure_ledger()
    pending = []
    with open(LEDGER_PATH, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if not row.get("outcome"):
                pending.append(row)
    return pending


def get_ledger_stats() -> dict:
    """Return basic statistics from the ledger."""
    _ensure_ledger()
    total = 0
    scored = 0
    hits = 0
    misses = 0
    by_system: dict[str, int] = {}
    by_event: dict[str, int] = {}

    with open(LEDGER_PATH, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            total += 1
            system = row.get("system", "unknown")
            event = row.get("event_type", "unknown")
            by_system[system] = by_system.get(system, 0) + 1
            by_event[event] = by_event.get(event, 0) + 1

            if row.get("outcome"):
                scored += 1
                if row["outcome"] == "hit":
                    hits += 1
                elif row["outcome"] == "miss":
                    misses += 1

    hit_rate = hits / scored if scored > 0 else 0.0

    return {
        "total": total,
        "scored": scored,
        "hits": hits,
        "misses": misses,
        "hit_rate": round(hit_rate, 4),
        "by_system": by_system,
        "by_event": by_event,
    }


if __name__ == "__main__":
    # Example usage
    pid = log_prediction(
        subject_id="P001",
        system="KP",
        event_type="marriage",
        rule_ids=["KP-R01-cusp7-sublord-marriage"],
        verdict="promised",
        window_start=date(2027, 3, 1),
        window_end=date(2027, 9, 30),
        probability=0.75,
        base_rate=0.5,
        miss_condition="No marriage ceremony held within the window",
        text_and_edition="KP Reader, 2nd edition",
        dasha_basis="Venus-Rahu",
    )
    print(f"Logged prediction: {pid}")
    print(f"Ledger stats: {get_ledger_stats()}")
