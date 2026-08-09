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

<!-- TODO: fill as it happens, not retrospectively. -->

## Attribution

Data from the public Fantasy Premier League API. Not affiliated with or endorsed
by the Premier League.
