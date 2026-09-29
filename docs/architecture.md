# Architecture

```
┌──────────────────────────────┐
│  Next.js 16 (App Router)     │  Vercel - static shell + client data fetching
│  shadcn/ui · TanStack Query  │
└──────────────┬───────────────┘
               │ REST / JSON  (/api/v1)
┌──────────────▼───────────────┐
│  FastAPI                     │  Cloud Run - one container
│  routers → services → repos  │
│  BackgroundTasks for jobs    │
└──┬───────────┬───────────┬───┘
   │           │           │
┌──▼────────┐ ┌▼────────┐ ┌▼─────────────────────────┐
│ Postgres  │ │ Redis   │ │ outside world            │
│ (Neon)    │ │(Upstash)│ │ · company websites       │
│ companies │ │ caches  │ │ · DNS (MX lookups)       │
│ contacts  │ │         │ │                          │
│ jobs, ICP │ │         │ │                          │
└───────────┘ └─────────┘ └──────────────────────────┘
```

## The pipeline

```
CSV / domains
  → parse (column auto-mapping, 5 MB / 5k rows)
  → normalise (canonical domain via the public suffix list, company-name cleanup)
  → dedupe (exact on domain, fuzzy on name + city, merge contacts)
  → save + queue a job                                   ← request returns here
  → per company, 10 at a time:
       enrich   fetch home → find about/contact/team/careers → run extractors
       validate email syntax + MX, phone → E.164, website health
       score    active ICP strategy → score, grade, breakdown
  → UI polls the job and shows progress
```

## Decisions (short ADRs)

**FastAPI + Next.js instead of one framework.** Python has the best tooling for
the hard part (fetching, parsing, DNS, phone numbers); Next.js + shadcn gets a
polished UI quickly. The API contract is plain REST so either side can be
swapped.

**PostgreSQL.** The data is relational (company → contacts → score breakdown)
with some genuinely flexible bits (tech stack, socials, signals), which is
exactly what JSONB is for. Full-text search on name + description uses a GIN
index, so no separate search service is needed.

**Redis for caching, not as a database.** Three caches, all optional - if Redis
is down, requests still work, they're just slower:

| Key | TTL | Why |
|---|---|---|
| `enrich:{domain}` | 7 days | re-importing a list doesn't re-crawl anything (1 ms vs 3-4 s per site) |
| `mx:{domain}` | 24 h | hundreds of leads on gmail.com = one DNS lookup |
| `robots:{host}` | 24 h | don't fetch robots.txt for every page |
| `stats:v1` | 30 s | dashboard query runs at most twice a minute |

**selectolax over BeautifulSoup.** It's a thin wrapper over a C parser
(lexbor), much faster than BeautifulSoup on real pages - and once pages are
cached, parsing is where the time goes.

**BackgroundTasks now, a queue later.** For a demo-sized workload an in-process
task is simpler and has no extra moving parts. The job code only needs a job id,
so moving it to an ARQ worker on Redis is a small change (see roadmap).

**Deterministic scoring.** Explainability beats a black-box number for a sales
team deciding who to call - see [scoring.md](scoring.md).

## Performance notes

- One shared `httpx.AsyncClient` (HTTP/2, connection pooling).
- Global concurrency 10 per job, max 2 requests in flight per host, 0.5 s
  politeness delay per host, 25 s hard cap per company.
- Retries only on timeouts / 5xx / 429, exponential backoff, 2 attempts.
- Leads list: `(score DESC NULLS LAST, id)` index matches the default sort, so
  paging is an index scan (checked with `EXPLAIN ANALYZE` on 5k rows: 1.7 ms full
  sort → 0.3 ms). The "verified email" filter uses an index-only scan.
- CSV export streams in 500-row batches, so memory stays flat.

## Code layout (backend)

```
app/
  api/v1/        thin routers - validation + wiring only
  services/      the actual logic, no http in here
    ingestion/   csv parsing, column mapping, import flow
    normalization/ domain, company name, dedup
    enrichment/  fetcher, pipeline, extractors/ (one strategy per signal)
    validation/  email, phone, website
    scoring/     rules, strategies, engine
    jobs/        the import → enrich → score orchestrator
    export/      streaming csv
  repositories/  sqlalchemy queries
  models/        orm tables
  schemas/       pydantic api contracts
```
