# Scoring model

Every lead gets a 0-100 score and an A-D grade against the **active ICP profile**.
It's deliberately not an ML model: a rep (or a searcher) has to be able to see
exactly why a company is ranked where it is, and argue with it.

## How it works

1. Each rule looks at the company + its contacts and either returns a short
   reason ("Operating since 1998 (28 yrs)") or nothing.
2. The active **strategy** decides how many points that reason is worth.
3. Points are summed and clamped to 0-100. The breakdown is stored with the
   lead and shown in the "Why this score" panel.

Grades: **A ≥ 80 · B 60-79 · C 40-59 · D < 40**

## Two lenses on the same data

| Rule | Fires when | Sales | Acquisition |
|---|---|---:|---:|
| `industry_match` | industry is in the ICP list (loose match, "HVAC" ~ "HVAC Services") | +20 | +20 |
| `location_match` | country or state is in the ICP list | +10 | +10 |
| `size_fit` | employees inside the ICP range (acquisition defaults to 5-100) | +10 | +15 |
| `personal_email_valid` | a personal (not info@) email whose domain has MX records | +15 | +10 |
| `decision_maker` | an owner / founder / CEO / president was found | +10 | +15 |
| `valid_phone` | a phone that parses as a real number | +5 | +5 |
| `site_healthy` | site is up and serves HTTPS | +5 | +5 |
| `hiring` | careers page, "we're hiring", or a job-board link | **+10** | **-5** |
| `modern_stack` | HubSpot, Shopify, Intercom, Next.js… detected | +5 | 0 |
| `years_in_business` | founded ≥ 10 years ago (or the ICP's minimum) | 0 | +10 |
| `stale_website` | copyright year is 3+ years old | **-5** | **+5** |
| `family_owned` | "family-owned", "owner-operated", "second generation"… | 0 | +5 |
| `role_only_emails` | the only emails are generic inboxes | -5 | -5 |
| `site_dead` | site is dead or timed out | -20 | -20 |

The interesting rows are the ones where the sign flips:

- **Hiring** is a buying signal when you sell to a company (budget, growth), but
  when you want to *buy* one it usually means the owner is still building, not
  looking for an exit.
- **A stale website** makes a company a slightly worse sales lead, but for a
  searcher it's upside: an under-invested business is exactly where a new owner
  can create value after the deal.

## Tuning

An ICP profile can override any weight:

```json
{ "industries": ["HVAC"], "countries": ["US"], "weights": { "hiring": 25 } }
```

Unknown rule names are ignored, and the base strategies are never mutated.

## Example breakdown (acquisition lens)

```json
[
  {"rule": "industry_match",    "points": 20, "reason": "Industry 'HVAC' is in your ICP"},
  {"rule": "decision_maker",    "points": 15, "reason": "Found decision maker: John Smith (Owner)"},
  {"rule": "years_in_business", "points": 10, "reason": "Operating since 1963 (63 yrs)"},
  {"rule": "location_match",    "points": 10, "reason": "Located in US"},
  {"rule": "family_owned",      "points": 5,  "reason": "Says it's 'family-owned'"},
  {"rule": "hiring",            "points": -5, "reason": "Hiring right now (careers page)"}
]
```

Code: `backend/app/services/scoring/` - `rules.py` (the checks), `strategies.py`
(the weights), `engine.py` (adds it up).
