#!/usr/bin/env python3
import sys
import os
import yaml
from pathlib import Path

SMELLS = ["S1_FLOATING_TAG", "S2_MISSING_TIMEOUT", "S3_BROAD_PERMISSIONS"]

FLOATING_REFS = {"main", "master", "dev", "develop", "head"}

def is_yaml(path: Path) -> bool:
    return path.suffix in {".yml", ".yaml"}

def iter_workflow_files(repo_root: Path):
    wf_dir = repo_root / ".github" / "workflows"
    if not wf_dir.exists():
        return
    for p in wf_dir.rglob("*"):
        if p.is_file() and is_yaml(p):
            yield p

def load_yaml(path: Path):
    try:
        with path.open("r", encoding="utf-8") as f:
            return yaml.safe_load(f)
    except Exception as e:
        print(f"[WARN] Failed to parse {path}: {e}")
        return None

def detect_floating_tags(uses_value: str):
    if "@" not in uses_value:
        # no ref => treat as floating
        return True, "<none>"
    action, ref = uses_value.split("@", 1)
    ref_clean = ref.strip().lower()
    if ref_clean in FLOATING_REFS:
        return True, ref
    # very simple heuristic: if ref looks like vX or vX.Y, treat as pinned
    if ref_clean.startswith("v") and any(ch.isdigit() for ch in ref_clean):
        return False, ref
    # everything else we'll treat as okay for now
    return False, ref

def detect_broad_permissions(perm_dict: dict):
    if not isinstance(perm_dict, dict):
        return False
    # very simple: any write permission counts as broad for demo purposes
    for scope, value in perm_dict.items():
        if isinstance(value, str) and value.lower() == "write":
            return True
    return False

def analyze_workflow(path: Path):
    data = load_yaml(path)
    findings = []

    if not isinstance(data, dict):
        return findings

    jobs = data.get("jobs", {}) or {}
    wf_permissions = data.get("permissions", {})

    # S3 at workflow level
    if detect_broad_permissions(wf_permissions):
        findings.append({
            "smell": "S3_BROAD_PERMISSIONS",
            "file": str(path),
            "where": "workflow",
            "details": f"workflow-level permissions={wf_permissions}"
        })

    for job_name, job in jobs.items():
        if not isinstance(job, dict):
            continue

        # S2: missing timeout-minutes
        if "timeout-minutes" not in job:
            findings.append({
                "smell": "S2_MISSING_TIMEOUT",
                "file": str(path),
                "where": f"job:{job_name}",
                "details": "job has no timeout-minutes"
            })

        # Job-level permissions (S3)
        job_perms = job.get("permissions", {})
        if detect_broad_permissions(job_perms):
            findings.append({
                "smell": "S3_BROAD_PERMISSIONS",
                "file": str(path),
                "where": f"job:{job_name}",
                "details": f"job permissions={job_perms}"
            })

        # Steps for S1
        steps = job.get("steps", []) or []
        for idx, step in enumerate(steps):
            if not isinstance(step, dict):
                continue
            uses = step.get("uses")
            if not uses:
                continue
            is_smell, ref = detect_floating_tags(uses)
            if is_smell:
                findings.append({
                    "smell": "S1_FLOATING_TAG",
                    "file": str(path),
                    "where": f"job:{job_name}:step:{idx}",
                    "details": f"uses={uses}"
                })

    return findings

def summarize(findings):
    summary = {s: 0 for s in SMELLS}
    for f in findings:
        summary[f["smell"]] += 1
    return summary

def main():
    if len(sys.argv) != 2:
        print("Usage: python gha_smell_detector.py /path/to/repo")
        sys.exit(1)

    repo_root = Path(sys.argv[1]).resolve()
    if not repo_root.exists():
        print(f"Path does not exist: {repo_root}")
        sys.exit(1)

    all_findings = []
    for wf in iter_workflow_files(repo_root):
        wf_findings = analyze_workflow(wf)
        all_findings.extend(wf_findings)

    # Print detailed findings
    repo_name = repo_root.name
    for f in all_findings:
        try:
            rel_path = os.path.relpath(f["file"], repo_root)
        except Exception:
            # Fallback, should not normally happen
            rel_path = f["file"]
        pretty_path = f"{repo_name}/{rel_path}"
        print(f"[{f['smell']}] {pretty_path}\n {f['where']} :: {f['details']}")

    # Print summary
    summary = summarize(all_findings)
    print("\nSummary:")
    for smell, count in summary.items():
        print(f"  {smell}: {count}")

    # Basic suggestions
    print("\nBasic Fix Suggestions:")
    print("  S1_FLOATING_TAG      -> Pin action to a stable tag or commit SHA")
    print("  S2_MISSING_TIMEOUT   -> Add 'timeout-minutes: <value>' at job level")
    print("  S3_BROAD_PERMISSIONS -> Restrict permissions to minimum required scopes")

if __name__ == "__main__":
    main()
