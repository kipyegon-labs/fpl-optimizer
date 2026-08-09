from __future__ import annotations

import argparse
import json
import sys

from fpl import fetch as fetch_mod
from fpl import store


def live_event_ids(bootstrap_body: bytes) -> list[int]:
    """Gameweeks whose live scores could still be moving.

    Current, plus previous — FPL amends bonus points and stat corrections for a
    day or two after a gameweek ends. Before GW1 this is empty, which is correct.
    """
    data = json.loads(bootstrap_body)
    ids = [
        e["id"]
        for e in data.get("events", [])
        if e.get("is_current") or e.get("is_previous")
    ]
    return sorted(set(ids))


def snapshot() -> int:
    failures = 0
    with fetch_mod.make_client() as client, store.connect() as conn:
        boot = fetch_mod.fetch(client, "bootstrap-static")
        store.write(conn, boot)
        conn.commit()
        if not boot.ok:
            print(f"FAIL bootstrap-static: {boot.error}", file=sys.stderr)
            failures += 1

        fixtures = fetch_mod.fetch(client, "fixtures")
        store.write(conn, fixtures)
        conn.commit()
        if not fixtures.ok:
            print(f"FAIL fixtures: {fixtures.error}", file=sys.stderr)
            failures += 1

        event_ids = live_event_ids(boot.body) if boot.ok and boot.body else []
        for event_id in event_ids:
            live = fetch_mod.fetch(client, "event-live", event_id=event_id)
            store.write(conn, live)
            conn.commit()
            if not live.ok:
                print(f"FAIL event-live {event_id}: {live.error}", file=sys.stderr)
                failures += 1

        print(
            f"snapshot: bootstrap={boot.ok} fixtures={fixtures.ok} "
            f"live_events={event_ids} failures={failures}"
        )
    return 1 if failures else 0


def main() -> int:
    parser = argparse.ArgumentParser(prog="fpl")
    parser.add_argument("command", choices=["snapshot"])
    args = parser.parse_args()
    if args.command == "snapshot":
        return snapshot()
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
