from __future__ import annotations
from pathlib import Path

def collect_files(repo_root: Path, cfg: dict) -> list[Path]:
    ignore = set(cfg.get("ignore", []))
    max_bytes = int(cfg.get("max_file_mb", 2)) * 1024 * 1024
    files: list[Path] = []
    for p in repo_root.rglob("*"):
        if p.is_dir():
            continue
        rel = p.relative_to(repo_root)
        if any(part in ignore for part in rel.parts):
            continue
        try:
            if p.stat().st_size > max_bytes:
                continue
        except OSError:
            continue
        files.append(p)
    return files
