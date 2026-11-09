# GANAKA — Jyotish Reading Skill

A structured, falsifiable Vedic astrology skill for LLMs that produces KP (Krishnamurti Paddhati), Parashari (BPHS), and Phaladeepika readings, logs every prediction to a ledger, and scores outcomes against real events.

## Project Status

| Phase | Status |
|-------|--------|
| Phase 0 — Foundation | ✅ Complete |
| Phase 1 — KP Calculation Engine | ✅ Complete |
| Phase 2 — FastAPI Backend | ✅ Complete |
| Phase 3 — Next.js Frontend | ✅ Complete |
| Phase 4 — Rule Tables | ⬜ In progress |
| Phase 5 — SKILL.md Integration | ⬜ Pending |
| Phase 6 — Parashari + Phaladeepika | ⬜ Pending |
| Phase 7 — Pilot & Launch | ⬜ Pending |

## Repository Structure

```
jyotish-skill/
  SKILL.md              # Claude Code skill file
  README.md             # This file
  schemas/
    prediction.schema.json
    palm.schema.json
  templates/
    reading.md
  checklists/
    input-gate.md
    pre-output.md
  references/
    kp/                 # KP rule tables, house groups
    bphs/               # BPHS rule tables (to fill)
    phaladeepika/       # Phaladeepika rule tables (to fill)
    routing.md          # System assignment by job
    synthesis.md        # Combination rule
    sources.md          # Verified source list
  scripts/
    chart.py            # Swiss Ephemeris chart calculation
    dasha.py            # Vimshottari dasha engine
    log_prediction.py   # Prediction ledger (CSV)
  backend/
    main.py             # FastAPI app
    database.py         # SQLite connection
    models.py           # SQLAlchemy models
    routers/            # charts, predictions, readings
  frontend/             # Next.js 14 App Router
    app/                # pages, layout, globals
```

## Tech Stack

- **Calculation:** pysweph (Swiss Ephemeris fork) + zoneinfo + timezonefinder
- **Backend:** FastAPI + SQLAlchemy + SQLite
- **Frontend:** Next.js 14 App Router + Tailwind CSS + Framer Motion
- **Payments:** Stripe (global, multi-currency)
- **License:** Commercial Swiss Ephemeris license (closed-source SaaS)

## Verified Sources

Astrology texts from `ayushman1024/ASTROLOGY-BOOKS-DATABASE`:

| System | Source File | Repo Path |
|--------|-------------|-----------|
| KP Reader 2 | K.P reader-2-fundamental-principles-of-astro.pdf | Nadi jyotish/ |
| KP Reader 3 | K.P reader-3 Predictive-stellar-astro.pdf | #Articles/ |
| KP System | Astrology-KP-System.pdf | #Articles/ |
| KP Significators | Sign lord,star lord,sub lord,sub sub lord.......pdf | #Articles/ |
| BPHS | BPHS 1.HTM, BPHS-Santhanam-Vol-1/2.pdf | Classics books/ |
| Phaladeepika | Mantreswara_Phaladeeplka.pdf | Classics books/ |
| Vimshottari Dasha | vimsottari-and-udu-dasas.pdf | Good books/ |

**License warning:** No explicit license on the source repo. Rules must be paraphrased with citations — do NOT distribute the PDFs.

## Event House Groups (KP Starter)

| Event | Houses |
|-------|--------|
| Marriage | 2, 7, 11 |
| Job/Career | 2, 6, 10, 11 |
| Higher Education | 4, 9, 11 |
| Foreign Travel/Settlement | 3, 9, 12 |
| Children | 2, 5, 11 |

## Getting Started

### Backend (FastAPI)

```bash
cd jyotish-skill/backend
pip install fastapi uvicorn sqlalchemy pysweph
uvicorn main:app --reload
```

### Frontend (Next.js)

```bash
cd jyotish-skill/frontend
npm install
npm run dev
```

### Running the Skill

Copy `SKILL.md` to `~/.claude/skills/jyotish-reading/SKILL.md` and invoke in Claude Code.

## License

Proprietary — Commercial Swiss Ephemeris license required for SaaS use.
