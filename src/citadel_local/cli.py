import argparse
from pathlib import Path
from citadel_local.repo_scan.file_walk import collect_files
from citadel_local.repo_scan.git_diff import get_changed_files
from citadel_local.repo_scan.inventory import inventory_repo
from citadel_local.detectors import run_detectors
from citadel_local.reporting.report_json import write_findings_json
from citadel_local.reporting.report_md import write_report_md
from citadel_local.llm.council import run_council
from citadel_local.config import load_config

def cmd_scan(args: argparse.Namespace) -> int:
    repo = Path(args.path).resolve()
    out = Path(args.out).resolve()
    out.mkdir(parents=True, exist_ok=True)

    cfg = load_config(args.config)
    files = collect_files(repo, cfg)
    meta = inventory_repo(repo, files)
    candidates = run_detectors(repo, files, cfg)

    if cfg.get("ollama", {}).get("enabled", True):
        findings = run_council(repo, meta, candidates, cfg)
    else:
        findings = candidates  # deterministic-only mode

    findings_json = out / "findings.json"
    report_md = out / "report.md"
    write_findings_json(findings_json, repo, meta, findings)
    write_report_md(report_md, repo, meta, findings)
    print(f"Wrote: {findings_json}")
    print(f"Wrote: {report_md}")
    return 0

def cmd_diff(args: argparse.Namespace) -> int:
    repo = Path(args.path).resolve()
    out = Path(args.out).resolve()
    out.mkdir(parents=True, exist_ok=True)

    cfg = load_config(args.config)
    files = get_changed_files(repo, args.base, cfg)
    print(f"Changed files: {len(files)}")
    if not files:
        print("No changed files to scan.")
        return 0

    meta = inventory_repo(repo, files)
    candidates = run_detectors(repo, files, cfg)

    if cfg.get("ollama", {}).get("enabled", True):
        findings = run_council(repo, meta, candidates, cfg)
    else:
        findings = candidates

    findings_json = out / "findings.json"
    report_md = out / "report.md"
    write_findings_json(findings_json, repo, meta, findings)
    write_report_md(report_md, repo, meta, findings)
    print(f"Wrote: {findings_json}")
    print(f"Wrote: {report_md}")
    return 0

def main() -> None:
    p = argparse.ArgumentParser(prog="citadel")
    sub = p.add_subparsers(dest="cmd", required=True)

    scan = sub.add_parser("scan", help="Scan a repo folder")
    scan.add_argument("path")
    scan.add_argument("--out", default="out")
    scan.add_argument("--config", default=".citadel-local.yaml")
    scan.set_defaults(func=cmd_scan)

    # Stubs for v1 roadmap
    diff = sub.add_parser("diff", help="Scan only changed files vs git base")
    diff.add_argument("path")
    diff.add_argument("--base", default="origin/main")
    diff.add_argument("--out", default="out")
    diff.add_argument("--config", default=".citadel-local.yaml")
    diff.set_defaults(func=cmd_diff)

    baseline = sub.add_parser("baseline", help="Record baseline findings (stub)")
    baseline.add_argument("path")
    baseline.add_argument("--out", default="baseline.json")
    baseline.add_argument("--config", default=".citadel-local.yaml")
    baseline.set_defaults(func=lambda a: (print("baseline: stub (write findings as baseline)"), 0)[1])

    report = sub.add_parser("report", help="Render markdown report from findings.json (stub)")
    report.add_argument("findings_json")
    report.add_argument("--out", default="report.md")
    report.set_defaults(func=lambda a: (print("report: stub (read findings.json and render md)"), 0)[1])

    args = p.parse_args()
    raise SystemExit(args.func(args))

if __name__ == "__main__":
    main()
