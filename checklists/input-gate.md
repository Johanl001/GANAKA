# Input Gate — Birth Data Validation

Run this checklist before any chart calculation or reading. If any item fails, stop and ask the user. Do not guess.

- [ ] Birth date is provided (YYYY-MM-DD)
- [ ] Birth time is provided (HH:MM, 24-hour format)
- [ ] Birth place is provided (city, country)
- [ ] Birth time source is identified (certificate, hospital record, family memory, other)
- [ ] If birth time is unverified (family memory or other), mark as unverified and note it in the reading
- [ ] Latitude and longitude are resolved for the birth place
- [ ] Time zone is determined for the birth date and place (including historical DST/clock offsets)
- [ ] Event type is identified (marriage, job and career, higher education, foreign travel or settlement, children)
- [ ] User consents to data logging and scoring

**If unverified birth time:** Say so at the top of the reading and lower every confidence value.
