from __future__ import annotations

import time
from datetime import datetime, timezone

import httpx
from pydantic import BaseModel, ConfigDict

from fpl import config


class FetchResult(BaseModel):
    """One HTTP attempt sequence against one URL. Always produces a row."""

    model_config = ConfigDict(frozen=True)

    endpoint: str
    url: str
    requested_at: datetime
    fetched_at: datetime
    http_status: int | None
    ok: bool
    error: str | None
    body: bytes | None
    event_id: int | None = None


def _now() -> datetime:
    return datetime.now(timezone.utc)


def fetch(
    client: httpx.Client,
    endpoint: str,
    *,
    event_id: int | None = None,
) -> FetchResult:
    url = config.ENDPOINTS[endpoint].format(event_id=event_id)
    requested_at = _now()
    status: int | None = None
    error: str | None = None

    for attempt in range(1, config.MAX_ATTEMPTS + 1):
        try:
            resp = client.get(url)
            status = resp.status_code
            if resp.status_code == 200:
                return FetchResult(
                    endpoint=endpoint,
                    url=url,
                    requested_at=requested_at,
                    fetched_at=_now(),
                    http_status=200,
                    ok=True,
                    error=None,
                    body=resp.content,
                    event_id=event_id,
                )
            error = f"HTTP {resp.status_code}"
            # 4xx other than 429 will not fix itself; stop burning attempts.
            if 400 <= resp.status_code < 500 and resp.status_code != 429:
                break
        except httpx.HTTPError as exc:
            error = f"{type(exc).__name__}: {exc}"

        if attempt < config.MAX_ATTEMPTS:
            time.sleep(config.BACKOFF_BASE_S ** attempt)

    return FetchResult(
        endpoint=endpoint,
        url=url,
        requested_at=requested_at,
        fetched_at=_now(),
        http_status=status,
        ok=False,
        error=error or "unknown failure",
        body=None,
        event_id=event_id,
    )


def make_client() -> httpx.Client:
    return httpx.Client(
        timeout=config.TIMEOUT_S,
        headers={"User-Agent": config.USER_AGENT},
        follow_redirects=True,
    )
