# Citadel Local (offline repo security auditor)

Local-first, open-source repo scanner that flags common security risks (secrets, injection patterns, authz footguns, insecure crypto, CI/CD misconfig) and produces actionable remediation guidance using **Ollama** models.

This project is **defensive**: it audits code you own or have permission to test. It does not generate exploit payloads or offensive instructions.

## Quick start

### 1) Requirements
- Python 3.11+
- Ollama running locally (default: `http://127.0.0.1:11434`)

### 2) Install (editable)
```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

### 3) Create a config
```bash
cp .citadel-local.example.yaml .citadel-local.yaml
```

### 4) Scan a repo
```bash
citadel scan /path/to/repo
```

Outputs:
- `out/findings.json`
- `out/report.md`

## Model routing (recommended defaults)

- triage: `llama3.2:3b`
- deep analysis + fixes: `qwen3-coder:30b`
- skeptic (false-positive reducer): `gpt-oss:20b`

See: `docs/ARCHITECTURE.md`

## Commands
- `citadel scan <path>`: scan a repo folder
- `citadel diff <path>`: scan only changed files vs git base (PR-friendly)
- `citadel baseline <path>`: record current findings as accepted baseline
- `citadel report <findings.json>`: render markdown report from JSON

## Safety boundaries
- No exploit chains, no weaponized payloads
- No guidance for attacking systems you don’t own
- Focus on detection, context, and remediation

## License
MIT (see `LICENSE`)
