from __future__ import annotations
from pathlib import Path
import re

SHELL_CALLS = re.compile(r"(?i)\b(os\.system|subprocess\.(popen|call|run)|exec\(|eval\()\b")
SQL_CONCAT = re.compile(r"(?i)\bSELECT\b.*\+.*\bFROM\b|\bINSERT\b.*\+|\bUPDATE\b.*\+|\bDELETE\b.*\+")

def scan_injections(repo_root: Path, files: list[Path], cfg: dict) -> list[dict]:
    out = []
    ctx_lines = int(cfg.get("context_lines", 40))
    for p in files:
        # simple extension filter for v1
        if p.suffix.lower() not in {".py", ".js", ".ts", ".tsx", ".jsx", ".sh"}:
            continue
        try:
            text = p.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        lines = text.splitlines()
        for i, line in enumerate(lines, start=1):
            if SHELL_CALLS.search(line):
                out.append({
                    "id": f"injection.shell_call:{p}:{i}",
                    "rule_id": "injection.shell_call",
                    "category": "injection",
                    "severity": "medium",
                    "confidence": 0.55,
                    "title": "Potential command injection surface",
                    "description": "A shell execution primitive was detected. Validate and constrain inputs before use.",
                    "evidence": {
                        "path": str(p.relative_to(repo_root)),
                        "start_line": i,
                        "end_line": i,
                        "snippet": line.strip()[:300],
                        "context": "\n".join(lines[max(0,i-1-ctx_lines):min(len(lines), i-1+ctx_lines)])
                    },
                    "recommendation": [
                        "Avoid shell=True and string concatenation.",
                        "Use argument arrays, strict allowlists, and escaping where appropriate.",
                        "Add tests for malicious-looking inputs (safe, non-payload)."
                    ],
                    "references": ["CWE-78: OS Command Injection"]
                })
            if SQL_CONCAT.search(line):
                out.append({
                    "id": f"injection.sql_concat:{p}:{i}",
                    "rule_id": "injection.sql_concat",
                    "category": "injection",
                    "severity": "high",
                    "confidence": 0.5,
                    "title": "Potential SQL injection via string concatenation",
                    "description": "SQL query construction via concatenation can allow injection if user input is included.",
                    "evidence": {
                        "path": str(p.relative_to(repo_root)),
                        "start_line": i,
                        "end_line": i,
                        "snippet": line.strip()[:300],
                        "context": "\n".join(lines[max(0,i-1-ctx_lines):min(len(lines), i-1+ctx_lines)])
                    },
                    "recommendation": [
                        "Use parameterized queries / prepared statements.",
                        "Validate inputs with strict schemas.",
                        "Add unit tests that confirm parameters are bound."
                    ],
                    "references": ["CWE-89: SQL Injection"]
                })
    return out
