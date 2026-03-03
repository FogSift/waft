#!/usr/bin/env python3
"""Karma CLI: event-driven state operations with JSON output."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from karma_system import KarmaSystem

DEFAULT_STATE = Path(".waft/karma/state.json")


def _parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Event-driven Karma system CLI")
    p.add_argument("--state-file", default=str(DEFAULT_STATE), help="Path to persisted karma state")
    p.add_argument("--json", action="store_true", help="Print machine-readable output")
    sub = p.add_subparsers(dest="command", required=True)

    init_cmd = sub.add_parser("init", help="Initialize state file")
    init_cmd.add_argument("--json", action="store_true", help=argparse.SUPPRESS)

    apply_cmd = sub.add_parser("apply", help="Apply one karma event")
    apply_cmd.add_argument("--json", action="store_true", help=argparse.SUPPRESS)
    apply_cmd.add_argument("--kind", required=True, help="Event kind label")
    apply_cmd.add_argument("--delta", required=True, type=float, help="Signed score delta")
    apply_cmd.add_argument("--reason", default="", help="Optional reason text")

    snapshot_cmd = sub.add_parser("snapshot", help="Show full snapshot")
    snapshot_cmd.add_argument("--json", action="store_true", help=argparse.SUPPRESS)
    recent_cmd = sub.add_parser("recent", help="Show recent events")
    recent_cmd.add_argument("--json", action="store_true", help=argparse.SUPPRESS)
    score_cmd = sub.add_parser("score", help="Show compact score summary")
    score_cmd.add_argument("--json", action="store_true", help=argparse.SUPPRESS)
    return p


def _print(payload: dict, as_json: bool) -> None:
    if as_json:
        print(json.dumps(payload, separators=(",", ":")))
        return
    print(json.dumps(payload, indent=2))


def main() -> int:
    args = _parser().parse_args()
    state_path = Path(args.state_file)
    ks = KarmaSystem().load(state_path)

    if args.command == "init":
        ks = KarmaSystem()
        ks.save(state_path)
        _print({"ok": True, "command": "init", "state_file": str(state_path), "snapshot": ks.snapshot()}, args.json)
        return 0

    if args.command == "apply":
        state = ks.apply_event(kind=args.kind, delta=args.delta, reason=args.reason)
        ks.save(state_path)
        _print(
            {
                "ok": True,
                "command": "apply",
                "event": {"kind": args.kind, "delta": args.delta, "reason": args.reason},
                "state": {
                    "score": state.score,
                    "streak": state.streak,
                    "level": state.level,
                    "updated_at": state.updated_at,
                },
                "state_file": str(state_path),
            },
            args.json,
        )
        return 0

    snap = ks.snapshot()
    if args.command == "snapshot":
        _print({"ok": True, "command": "snapshot", "state_file": str(state_path), "snapshot": snap}, args.json)
        return 0

    if args.command == "recent":
        _print(
            {
                "ok": True,
                "command": "recent",
                "state_file": str(state_path),
                "events": snap["events"],
                "count": len(snap["events"]),
            },
            args.json,
        )
        return 0

    if args.command == "score":
        st = snap["state"]
        _print(
            {
                "ok": True,
                "command": "score",
                "state_file": str(state_path),
                "score": st["score"],
                "streak": st["streak"],
                "level": st["level"],
                "updated_at": st["updated_at"],
            },
            args.json,
        )
        return 0

    return 1


if __name__ == "__main__":
    raise SystemExit(main())
