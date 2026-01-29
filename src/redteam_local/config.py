from __future__ import annotations
from pathlib import Path
import yaml

DEFAULTS = {
  "ignore": ["node_modules", ".git", "dist", "build", "vendor", ".venv"],
  "max_file_mb": 2,
  "context_lines": 40,
  "ollama": {
    "enabled": True,
    "base_url": "http://127.0.0.1:11434",
    "triage_model": "llama3.2:3b",
    "deep_model": "qwen3-coder:30b",
    "skeptic_model": "gpt-oss:20b",
    "timeout_s": 90
  }
}

def load_config(path: str) -> dict:
    p = Path(path)
    if not p.exists():
        return DEFAULTS
    data = yaml.safe_load(p.read_text(encoding="utf-8")) or {}
    # shallow merge
    cfg = {**DEFAULTS, **data}
    cfg["ollama"] = {**DEFAULTS["ollama"], **(data.get("ollama") or {})}
    return cfg
