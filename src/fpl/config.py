from __future__ import annotations

import os

INGEST_VERSION = "ingest/0.1.0"

BASE = "https://fantasy.premierleague.com/api"

# Logical endpoint name -> URL template. event_id is substituted when GW-scoped.
ENDPOINTS: dict[str, str] = {
    "bootstrap-static": f"{BASE}/bootstrap-static/",
    "fixtures": f"{BASE}/fixtures/",
    "event-live": f"{BASE}/event/{{event_id}}/live/",
}

USER_AGENT = "fpl-optimizer/0.1 (portfolio project; contact via GitHub)"

TIMEOUT_S = 30.0
MAX_ATTEMPTS = 4
BACKOFF_BASE_S = 2.0


def database_url() -> str:
    url = os.environ.get("DATABASE_URL")
    if not url:
        raise RuntimeError("DATABASE_URL is not set")
    return url
