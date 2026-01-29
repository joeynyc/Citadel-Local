from __future__ import annotations
from pathlib import Path
from .secrets import scan_secrets
from .injections import scan_injections
from .crypto import scan_crypto

def run_detectors(repo_root: Path, files: list[Path], cfg: dict) -> list[dict]:
    findings: list[dict] = []
    for fn in (scan_secrets, scan_injections, scan_crypto):
        findings.extend(fn(repo_root, files, cfg))
    return findings
