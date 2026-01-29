from __future__ import annotations
from pathlib import Path
from collections import Counter

def inventory_repo(repo_root: Path, files: list[Path]) -> dict:
    exts = [p.suffix.lower() for p in files if p.suffix]
    common = Counter(exts).most_common(20)
    return {
        "repo_root": str(repo_root),
        "file_count": len(files),
        "top_extensions": common,
        "has_docker": any(p.name in ("Dockerfile", "docker-compose.yml", "docker-compose.yaml") for p in files),
        "has_github_actions": any(".github/workflows" in str(p) for p in files),
        "has_env_files": any(p.name in (".env", ".env.local", ".env.production") for p in files),
    }
