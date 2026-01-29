# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Citadel Local is a **defensive**, offline-first Python security auditor that scans codebases for vulnerabilities (secrets, injection patterns, insecure crypto) and produces remediation guidance using local Ollama models. It does **not** generate exploit payloads or offensive instructions.

## Commands

```bash
# Install (editable, with dev tools)
pip install -e .[dev]

# Run tests
pytest -q

# Lint
ruff check src/ tests/

# Format
ruff format src/ tests/

# Scan a repository
citadel scan /path/to/repo --out out/ --config .citadel-local.yaml
```

## Architecture

The system is a four-stage pipeline orchestrated from `cli.py`:

```
CLI (cli.py) → Config (config.py)
  → File Collection (repo_scan/file_walk.py) + Inventory (repo_scan/inventory.py)
  → Deterministic Detectors (detectors/)
  → Optional LLM Council (llm/council.py)
  → Reporting (reporting/)
```

**Key design principle: "Evidence first, models second."** Deterministic detectors produce candidate findings with grounded evidence. LLM models only judge these evidence bundles — they never free-scan the repo.

### Source layout (`src/citadel_local/`)

- **cli.py** — Entry point. Subcommands: `scan`, `diff` (stub), `baseline` (stub), `report` (stub).
- **config.py** — Loads `.citadel-local.yaml`, merges with defaults.
- **repo_scan/** — `file_walk.py` collects files (respects ignore patterns, max file size). `inventory.py` detects repo metadata.
- **detectors/** — Rule-based scanners. Each returns `list[dict]` of findings. Orchestrated by `detectors/__init__.py:run_detectors()`.
  - `secrets.py` — Regex + Shannon entropy for credentials/keys.
  - `injections.py` — Shell and SQL injection patterns.
  - `crypto.py` — Weak hashing, insecure randomness.
- **llm/** — Ollama integration. `council.py` runs a three-model pipeline: Triage (fast) → Deep analysis (strong coder) → Skeptic (false-positive reducer). `ollama_client.py` wraps the Ollama HTTP API. `prompts.py` holds prompt templates.
- **reporting/** — `report_json.py` exports structured JSON. `report_md.py` generates a Markdown report sorted by severity.

### Detection rules

YAML-based rules in `rules/`: `insecure_patterns.yaml` (injection/crypto patterns) and `secrets_regex.yaml` (secret detection regexes).

### Adding a new detector

1. Create a module in `src/citadel_local/detectors/`
2. Register it in `detectors/__init__.py` (add the scan function to the `run_detectors` loop)
3. Add rule IDs in `rules/*.yaml`
4. Add test cases in `tests/`

## Configuration

Config file: `.citadel-local.yaml` (copy from `.citadel-local.example.yaml`). Key settings:

- `ignore` — directories to skip (node_modules, .git, vendor, etc.)
- `max_file_mb` — max file size to scan (default: 2)
- `context_lines` — lines of context around findings (default: 40)
- `ollama.enabled` — toggle LLM council (default: true)
- `ollama.base_url` — Ollama endpoint (default: `http://127.0.0.1:11434`)
- Model routing: `triage_model`, `deep_model`, `skeptic_model`

## Safety Constraints

This tool is strictly defensive. All LLM prompts enforce `defensive_only: true` and `no_exploit_payloads: true`. Do not add features that generate exploit code, weaponized payloads, or guidance for attacking systems without authorization.

## Dependencies

Minimal: `pyyaml` and `requests`. Python 3.11+ required.
