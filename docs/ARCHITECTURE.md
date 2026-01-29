# Architecture

## Goals
1. **Offline-first**: code stays on your machine.
2. **High signal**: deterministic detectors find evidence; LLMs explain and prioritize.
3. **Low hallucination**: models never “free-scan” the entire repo. They only judge evidence bundles.
4. **Actionable output**: markdown report + JSON + optional SARIF.

## Pipeline

### 1) Inventory
- languages, package managers, frameworks
- entrypoints
- CI/CD & infrastructure files

### 2) Deterministic detectors (fast)
Examples:
- secrets (regex + entropy)
- injection patterns (shell, SQL)
- insecure deserialization / eval usage
- crypto misuse patterns
- dangerous configs (Docker, GitHub Actions, Kubernetes)

Detectors output *candidate findings* with:
- file path
- line ranges
- snippet + small context window
- detector id + rule id

### 3) Model council (roles, not “agents”)
- **Triage** (fast): labels category, severity, confidence, needs_deep_review
- **Deep** (strong coder model): root cause, safe remediation, patch guidance, tests to add
- **Skeptic** (middle model): argues against the finding, marks missing evidence, reduces false positives

### 4) Reporting
- Merge council outputs into a final Finding record (schema in `docs/SCHEMA.md`)
- Render to `findings.json` and `report.md`
- Optional: SARIF

## Why this works
Detectors provide grounded evidence. Models provide:
- context awareness and prioritization
- remediation guidance
- false-positive reduction

This avoids the classic failure mode: “LLM guessed a vulnerability without proof.”

## Performance tips
- Scan only changed files in CI (`citadel diff`)
- Cache LLM outputs by `{file_hash}:{finding_id}:{model}:{prompt_version}`
- Limit context to the smallest relevant function + call sites
