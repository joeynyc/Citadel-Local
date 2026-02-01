# Citadel Local (offline repo security auditor)

Local-first, open-source repo scanner that flags common security risks (secrets, injection patterns, authz footguns, insecure crypto, CI/CD misconfig) and produces actionable remediation guidance using **Ollama** models.

This project is **defensive**: it audits code you own or have permission to test. It does not generate exploit payloads or offensive instructions.

## Quick start

### 1) Requirements
- Python 3.11+
- Ollama running locally (default: `http://127.0.0.1:11434`)
  - [Install Ollama](https://ollama.ai) for your platform
  - Run: `ollama serve` in a separate terminal
  - Verify: `curl http://127.0.0.1:11434/api/tags` returns available models

### 2) Install (editable)
```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

### 3) Create a config
```bash
cp .citadel-local.example.yaml .citadel-local.yaml
# Edit to customize scan rules, ignore patterns, model selection, etc.
# See: docs/CONFIGURATION.md for detailed options
```

### 4) Scan a repo
```bash
citadel scan /path/to/repo
```

Outputs:
- `out/findings.json` — structured findings for tooling integration
- `out/report.md` — human-readable markdown report

## Commands

| Command | Purpose | Use case |
|---------|---------|----------|
| `citadel scan <path>` | Full scan of a repo | Initial security audit, scheduled scans |
| `citadel diff <path>` | Scan only changed files vs git base | PR checks, pre-commit hooks |
| `citadel baseline <path>` | Record current findings as baseline | Acknowledge known issues, track deltas |
| `citadel report <findings.json>` | Render markdown report from JSON | Re-format findings, share with team |

## Example output

### findings.json (structure)
```json
[
  {
    "id": "secrets_001",
    "file": "src/config.py",
    "line_start": 42,
    "line_end": 42,
    "severity": "critical",
    "category": "secrets",
    "evidence": "AWS_SECRET_KEY=AKIA...",
    "triage": {
      "category": "hardcoded_credential",
      "confidence": 0.98
    },
    "analysis": {
      "root_cause": "Plaintext secret committed to repo",
      "remediation": "Remove secret, rotate key, add to .gitignore"
    },
    "skeptic": {
      "false_positive_risk": 0.02,
      "notes": "High confidence match to AWS secret pattern"
    }
  }
]
```

### report.md (excerpt)
```
# Security Audit Report
Generated: 2026-02-01 14:32:45 UTC

## Critical (1)
### AWS Secret Key (secrets_001)
**File:** src/config.py:42
**Confidence:** 98%

**Finding:** Plaintext AWS secret found in source code

**Remediation:**
1. Immediately rotate the exposed key
2. Remove the secret from git history (use git-filter-repo or BFG)
3. Add `*.secrets` to .gitignore
4. Use environment variables or AWS Secrets Manager

## Medium (3)
...
```

## Model routing (recommended defaults)

| Role | Model | Why |
|------|-------|-----|
| **Triage** | `llama3.2:3b` | Fast category/severity labeling (3B params, ~2s) |
| **Deep analysis** | `qwen3-coder:30b` | Strong code reasoning, remediation guidance (30B params) |
| **Skeptic** | `gpt-oss:20b` | False-positive reduction, critical thinking |

**Trade-offs:**
- Smaller models = faster, lower memory. Larger = better accuracy.
- Test on your codebase to find the sweet spot for latency vs quality.
- See: `docs/CONFIGURATION.md` for model selection guidance

## Architecture

Citadel follows an **evidence-first** pipeline:

```
Scan files → Inventory metadata → Run deterministic detectors
  → Pass candidate findings to model council → Merge outputs
  → Report findings
```

**Key principle:** Models never "free-scan." They analyze evidence bundles provided by deterministic detectors, which avoids hallucination.

See: `docs/ARCHITECTURE.md` for detailed pipeline description.

## Safety boundaries
- No exploit chains, no weaponized payloads
- No guidance for attacking systems you don't own
- Focus on detection, context, and remediation
- All LLM prompts enforce `defensive_only: true`

See: `docs/SECURITY.md` for full policy.

## Documentation

- **[docs/CONFIGURATION.md](docs/CONFIGURATION.md)** — Config file reference, model selection, performance tuning
- **[docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)** — Pipeline design, detector rules, council prompts
- **[docs/CONTRIBUTING.md](docs/CONTRIBUTING.md)** — Development setup, adding detectors, testing
- **[docs/SCHEMA.md](docs/SCHEMA.md)** — JSON schema for findings and model outputs
- **[docs/PROMPTS.md](docs/PROMPTS.md)** — LLM council prompts (triage, analysis, skeptic)
- **[docs/SECURITY.md](docs/SECURITY.md)** — Security policy, threat model, bug reporting
- **[docs/CI-CD.md](docs/CI-CD.md)** — Integration with GitHub Actions, GitLab CI, Jenkins
- **[docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md)** — Common issues and solutions

## License
MIT (see `LICENSE`)
