from __future__ import annotations
from pathlib import Path
import re
import math

# Minimal starter regexes (extend in rules/secrets_regex.yaml)
SECRET_PATTERNS = [
    ("secrets.aws_access_key_id", re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
    ("secrets.generic_api_key", re.compile(r"(?i)\b(api[_-]?key|secret|token)\b\s*[:=]\s*['\"][A-Za-z0-9_\-]{16,}['\"]")),
    ("secrets.private_key_block", re.compile(r"-----BEGIN (RSA|EC|OPENSSH) PRIVATE KEY-----")),
]

def shannon_entropy(s: str) -> float:
    if not s:
        return 0.0
    freq = {}
    for c in s:
        freq[c] = freq.get(c, 0) + 1
    ent = 0.0
    for c, n in freq.items():
        p = n / len(s)
        ent -= p * math.log2(p)
    return ent

def scan_secrets(repo_root: Path, files: list[Path], cfg: dict) -> list[dict]:
    out = []
    ctx_lines = int(cfg.get("context_lines", 40))
    for p in files:
        try:
            text = p.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        lines = text.splitlines()
        for i, line in enumerate(lines, start=1):
            for rule_id, rx in SECRET_PATTERNS:
                if rx.search(line):
                    snippet = line.strip()[:300]
                    out.append({
                        "id": f"{rule_id}:{p}:{i}",
                        "rule_id": rule_id,
                        "category": "secrets",
                        "severity": "high",
                        "confidence": 0.7,
                        "title": "Possible secret detected",
                        "description": "A string matching a secret pattern was found.",
                        "evidence": {
                            "path": str(p.relative_to(repo_root)),
                            "start_line": i,
                            "end_line": i,
                            "snippet": snippet,
                            "context": "\n".join(lines[max(0,i-1-ctx_lines):min(len(lines), i-1+ctx_lines)])
                        },
                        "recommendation": [
                            "Remove the secret from the repo history if possible.",
                            "Rotate the credential immediately.",
                            "Use environment variables or a secret manager."
                        ],
                        "references": ["OWASP:Secrets Management"]
                    })
    return out
