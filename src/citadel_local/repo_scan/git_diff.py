from __future__ import annotations
import subprocess
from pathlib import Path


def get_changed_files(repo: Path, base: str, cfg: dict) -> list[Path]:
    """Return absolute paths of files changed vs *base* branch, including uncommitted changes."""
    _check_git(repo)

    ignore = set(cfg.get("ignore", []))
    max_bytes = int(cfg.get("max_file_mb", 2)) * 1024 * 1024

    raw_paths: set[str] = set()

    # Committed changes vs base
    raw_paths.update(_git_diff_names(repo, f"{base}...HEAD"))
    # Staged (cached) changes
    raw_paths.update(_git_diff_names(repo, "--cached"))
    # Unstaged working-tree changes
    raw_paths.update(_git_diff_names(repo))

    raw_paths.discard("")

    files: list[Path] = []
    for rel_str in sorted(raw_paths):
        p = (repo / rel_str).resolve()
        if not p.is_file():
            continue
        rel = p.relative_to(repo)
        if any(part in ignore for part in rel.parts):
            continue
        try:
            if p.stat().st_size > max_bytes:
                continue
        except OSError:
            continue
        files.append(p)
    return files


def _git_diff_names(repo: Path, *extra_args: str) -> list[str]:
    cmd = ["git", "diff", "--name-only", *extra_args]
    result = subprocess.run(
        cmd, cwd=repo, capture_output=True, text=True, timeout=30,
    )
    if result.returncode != 0:
        return []
    return result.stdout.strip().splitlines()


def _check_git(repo: Path) -> None:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--is-inside-work-tree"],
            cwd=repo, capture_output=True, text=True, timeout=10,
        )
    except FileNotFoundError:
        raise RuntimeError("git is not available on PATH")
    if result.returncode != 0:
        raise RuntimeError(f"{repo} is not a git repository")
