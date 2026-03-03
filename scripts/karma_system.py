#!/usr/bin/env python3
"""Refined + minified Karma system.

Design goals:
- Single-file, low-abstraction, direct logic
- Event-driven updates (no background loop)
- Bounded history and predictable state transitions
"""

from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path


def _iso_now() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class KarmaEvent:
    kind: str
    delta: float
    reason: str = ""
    ts: str = field(default_factory=_iso_now)


@dataclass
class KarmaState:
    score: float = 0.0
    streak: int = 0
    level: str = "neutral"
    updated_at: str = field(default_factory=_iso_now)


class KarmaSystem:
    def __init__(self, min_score: float = -100.0, max_score: float = 100.0, max_events: int = 500):
        self.min_score = min_score
        self.max_score = max_score
        self.max_events = max_events
        self.state = KarmaState()
        self.events: list[KarmaEvent] = []

    def _clamp(self, value: float) -> float:
        if value < self.min_score:
            return self.min_score
        if value > self.max_score:
            return self.max_score
        return value

    def _level(self, score: float) -> str:
        if score >= 40:
            return "high"
        if score <= -40:
            return "low"
        return "neutral"

    def apply_event(self, kind: str, delta: float, reason: str = "") -> KarmaState:
        # Event-driven mutation only; no continuous polling.
        event = KarmaEvent(kind=kind, delta=delta, reason=reason)
        self.events.append(event)
        if len(self.events) > self.max_events:
            self.events = self.events[-self.max_events :]

        next_score = self._clamp(self.state.score + delta)
        same_sign = (self.state.score == 0.0) or (self.state.score * next_score > 0)
        if same_sign:
            self.state.streak += 1
        else:
            self.state.streak = 1

        self.state.score = next_score
        self.state.level = self._level(next_score)
        self.state.updated_at = event.ts
        return self.state

    def snapshot(self) -> dict:
        return {
            "state": {
                "score": self.state.score,
                "streak": self.state.streak,
                "level": self.state.level,
                "updated_at": self.state.updated_at,
            },
            "events": [
                {"kind": e.kind, "delta": e.delta, "reason": e.reason, "ts": e.ts}
                for e in self.events[-20:]
            ],
            "limits": {
                "min_score": self.min_score,
                "max_score": self.max_score,
                "max_events": self.max_events,
            },
        }

    def load(self, path: str | Path) -> "KarmaSystem":
        p = Path(path)
        if not p.exists():
            return self
        try:
            payload = json.loads(p.read_text(encoding="utf-8"))
            if not isinstance(payload, dict):
                raise ValueError("Payload is not an object")
            state = payload.get("state", {})
            limits = payload.get("limits", {})
            min_score = float(limits.get("min_score", self.min_score))
            max_score = float(limits.get("max_score", self.max_score))
            max_events = max(1, int(limits.get("max_events", self.max_events)))
            score = float(state.get("score", 0.0))
            streak = int(state.get("streak", 0))
            updated_at = str(state.get("updated_at", _iso_now()))
            events = payload.get("events", [])
            parsed_events: list[KarmaEvent] = []
            if isinstance(events, list):
                for e in events:
                    if not isinstance(e, dict):
                        continue
                    parsed_events.append(
                        KarmaEvent(
                            kind=str(e.get("kind", "unknown")),
                            delta=float(e.get("delta", 0.0)),
                            reason=str(e.get("reason", "")),
                            ts=str(e.get("ts", _iso_now())),
                        )
                    )
            self.min_score = min_score
            self.max_score = max_score
            self.max_events = max_events
            clamped_score = self._clamp(score)
            self.state = KarmaState(
                score=clamped_score,
                streak=max(0, streak),
                level=self._level(clamped_score),
                updated_at=updated_at,
            )
            self.events = parsed_events[-self.max_events :]
        except (OSError, json.JSONDecodeError, ValueError, TypeError):
            self.state = KarmaState()
            self.events = []
        return self

    def save(self, path: str | Path) -> Path:
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        tmp = p.with_name(f".{p.name}.tmp-{os.getpid()}-{time.time_ns()}")
        tmp.write_text(json.dumps(self.snapshot(), indent=2), encoding="utf-8")
        os.replace(tmp, p)
        return p


if __name__ == "__main__":
    karma = KarmaSystem()
    karma.apply_event("helped_user", +12, "resolved blocker quickly")
    karma.apply_event("introduced_regression", -8, "needed follow-up fix")
    karma.apply_event("hardened_system", +18, "added resource guardrails")
    print(karma.snapshot())
