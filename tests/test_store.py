from __future__ import annotations

import json
from datetime import datetime, timezone

from fpl.cli import live_event_ids
from fpl.fetch import FetchResult
from fpl.store import compress, decompress, row_from, sha256_hex


def _result(body: bytes | None, ok: bool = True) -> FetchResult:
    now = datetime.now(timezone.utc)
    return FetchResult(
        endpoint="bootstrap-static",
        url="https://example.invalid/",
        requested_at=now,
        fetched_at=now,
        http_status=200 if ok else 503,
        ok=ok,
        error=None if ok else "HTTP 503",
        body=body,
    )


def test_gzip_roundtrip_and_determinism():
    body = b'{"elements": [1, 2, 3]}'
    blob = compress(body)
    assert decompress(blob) == body
    assert compress(body) == blob  # mtime=0 => byte-identical across runs


def test_hash_is_over_raw_bytes():
    body = b"abc"
    assert sha256_hex(body) == (
        "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"
    )


def test_failed_fetch_still_produces_a_row():
    row = row_from(_result(None, ok=False))
    assert row["ok"] is False
    assert row["payload_gzip"] is None
    assert row["payload_sha256"] is None
    assert row["error"] == "HTTP 503"


def test_successful_row_carries_payload_metadata():
    body = b'{"x": 1}'
    row = row_from(_result(body))
    assert row["payload_bytes"] == len(body)
    assert row["payload_sha256"] == sha256_hex(body)
    assert decompress(row["payload_gzip"]) == body


def test_no_live_events_before_season_start():
    body = json.dumps(
        {"events": [{"id": 1, "is_current": False, "is_previous": False, "is_next": True}]}
    ).encode()
    assert live_event_ids(body) == []


def test_current_and_previous_events_are_pulled():
    body = json.dumps(
        {
            "events": [
                {"id": 1, "is_current": False, "is_previous": True},
                {"id": 2, "is_current": True, "is_previous": False},
                {"id": 3, "is_next": True},
            ]
        }
    ).encode()
    assert live_event_ids(body) == [1, 2]
