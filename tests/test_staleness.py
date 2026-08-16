# tests/test_staleness.py
from datetime import datetime, timedelta, timezone
from fpl.check_staleness import evaluate

NOW = datetime(2026, 8, 16, 12, 0, tzinfo=timezone.utc)


def test_all_fresh():
    seen = {"bootstrap-static": NOW - timedelta(hours=2),
            "fixtures": NOW - timedelta(hours=3)}
    _, failures = evaluate(seen, NOW)
    assert failures == []


def test_one_endpoint_stale_while_other_fresh():
    seen = {"bootstrap-static": NOW - timedelta(minutes=30),
            "fixtures": NOW - timedelta(hours=9)}
    _, failures = evaluate(seen, NOW)
    assert len(failures) == 1 and "fixtures" in failures[0]


def test_missing_endpoint_fails():
    seen = {"bootstrap-static": NOW - timedelta(hours=1)}
    _, failures = evaluate(seen, NOW)
    assert any("NO ROWS" in f for f in failures)


def test_empty_database_fails_loudly():
    _, failures = evaluate({}, NOW)
    assert len(failures) == 2