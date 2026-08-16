# FPL Optimizer — live evals across the 2026/27 season

Point-in-time-correct ingestion of the public Fantasy Premier League API, a squad
optimizer, and a weekly published scorecard scored against real gameweek outcomes.

The artifact is the track record, not the code.

Non-commercial. No paid tier, no sponsorship, no donations.

## Status

Phase 1 — ingestion. Ingestion must be live before GW1 (2026-08-21). Missed
gameweeks cannot be backfilled honestly.

## The one rule

`raw.fetch` is append-only. Every row records *when* the bytes were observed.
No model feature may ever be computed from a row whose `fetched_at` is later than
the deadline of the gameweek being predicted:

```sql
where fetched_at < (select deadline_time from derived.event where event_id = :gw)
```

Anything else is lookahead bias, and it silently invalidates every backtest
produced afterwards. The `derived` schema is disposable and rebuildable from
`raw`. `raw` is never rewritten.

Two mechanisms enforce this: the ingest role holds only `SELECT, INSERT`, and a
statement trigger on `raw.fetch` raises on `UPDATE`, `DELETE`, and `TRUNCATE`.

## Run locally

```bash
docker compose up -d                       # postgres:16, runs sql/ on first boot
export DATABASE_URL="postgresql://fpl:fpl@localhost:5432/fpl"
uv sync
uv run python -m fpl.cli snapshot
uv run pytest
```

Every invocation writes exactly one row per endpoint attempted, including
failures. A failed snapshot exits non-zero so the scheduler reports red.

## Architecture

<!-- TODO(phase 1 done): diagram — cron -> fetch -> raw.fetch -> derived -> optimizer -> scorecard -->

## Evals

<!-- TODO(phase 1 done): ingestion reliability table — scheduled runs, completed,
     late by >30min, failed, distinct pre-deadline snapshots per gameweek.
     Include the gameweeks where coverage was bad. -->

A repo without an eval table is a demo, not evidence.

## What broke and how I fixed it

## Phase 1 evals — ingestion fidelity

Measured 2026-08-16, over 7 days (2026-08-09 → 2026-08-16).
Cron: `7 */3 * * *` (every 3h, UTC).

| Metric | Target | Measured | Status |
|---|---|---|---|
| Endpoints captured | 2 (bootstrap-static, fixtures) | 2 | PASS |
| Scheduled runs succeeded | — | 61 | — |
| Fetch events landed in Neon | = successful runs | 62 (61 sched + 1 manual) | PASS |
| Runs green but zero rows written | 0 | 0 | PASS |
| Slots skipped entirely (gap ≥ 6h) | 0 | 0 | PASS |
| Median inter-fetch gap | ~3h00m | 2h47m | PASS |
| Max inter-fetch gap | < 6h | 4h46m | PASS (jitter, no loss) |
| Total rows | — | 124 | — |
| bootstrap-static compression | — | 10.6× | — |
| fixtures compression | — | 19.8× | — |
| UPDATE on `raw.fetch` rejected | yes | yes | PASS |
| DELETE on `raw.fetch` rejected | yes | yes | PASS |
| Unit tests | 6/6 | 6/6 | PASS |

### Known limitations
- Gaps are measured between fetch *completions*, so GitHub queue lag and job
  runtime are not separable. The 4h46m max gap is one late run, not a miss.
- `event-live` is not yet ingested; season storage projection is therefore a
  lower bound and must be re-measured after GW1 against the 250 MB tripwire.
- 3h cadence is coarse for in-match data. Acceptable pre-season; revisit for
  live gameweeks.

## Attribution

Data from the public Fantasy Premier League API. Not affiliated with or endorsed
by the Premier League.
