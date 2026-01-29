from __future__ import annotations
import json

TRIAGE_SYSTEM = (
    "You are a defensive code auditor. Be conservative. "
    "Do not invent evidence. Output valid JSON only."
)

DEEP_SYSTEM = (
    "You are a defensive code auditor. "
    "Do NOT provide exploit payloads or instructions for attacking systems. "
    "Focus on root cause and remediation. Output valid JSON only."
)

SKEPTIC_SYSTEM = (
    "You are a skeptical reviewer. Try to disprove the finding unless evidence is strong. "
    "Do not invent evidence. Output valid JSON only."
)

def _policy():
    return {"defensive_only": True, "no_exploit_payloads": True}

def triage_user(repo_context: dict, finding: dict) -> str:
    payload = {"repo_context": repo_context, "finding": finding, "policy": _policy()}
    return json.dumps(payload, ensure_ascii=False)

def deep_user(repo_context: dict, finding: dict) -> str:
    payload = {"repo_context": repo_context, "finding": finding, "policy": _policy()}
    return json.dumps(payload, ensure_ascii=False)

def skeptic_user(repo_context: dict, finding: dict) -> str:
    payload = {"repo_context": repo_context, "finding": finding, "policy": _policy()}
    return json.dumps(payload, ensure_ascii=False)
