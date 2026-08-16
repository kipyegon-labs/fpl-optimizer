# scripts/check_staleness.py
import os
import sys
from datetime import datetime, timedelta, timezone

import psycopg

THRESHOLD = timedelta(hours=6)
EXPECTED_ENDPOINTS = ("bootstrap-static", "fixtures")

QUERY = """
SELECT endpoint, max(fetched_at) AS last_seen
FROM raw.fetch
GROUP BY endpoint
"""


def evaluate(seen: dict, now: datetime, threshold: timedelta = THRESHOLD):
    """Pure. Returns (report_lines, failures). Failures non-empty => alarm."""
    report, failures = [], []
    for endpoint in EXPECTED_ENDPOINTS:
        last = seen.get(endpoint)
        if last is None:
            failures.append(f"{endpoint}: NO ROWS — endpoint has never written")
            report.append(f"{endpoint}: last=NEVER MISSING")
            continue
        age = now - last
        stale = age > threshold
        report.append(f"{endpoint}: last={last.isoformat()} age={age} "
                      f"{'STALE' if stale else 'ok'}")
        if stale:
            failures.append(f"{endpoint}: stale by {age - threshold} beyond {threshold}")
    return report, failures


def main() -> int:
    now = datetime.now(timezone.utc)
    with psycopg.connect(os.environ["DATABASE_URL"]) as conn:
        rows = conn.execute(QUERY).fetchall()
    seen = {endpoint: last for endpoint, last in rows}

    report, failures = evaluate(seen, now)
    for line in report:
        print(line)

    if failures:
        print("\nSTALENESS ALARM", file=sys.stderr)
        for f in failures:
            print(f"  - {f}", file=sys.stderr)
        return 1
    print("\nall expected endpoints fresh")
    return 0


if __name__ == "__main__":
    sys.exit(main())