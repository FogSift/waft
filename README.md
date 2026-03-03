# waft

Minimal starting surface for FogSift WAFT.

## Included now

- `scripts/work_effort_report.py` - sitrep hub report generator
- `scripts/karma_system.py` - refined, minified, event-driven Karma system
- `scripts/karma_cli.py` - practical CLI wrapper with JSON output + persistence

## Karma quick start

```bash
python3 scripts/karma_cli.py init
python3 scripts/karma_cli.py apply --kind helped_user --delta 12 --reason "unblocked deploy"
python3 scripts/karma_cli.py score
python3 scripts/karma_cli.py recent
python3 scripts/karma_cli.py snapshot --json
```