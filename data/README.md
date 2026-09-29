# Sample dataset

`sample_leads.csv` - 51 rows of small, mostly family-run US HVAC and plumbing
businesses across 7 metros (Austin, Denver, Ohio, Phoenix, Twin Cities, Tampa,
Charlotte). It's the kind of niche list a searcher would pull when hunting for
an owner-operated business to buy, which is what the Acquisition-fit mode is for.

## Where it came from

- Company names and websites were collected by hand from public web search
  results (the businesses' own sites and public directories) in September 2026.
- Only business-level fields are included: name, website, industry, city,
  state, country. No personal data - owner names, emails and phones are left
  for LeadLens to find on the company's own public website.
- Fields we couldn't confirm (headcount, revenue, some cities) are blank on
  purpose rather than guessed.
- 3 rows are deliberate duplicates (same company, different URL format /
  casing) so the dedup step has something to do.

## Results from a real run

Imported locally with the default Sales ICP:

| | |
|---|---|
| Rows in file | 51 |
| Duplicates removed | 3 |
| Companies crawled | 48 in ~40 s (10 concurrent, 2 per host) |
| Sites alive / blocked us / timed out | 39 / 7 / 2 |
| Founding year found on site | 29 of 48 (1904 - 2006) |

The 7 "blocked" sites disallow crawlers in robots.txt or sit behind a bot
wall - LeadLens marks them and moves on instead of trying to get around it.

## Regenerating

```bash
docker compose up -d
cd backend && uv run python -m scripts.seed_demo   # imports this file
```

Numbers will drift a little between runs - websites change.
