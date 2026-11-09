---
name: jyotish-reading
description: Produces structured, falsifiable astrological readings from verified birth data using script-computed charts and multiple rule systems (KP, Parashari/BPHS, Phaladeepika). Logs every prediction per system with a prediction ledger, scores outcomes against real events, and supports retrodiction and prospective testing. Use when the user asks for a Vedic, KP, or Parashari astrology reading, an event-timing question, or a prediction-log entry.
---

# Jyotish Reading Skill

## Before anything else

1. Require birth date, time, and place. Ask where the birth time comes from (certificate, hospital record, family memory). If unverified, say so at the top of the reading and lower every confidence value.
2. Run `scripts/chart.py` for each active system. Never estimate planetary positions or house cusps from memory.
3. If any input is missing, stop and ask. Do not guess.

## Workflow

1. Read `references/routing.md` to see which system is primary for this question. Run every active system anyway.
2. Load each system's chart output. KP: KP ayanamsa, Placidus cusps, sign, star and sub-lords, significators. Parashari: Lahiri ayanamsa, whole-sign houses, divisional charts. Both: Vimshottari dasha table.
3. Identify the event (marriage, job and career, higher education, foreign travel or settlement, children). Find its rules in that system's rule table (`references/kp/rule-table.csv`, `references/bphs/rule-table.csv`, `references/phaladeepika/rule-table.csv`).
4. KP: the sub-lord of the relevant cusp must signify the event houses. State promised, denied, or uncertain, with the rule ID. BPHS and Phaladeepika: apply that text's rules for the event houses, lords, and yogas. Name the text and edition.
5. Timing, only if that system's rules support the event: find dasha, bhukti, and antara periods that fit, then check transit support. Give a window, never a single date.
6. Write one prediction record per system (`schemas/prediction.schema.json`) and run `scripts/log_prediction.py`.
7. Combined result: apply the fixed combination rule in `references/synthesis.md`. Log it as system COMBINED with a combined_from list. If the windows do not overlap, say the systems disagree and give no combined prediction.
8. Write the reading with `templates/reading.md`. Show each system's verdict separately before any combined result.

## Hard rules

- Every claim cites a rule ID from a rule table. No rule ID, no claim.
- Every prediction has a window, a probability, a base rate, and a miss condition.
- Banned: death dates, diagnoses or medical advice, instructions to buy/sell/invest, fear-based remedies.
- No statement that would fit almost anyone (Barnum statements).
- State the evidence tier on each claim. Default is tier C.
- Every reading says plainly that it is tradition-based and not scientifically validated.
- The same chart must give the same verdicts every time. Do not vary them.
- Never merge rules from different texts into one rule. Each rule keeps its own system, text, and edition. Report conflicts between texts instead of resolving them silently.
- Do not combine systems to raise confidence. A combined result is a separate, scored entry.
- Palm: interpret only fields present in the palm JSON, and skip fields marked low confidence.

## Calculation settings

- KP layer: sidereal zodiac with KP ayanamsa, Placidus house cusps, Vimshottari dasha, KP sub-lord table (249 subdivisions).
- Parashari layer: Lahiri ayanamsa, whole-sign houses, Vimshottari dasha, divisional charts.
- Library: Swiss Ephemeris through pysweph (commercial license for SaaS use).
- Test code against fixtures in `tests/fixtures/` before trusting any reading.

## Event house groups (starter)

| Event | Houses |
|-------|--------|
| Marriage | 2, 7, 11 |
| Job and career | 2, 6, 10, 11 |
| Higher education | 4, 9, 11 |
| Foreign travel or settlement | 3, 9, 12 |
| Children | 2, 5, 11 |

## Prediction record schema

See `schemas/prediction.schema.json`. Every record: prediction_id, subject_id, made_on, system, text_and_edition, combined_from, event_type, rule_ids, source, evidence_tier, verdict, window, window_length_days, dasha_basis, probability, base_rate, miss_condition, outcome, scored_on.

Outcome and scored_on stay empty until the window closes. A committed record is never edited. A correction is a new record. Git history is the proof that predictions came before events.
