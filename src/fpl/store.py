from __future__ import annotations

import gzip
import hashlib

import psycopg

from fpl import config
from fpl.fetch import FetchResult

INSERT_SQL = """
insert into raw.fetch (
    endpoint, url, requested_at, fetched_at, http_status, ok, error,
    payload_sha256, payload_gzip, payload_bytes, event_id, ingest_version
) values (
    %(endpoint)s, %(url)s, %(requested_at)s, %(fetched_at)s, %(http_status)s,
    %(ok)s, %(error)s, %(payload_sha256)s, %(payload_gzip)s, %(payload_bytes)s,
    %(event_id)s, %(ingest_version)s
)
returning fetch_id
"""


def sha256_hex(body: bytes) -> str:
    return hashlib.sha256(body).hexdigest()


def compress(body: bytes) -> bytes:
    # mtime=0 so identical bytes compress to identical bytes — makes the stored
    # blob reproducible and diffable across runs.
    return gzip.compress(body, compresslevel=6, mtime=0)


def decompress(blob: bytes) -> bytes:
    return gzip.decompress(blob)


def row_from(result: FetchResult) -> dict:
    body = result.body
    return {
        "endpoint": result.endpoint,
        "url": result.url,
        "requested_at": result.requested_at,
        "fetched_at": result.fetched_at,
        "http_status": result.http_status,
        "ok": result.ok,
        "error": result.error,
        "payload_sha256": sha256_hex(body) if body is not None else None,
        "payload_gzip": compress(body) if body is not None else None,
        "payload_bytes": len(body) if body is not None else None,
        "event_id": result.event_id,
        "ingest_version": config.INGEST_VERSION,
    }


def write(conn: psycopg.Connection, result: FetchResult) -> int:
    with conn.cursor() as cur:
        cur.execute(INSERT_SQL, row_from(result))
        (fetch_id,) = cur.fetchone()
    return fetch_id


def connect() -> psycopg.Connection:
    return psycopg.connect(config.database_url(), autocommit=False)
