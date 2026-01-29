from __future__ import annotations
from pathlib import Path
import re

WEAK_HASH = re.compile(r"(?i)\b(md5|sha1)\b")
INSECURE_RANDOM = re.compile(r"(?i)\b(Math\.random\(|random\.random\(|rand\()")

def scan_crypto(repo_root: Path, files: list[Path], cfg: dict) -> list[dict]:
    out = []
    ctx_lines = int(cfg.get("context_lines", 40))
    for p in files:
        if p.suffix.lower() not in {".py", ".js", ".ts", ".go", ".java"}:
            continue
        try:
            text = p.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        lines = text.splitlines()
        for i, line in enumerate(lines, start=1):
            if WEAK_HASH.search(line):
                out.append({
                    "id": f"crypto.weak_hash:{p}:{i}",
                    "rule_id": "crypto.weak_hash",
                    "category": "crypto",
                    "severity": "medium",
                    "confidence": 0.6,
                    "title": "Potential weak hash usage (md5/sha1)",
                    "description": "md5/sha1 are considered weak for many security uses (passwords, signatures).",
                    "evidence": {
                        "path": str(p.relative_to(repo_root)),
                        "start_line": i,
                        "end_line": i,
                        "snippet": line.strip()[:300],
                        "context": "\n".join(lines[max(0,i-1-ctx_lines):min(len(lines), i-1+ctx_lines)])
                    },
                    "recommendation": [
                        "Use modern algorithms (e.g., SHA-256/512) for non-password hashing.",
                        "For passwords, use a KDF (bcrypt/scrypt/Argon2) via a reputable library.",
                        "Confirm the hash is not used for security-sensitive decisions."
                    ],
                    "references": ["OWASP:Cryptographic Storage"]
                })
            if INSECURE_RANDOM.search(line):
                out.append({
                    "id": f"crypto.insecure_random:{p}:{i}",
                    "rule_id": "crypto.insecure_random",
                    "category": "crypto",
                    "severity": "low",
                    "confidence": 0.5,
                    "title": "Potential insecure randomness for security use",
                    "description": "Non-cryptographic RNG may be unsafe for tokens, resets, or secrets.",
                    "evidence": {
                        "path": str(p.relative_to(repo_root)),
                        "start_line": i,
                        "end_line": i,
                        "snippet": line.strip()[:300],
                        "context": "\n".join(lines[max(0,i-1-ctx_lines):min(len(lines), i-1+ctx_lines)])
                    },
                    "recommendation": [
                        "Use a cryptographically secure RNG for tokens/secrets.",
                        "Audit usage sites: if only for UI/UX, downgrade severity."
                    ],
                    "references": ["CWE-338: Use of Cryptographically Weak PRNG"]
                })
    return out
