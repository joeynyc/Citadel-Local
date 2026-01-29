# Contributing

## Dev setup
```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
```

## Run tests
```bash
pytest -q
```

## Add a detector
1. Add a module in `src/redteam_local/detectors/`
2. Register it in `src/redteam_local/detectors/__init__.py`
3. Add rule ids in `rules/*.yaml`
4. Add test cases in `tests/`

## Principles
- Evidence first, models second
- Prefer fewer high-signal rules over noisy “everything is a vuln”
