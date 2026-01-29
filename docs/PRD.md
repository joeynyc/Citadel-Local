# PRD: RedTeam Local (Offline Repo Security Auditor)

Date: 2026-01-29

## Problem
Developers accidentally ship vulnerabilities and secrets because security checks are noisy, online-only, or too hard to adopt.

## Target users
- OSS maintainers
- small teams
- solo devs
- local-first builders using Ollama

## Goals (v1)
- Scan a folder/repo offline
- Detect common security issues with deterministic rules
- Use local Ollama models to:
  - classify severity/confidence
  - provide safe remediation steps
  - reduce false positives
- Produce `findings.json` + `report.md`

## Non-goals (v1)
- No exploit generation
- No dynamic penetration testing
- No scanning of third-party systems

## Core workflows
1. Developer runs `rtl scan <path>`
2. Tool inventories repo, runs detectors, creates evidence bundles
3. Council labeling (triage -> deep -> skeptic)
4. Tool outputs report artifacts

## CLI
- `rtl scan <path> --out out/`
- `rtl diff <path> --base origin/main`
- `rtl baseline <path> --out baseline.json`
- `rtl report <findings.json> --out report.md`

## Output requirements
- stable finding IDs
- severity + confidence
- exact file/line references
- fix guidance

## Acceptance criteria
- v1 runs on a medium repo (<50k files) with reasonable time
- produces deterministic findings without LLM enabled
- with LLM enabled, adds better descriptions + fix steps without hallucinating new evidence
