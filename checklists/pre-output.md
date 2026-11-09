# Pre-Output Checklist

Run this checklist before emitting any reading. If any item fails, fix it before output.

- [ ] Every claim cites a rule ID from a rule table. No rule ID, no claim.
- [ ] Every prediction has a window, a probability, a base rate, and a miss condition.
- [ ] No death dates, diagnoses, medical advice, or buy/sell/invest instructions.
- [ ] No Barnum statements (statements that would fit almost anyone).
- [ ] Evidence tier is stated on each claim (default: tier C).
- [ ] Reading states plainly that it is tradition-based and not scientifically validated.
- [ ] Same chart would produce the same verdicts every time (deterministic).
- [ ] Rules are not merged from different texts. Each rule keeps its own system, text, and edition.
- [ ] Conflicts between texts are reported, not silently resolved.
- [ ] Combined result is logged as a separate system (COMBINED), not used to raise confidence.
- [ ] Palm reading interprets only fields present in the palm JSON; low-confidence fields are skipped.
- [ ] Disclaimer is present at the top of the reading.
