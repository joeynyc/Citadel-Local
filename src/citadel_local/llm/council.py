from __future__ import annotations
from pathlib import Path
import json
from .ollama_client import ollama_chat
from .prompts import TRIAGE_SYSTEM, DEEP_SYSTEM, SKEPTIC_SYSTEM, triage_user, deep_user, skeptic_user

def _extract_text(resp: dict) -> str:
    # Ollama chat response typically has: {"message": {"content": "..."}}
    return (resp.get("message") or {}).get("content") or ""

def _parse_json_maybe(s: str) -> dict:
    s = s.strip()
    try:
        return json.loads(s)
    except Exception:
        # If model returned extra text, try to salvage first JSON object
        start = s.find("{")
        end = s.rfind("}")
        if start != -1 and end != -1 and end > start:
            try:
                return json.loads(s[start:end+1])
            except Exception:
                return {"_raw": s}
        return {"_raw": s}

def run_council(repo_root: Path, meta: dict, candidates: list[dict], cfg: dict) -> list[dict]:
    oll = cfg.get("ollama", {})
    base_url = oll.get("base_url", "http://127.0.0.1:11434")
    triage_model = oll.get("triage_model", "llama3.2:3b")
    deep_model = oll.get("deep_model", "qwen3-coder:30b")
    skeptic_model = oll.get("skeptic_model", "gpt-oss:20b")
    timeout_s = int(oll.get("timeout_s", 90))

    out = []
    for f in candidates:
        # 1) triage
        tri = ollama_chat(base_url, triage_model, [
            {"role": "system", "content": TRIAGE_SYSTEM},
            {"role": "user", "content": triage_user(meta, f)}
        ], timeout_s=timeout_s)
        tri_json = _parse_json_maybe(_extract_text(tri))

        f["triage"] = {"model": triage_model, **tri_json}

        needs_deep = bool(tri_json.get("needs_deep_review", True))
        if needs_deep:
            deep = ollama_chat(base_url, deep_model, [
                {"role": "system", "content": DEEP_SYSTEM},
                {"role": "user", "content": deep_user(meta, f)}
            ], timeout_s=timeout_s)
            deep_json = _parse_json_maybe(_extract_text(deep))
            f["analysis"] = {"model": deep_model, **deep_json}

            sk = ollama_chat(base_url, skeptic_model, [
                {"role": "system", "content": SKEPTIC_SYSTEM},
                {"role": "user", "content": skeptic_user(meta, f)}
            ], timeout_s=timeout_s)
            sk_json = _parse_json_maybe(_extract_text(sk))
            f["skeptic"] = {"model": skeptic_model, **sk_json}

            # Merge severity/confidence conservatively
            sev = tri_json.get("severity")
            if isinstance(sk_json.get("recommendation"), str) and sk_json["recommendation"] in ("downgrade", "dismiss"):
                f["confidence"] = min(float(f.get("confidence", 0.5)), 0.4)
                if sev in ("critical", "high"):
                    f["severity"] = "medium"
        out.append(f)
    return out
