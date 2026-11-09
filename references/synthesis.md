# Synthesis — Combination Rule

## Fixed combination rule (pre-registered before testing)

The combined window is the **overlap** of the individual windows from each active system.

- If windows overlap: combined prediction is given, logged as system COMBINED with a combined_from list of prediction IDs.
- If windows do not overlap: systems disagree, no combined prediction is given.

## Combined result scoring

A combined prediction is logged as its own system entry (COMBINED). It is scored separately against the best single system on the same events. Window length is scored next to hit rate, because wider windows are easier to hit.

## Multiple-comparison correction

Three or four systems across five event types make many comparisons. Apply a multiple-comparison correction and pre-register routing hypotheses (OSF.io).

## References

- routing.md: assignment of systems to jobs
- rule-table.csv per system: individual rule conditions
