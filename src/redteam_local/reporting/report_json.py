from __future__ import annotations
from pathlib import Path
import json
from datetime import datetime

def write_findings_json(path: Path, repo_root: Path, meta: dict, findings: list[dict]) -> None:
    payload = {
        "schema_version": "1.0",
        "scan": {
            "repo_root": str(repo_root),
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "meta": meta,
        },
        "findings": findings,
    }
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
