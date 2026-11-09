# Jyotish Reading — {{subject_id}}

**Date:** {{reading_date}}  
**System(s):** {{systems}}  
**Evidence Tier:** {{evidence_tier}} (default C)

---

## Important Notice

This reading is **tradition-based and not scientifically validated**. It is provided for informational and entertainment purposes only. It is not a substitute for professional medical, legal, or financial advice. No specific future outcome is guaranteed.

---

## Birth Data

- **Date:** {{birth_date}}
- **Time:** {{birth_time}} ({{time_source}})
- **Place:** {{birth_place}} ({{latitude}}, {{longitude}})
- **Time zone:** {{timezone}}
- **Birth time verification:** {{birth_time_verified}}

{{#if birth_time_unverified}}
> **Note:** Birth time is unverified. All confidence values are lowered accordingly.
{{/if}}

---

## Chart Settings

- **KP layer:** KP ayanamsa, Placidus house cusps, Vimshottari dasha
- **Parashari layer:** Lahiri ayanamsa, whole-sign houses, Vimshottari dasha
- **Ayanamsa (KP):** {{kp_ayanamsa}}°
- **Ayanamsa (Parashari):** {{lahiri_ayanamsa}}°

---

## Predictions by System

{{#each systems}}
### {{this.name}} ({{this.system}})

**Event:** {{this.event_type}}  
**Verdict:** {{this.verdict}}  
**Rule IDs:** {{this.rule_ids}}  
**Source:** {{this.source}} ({{this.text_and_edition}})

**Window:** {{this.window.start}} to {{this.window.end}} ({{this.window_length_days}} days)  
**Dasha basis:** {{this.dasha_basis}}  
**Probability:** {{this.probability}}  
**Base rate:** {{this.base_rate}}  
**Miss condition:** {{this.miss_condition}}

{{this.verdict_explanation}}

{{/each}}

---

## Combined Result

{{#if combined_available}}
**Combined verdict:** {{combined.verdict}}  
**Combined window:** {{combined.window.start}} to {{combined.window.end}}  
**Systems combined:** {{combined.combined_from}}  
**Combination rule:** Overlap of individual windows
{{else}}
**Combined result:** The active systems do not overlap. No combined prediction is given. The systems disagree.
{{/if}}

---

## Scoring

This prediction has been logged to the prediction ledger. Outcome and scored_on will be filled when the window closes.

- **Prediction ID(s):** {{prediction_ids}}
- **Ledger:** evals/ledger.csv

---

**End of reading**
