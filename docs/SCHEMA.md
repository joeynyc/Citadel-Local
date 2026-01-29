# Findings JSON Schema (v1)

A `Finding` is the atomic unit of output, with grounded evidence and model-augmented analysis.

## Top-level
- `schema_version`: string (e.g., "1.0")
- `scan`: metadata about the scan run
- `findings`: array of Finding

## Finding fields

Required:
- `id`: stable id (hash of path + rule + line range)
- `rule_id`: e.g. "secrets.generic_api_key"
- `category`: e.g. "secrets" | "injection" | "auth" | "crypto" | "config" | "deps"
- `severity`: "critical" | "high" | "medium" | "low" | "info"
- `confidence`: 0.0 - 1.0
- `title`: short string
- `description`: short explanation
- `evidence`: object with:
  - `path`: file path relative to repo root
  - `start_line`, `end_line`
  - `snippet`: the minimal code/config excerpt
  - `context`: optional wider window
- `recommendation`: bullet list steps
- `references`: optional (CWE/OWASP tags, docs)

Optional (model outputs):
- `triage`: `{model, rationale_short, needs_deep_review}`
- `analysis`: `{model, root_cause, exploit_scenario_safe, fix_plan, safe_patch_suggestion, tests_to_add}`
- `skeptic`: `{model, counterarguments, missing_evidence, false_positive_likelihood, recommendation}`

## Example
See `examples/sample_findings.json`
