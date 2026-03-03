# Chat Worklog - 2026-03-03

## Phase 1 - Initial Documentation

This file documents work completed in the current chat before revision.

### Delivered

- Added sitrep report generator:
  - `scripts/work_effort_report.py`
- Added minified, event-driven Karma core:
  - `scripts/karma_system.py`
- Added practical Karma CLI with persistent state:
  - `scripts/karma_cli.py`
- Updated root README with usage guidance.

### Current Runtime Model (before revision)

- Sitrep hub monitor uses adaptive pinging and stimulus-based checks.
- Long-task metric uses interval projection:
  - `longTasksPerMin = Math.round(longTasksInWindow * (60000 / expectedMs))`
  - Counter resets each sample, so short sample windows can inflate per-minute rates.
- `requestSample()` currently has no explicit `low` urgency path, so low-priority stimuli can be treated similarly to normal scheduling.
- Karma system supports in-memory event application and file persistence.
- Karma persistence path currently behaves as:
  - `load()`: direct `json.loads()` from file with no corrupt-file recovery.
  - `save()`: direct `write_text()` to target path (not atomic).
- Karma CLI supports:
  - `init`
  - `apply`
  - `snapshot`
  - `recent`
  - `score`

### Known Issues Identified

- Resource monitor can overestimate long-task rate during short sampling windows.
- `low` urgency stimulus path in monitor is not explicitly handled.
- Karma file persistence is not atomic and has no corrupt-file recovery guard.
- CLI `--json` exists at root and subcommand levels (redundant parser setup).

### Baseline Validation (pre-revision)

- Sitrep command:
  - Requested command (`python3 scripts/work_effort_report.py --no-open --hub-max-runs 120`) failed in this repo because `_work_efforts/devlog.md` is not present under `.ai_tmp/fogsift-waft`.
  - Baseline run completed with explicit paths:
    - `python3 scripts/work_effort_report.py --work-efforts-dir /Users/ctavolazzi/Code/_work_efforts --devlog /Users/ctavolazzi/Code/_work_efforts/devlog.md --no-open --hub-max-runs 120`
  - Output artifacts generated successfully: markdown/html/pdf report + hub page.
- Karma CLI baseline sequence (`--state-file .waft/karma/state_phase1.json`):
  - `init` -> score `0.0`, no events.
  - `apply --kind helped_user --delta 12 --reason baseline` -> score `12.0`, streak `1`.
  - `score` and `snapshot` matched persisted state and one appended event.

## Phase 3 - Post-Revision

### What changed and why

- `scripts/work_effort_report.py`:
  - Replaced short-window long-task projection with rolling-window event density (`longTaskTimestamps` over `longTaskWindowMs`) to reduce noisy overestimation.
  - Added explicit `requestSample(urgency)` behavior with dedicated `low` path:
    - `low`: throttled and deferred to reduce runtime impact.
    - `normal`: short deferred sample.
    - `high|critical`: immediate sample.
  - Added atomic file output helpers (`_atomic_write_text`, `_atomic_write_bytes`).
  - Switched latest/index writes to atomic operations:
    - `report_index.json`
    - `recent_work_report_latest.{md,html,pdf}`
    - `report_hub_latest.html`
- `scripts/karma_system.py`:
  - Added corrupt-load recovery guard in `load()` (safe reset to fresh state when JSON is invalid/non-dict or unreadable).
  - Switched `save()` to atomic `tmp + os.replace` writes.
- `scripts/karma_cli.py`:
  - No behavior changes required; command/output contract preserved.

### Validation commands and output summary

- Sitrep (exact requested command):
  - `python3 scripts/work_effort_report.py --no-open --hub-max-runs 120`
  - Result: fails in this repo context due to missing local `_work_efforts/devlog.md`.
- Sitrep (explicit paths for runnable validation):
  - `python3 scripts/work_effort_report.py --work-efforts-dir /Users/ctavolazzi/Code/_work_efforts --devlog /Users/ctavolazzi/Code/_work_efforts/devlog.md --no-open --hub-max-runs 120`
  - Result: success; markdown/html/pdf plus hub artifacts generated.
- Karma CLI smoke flow:
  - `python3 scripts/karma_cli.py --state-file .waft/karma/state_phase3.json init --json`
  - `python3 scripts/karma_cli.py --state-file .waft/karma/state_phase3.json apply --kind hardened_system --delta 18 --reason "post-revision" --json`
  - `python3 scripts/karma_cli.py --state-file .waft/karma/state_phase3.json score --json`
  - `python3 scripts/karma_cli.py --state-file .waft/karma/state_phase3.json snapshot --json`
  - Result: all commands succeeded; persisted state and event history consistent.

### Remaining risks

- Corrupt-load guard currently resets to fresh state and does not archive the corrupt source file.
- Rolling long-task window is less noisy but still bounded by browser `PerformanceObserver` availability.
- No user-facing CLI/API contract changes were introduced, so `README.md` was left unchanged.

---
