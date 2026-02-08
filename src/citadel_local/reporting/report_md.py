from __future__ import annotations
from pathlib import Path
from datetime import datetime

def _sev_rank(sev: str) -> int:
    return {"critical": 0, "high": 1, "medium": 2, "low": 3, "info": 4}.get(sev, 9)

def write_report_md(path: Path, repo_root: Path, meta: dict, findings: list[dict]) -> None:
    findings_sorted = sorted(findings, key=lambda f: (_sev_rank(f.get("severity","info")), -float(f.get("confidence",0.0))))
    lines = []
    lines.append("# Security Report")
    lines.append("")
    lines.append(f"- Repo: `{repo_root}`")
    lines.append(f"- Generated: {datetime.utcnow().isoformat()}Z")
    lines.append(f"- Files scanned: {meta.get('file_count')}")
    lines.append("")

    if not findings_sorted:
        lines.append("No findings.")
        path.write_text("\n".join(lines), encoding="utf-8")
        return

    lines.append("## Findings")
    lines.append("")
    for idx, f in enumerate(findings_sorted, start=1):
        ev = f.get("evidence", {})
        lines.append(f"### {idx}. {f.get('title','Finding')}")
        lines.append(f"- Severity: **{f.get('severity','info')}**")
        lines.append(f"- Confidence: **{f.get('confidence',0.0)}**")
        lines.append(f"- Category: `{f.get('category','other')}`")
        lines.append(f"- Rule: `{f.get('rule_id','')}`")
        lines.append(f"- Location: `{ev.get('path','')}`:{ev.get('start_line','?')}")
        lines.append("")
        lines.append(f"{f.get('description','')}")
        lines.append("")
        lines.append("**Evidence (snippet):**")
        lines.append("```")
        lines.append(ev.get("snippet",""))
        lines.append("```")
        lines.append("")
        rec = f.get("recommendation") or []
        if rec:
            lines.append("**Recommendation:**")
            for r in rec:
                lines.append(f"- {r}")
            lines.append("")
        analysis = f.get("analysis") or {}
        if analysis:
            lines.append("**Fix plan (LLM-assisted):**")
            for step in (analysis.get("fix_plan") or []):
                lines.append(f"- {step}")
            lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")
