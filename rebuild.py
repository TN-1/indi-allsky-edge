#!/usr/bin/env python3
"""
indi-allsky-edge Rebuild & Synthesis Engine

Deterministic builder that aggregates upstream/main with a curated manifest
of pull requests and topic branches to synthesize the ephemeral 'edge' branch.
All merges operate with graceful exclusion: clean merges are integrated;
conflicts are logged and skipped without halting the pipeline.
"""

from __future__ import annotations

import argparse
from datetime import datetime
from pathlib import Path
import re
import shutil
import subprocess
import sys
import yaml


def run_command(cmd: list[str], cwd: Path | None = None, check: bool = True) -> subprocess.CompletedProcess[str]:
    """Execute a subprocess command returning stdout."""
    res = subprocess.run(
        cmd,
        cwd=str(cwd) if cwd else None,
        check=check,
        capture_output=True,
        text=True,
    )
    return res


def load_manifest(manifest_path: Path) -> dict:
    if not manifest_path.exists():
        raise FileNotFoundError(f"Manifest not found: {manifest_path}")
    with open(manifest_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def setup_workspace(workspace_dir: Path, upstream_url: str, default_branch: str) -> None:
    """Initialize or update the target git repository workspace."""
    workspace_dir.parent.mkdir(parents=True, exist_ok=True)
    if not (workspace_dir / ".git").exists():
        print(f"Cloning upstream repository into {workspace_dir}...")
        run_command(["git", "clone", upstream_url, str(workspace_dir)])
    else:
        print(f"Workspace already exists at {workspace_dir}. Fetching remotes...")

    # Configure git remotes
    remotes = run_command(["git", "remote"], cwd=workspace_dir).stdout.splitlines()
    if "upstream" not in remotes:
        run_command(["git", "remote", "add", "upstream", upstream_url], cwd=workspace_dir)
    else:
        run_command(["git", "remote", "set-url", "upstream", upstream_url], cwd=workspace_dir)

    run_command(["git", "fetch", "upstream", default_branch], cwd=workspace_dir)


def configure_rerere(workspace_dir: Path, rr_cache_source: Path) -> None:
    """Configure Git rerere and pre-seed cached conflict resolutions."""
    run_command(["git", "config", "rerere.enabled", "true"], cwd=workspace_dir)
    run_command(["git", "config", "rerere.autoupdate", "true"], cwd=workspace_dir)

    target_rr_cache = workspace_dir / ".git" / "rr-cache"
    target_rr_cache.mkdir(parents=True, exist_ok=True)

    if rr_cache_source.exists() and any(rr_cache_source.iterdir()):
        print(f"Seeding {len(list(rr_cache_source.iterdir()))} cached conflict resolutions...")
        for item in rr_cache_source.iterdir():
            if item.is_dir():
                dest = target_rr_cache / item.name
                if dest.exists():
                    shutil.rmtree(dest)
                shutil.copytree(item, dest)


def sync_back_rerere(workspace_dir: Path, rr_cache_target: Path) -> None:
    """Persist any new rerere resolutions recorded during merge into source directory."""
    source_rr_cache = workspace_dir / ".git" / "rr-cache"
    if not source_rr_cache.exists():
        return

    rr_cache_target.mkdir(parents=True, exist_ok=True)
    count = 0
    for item in source_rr_cache.iterdir():
        if item.is_dir():
            dest = rr_cache_target / item.name
            if not dest.exists():
                shutil.copytree(item, dest)
                count += 1
    if count > 0:
        print(f"Captured {count} new resolution(s) in {rr_cache_target}.")


def write_composition_manifest(
    workspace_dir: Path,
    upstream_repo: str,
    upstream_branch: str,
    upstream_sha: str,
    upstream_msg: str,
    upstream_date: str,
    integrated_prs: list[dict],
    integrated_branches: list[dict],
    applied_patches: list[dict],
    excluded_items: list[str],
) -> Path:
    """Generate structured markdown manifest recording exact base commit and integrated items."""
    lines = [
        "## `indi-allsky-edge` Build Composition\n",
        "This release is an automated bleeding edge distribution aggregating pending pull requests on top of the official upstream repository. It is mainly for testing purposes, and previewing upcoming features. Please do not report issues with this build on aaronwmorris/indi-allsky.\n",
        "### Base Upstream Reference",
        f"* **Repository**: [{upstream_repo}](https://github.com/{upstream_repo})",
        f"* **Branch**: `{upstream_branch}`",
        f"* **Base Commit**: [`{upstream_sha[:8]}`](https://github.com/{upstream_repo}/commit/{upstream_sha}) – *\"{upstream_msg}\"* ({upstream_date})\n",
        f"### Integrated Pull Requests ({len(integrated_prs)})\n",
        "| PR | Title | Author | Status |",
        "|:---|:---|:---|:---|",
    ]

    for pr in integrated_prs:
        pr_id = pr["id"]
        pr_title = pr["title"].replace("|", "\\|")
        author = pr.get("author", "Unknown")
        author_link = f"[@{author}](https://github.com/{author})" if author != "Unknown" else "Unknown"
        pr_link = f"[#{pr_id}](https://github.com/{upstream_repo}/pull/{pr_id})"
        lines.append(f"| {pr_link} | {pr_title} | {author_link} | {pr['status']} |")

    if integrated_branches:
        lines.extend([
            f"\n### Integrated External Branches ({len(integrated_branches)})\n",
            "| Branch | Repository | Description | Status |",
            "|:---|:---|:---|:---|",
        ])
        for b in integrated_branches:
            b_name = b["branch"]
            b_repo = b["repo"]
            b_title = b["title"].replace("|", "\\|")
            lines.append(f"| `{b_name}` | [{b_repo}]({b_repo}) | {b_title} | {b['status']} |")

    if applied_patches:
        lines.extend([
            f"\n### Applied Reconciliation Glue Patches ({len(applied_patches)})\n",
            "| Patch | Description |",
            "|:---|:---|",
        ])
        for p in applied_patches:
            lines.append(f"| `{p['file']}` | {p['desc']} |")

    if excluded_items:
        lines.extend([
            f"\n### Excluded Items ({len(excluded_items)})\n",
            "| Item |",
            "|:---|",
        ])
        for ex in excluded_items:
            lines.append(f"| {ex.replace('|', '\\|')} |")

    manifest_md = workspace_dir / "EDGE_COMPOSITION.md"
    manifest_md.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return manifest_md


def main() -> int:
    parser = argparse.ArgumentParser(description="indi-allsky-edge Rebuild Engine")
    parser.add_argument("--manifest", type=Path, default=Path("manifest.yaml"), help="Path to manifest.yaml")
    parser.add_argument("--workspace", type=Path, default=Path("workspace"), help="Workspace directory for git build")
    parser.add_argument("--target-branch", type=str, default="edge", help="Target branch name")
    parser.add_argument("--push", action="store_true", help="Push target branch to origin")
    args = parser.parse_args()

    manifest_file = args.manifest.resolve()
    manifest = load_manifest(manifest_file)
    workspace = args.workspace.resolve()
    rr_cache_dir = manifest_file.parent / "rr-cache"

    upstream_repo = manifest["upstream"]["repo"]
    upstream_url = f"https://github.com/{upstream_repo}.git"
    default_branch = manifest["upstream"].get("default_branch", "main")
    package_name = manifest.get("package", {}).get("name", "indi-allsky-edge")

    print("==================================================================")
    print(f"=== Reconstructing {args.target_branch} from {upstream_repo} ===")
    print("==================================================================")

    setup_workspace(workspace, upstream_url, default_branch)
    configure_rerere(workspace, rr_cache_dir)

    # Reset target branch to upstream default
    print(f"Resetting '{args.target_branch}' to upstream/{default_branch}...")
    run_command(["git", "checkout", "-B", args.target_branch, f"upstream/{default_branch}"], cwd=workspace)

    upstream_sha = run_command(["git", "rev-parse", f"upstream/{default_branch}"], cwd=workspace).stdout.strip()
    upstream_msg = run_command(["git", "log", "-1", "--format=%s", upstream_sha], cwd=workspace).stdout.strip()
    upstream_date = run_command(["git", "log", "-1", "--format=%cd", "--date=short", upstream_sha], cwd=workspace).stdout.strip()

    integrated: list[str] = []
    excluded: list[str] = []
    integrated_prs: list[dict] = []
    integrated_branches: list[dict] = []
    applied_patches: list[dict] = []

    # 1. Integrate Upstream Pull Requests
    pull_requests = manifest.get("pull_requests", [])
    for pr in pull_requests:
        pr_id = pr["id"]
        title = pr.get("title", f"PR #{pr_id}")

        print(f"\n--> Evaluating PR #{pr_id}: {title}")
        fetch_res = run_command(
            ["git", "fetch", "upstream", f"pull/{pr_id}/head:pr-{pr_id}"],
            cwd=workspace,
            check=False,
        )
        if fetch_res.returncode != 0:
            print(f"Warning: Failed to fetch PR #{pr_id} from upstream. Skipping.")
            excluded.append(f"PR #{pr_id} (Fetch failed)")
            continue

        # Check if already in history
        check_merged = run_command(
            ["git", "merge-base", "--is-ancestor", f"pr-{pr_id}", "HEAD"],
            cwd=workspace,
            check=False,
        )
        if check_merged.returncode == 0:
            print(f"PR #{pr_id} is already merged in upstream history. Skipping.")
            integrated.append(f"PR #{pr_id} (Already upstream)")
            integrated_prs.append({"id": pr_id, "title": title, "author": pr.get("author", "Unknown"), "status": "Already upstream"})
            continue

        # Attempt merge
        merge_cmd = ["git", "merge", "--no-ff", "--no-edit", f"pr-{pr_id}", "-m", f"Merge PR #{pr_id}: {title}"]
        merge_res = run_command(merge_cmd, cwd=workspace, check=False)

        if merge_res.returncode == 0:
            print(f"Successfully integrated PR #{pr_id}.")
            integrated.append(f"PR #{pr_id}: {title}")
            integrated_prs.append({"id": pr_id, "title": title, "author": pr.get("author", "Unknown"), "status": "Clean merge"})
        else:
            print(f"Merge conflict encountered in PR #{pr_id}.")
            status_res = run_command(["git", "status", "--porcelain"], cwd=workspace, check=False)
            unmerged = [line for line in status_res.stdout.splitlines() if line.startswith("UU") or line.startswith("AA")]

            if not unmerged:
                print("All conflicts resolved automatically via git rerere. Committing merge...")
                run_command(["git", "commit", "--no-edit"], cwd=workspace)
                integrated.append(f"PR #{pr_id} (Resolved via rerere)")
                integrated_prs.append({"id": pr_id, "title": title, "author": pr.get("author", "Unknown"), "status": "Resolved via rerere"})
            else:
                run_command(["git", "merge", "--abort"], cwd=workspace, check=False)
                print(f"Graceful Exclusion: Skipping PR #{pr_id} to maintain build continuity.")
                excluded.append(f"PR #{pr_id}: {title} (Conflict on {len(unmerged)} file(s))")

    # 2. Integrate External Branches
    external_refs = manifest.get("external_refs", [])
    for ext in external_refs:
        repo_url = ext["repo"]
        branch_name = ext["branch"]
        title = ext.get("title", f"{repo_url}@{branch_name}")

        print(f"\n--> Evaluating External Branch: {branch_name} ({title})")
        fetch_res = run_command(["git", "fetch", repo_url, f"{branch_name}:ext-{branch_name}"], cwd=workspace, check=False)
        if fetch_res.returncode != 0:
            print(f"Warning: Failed to fetch external branch '{branch_name}'. Skipping.")
            excluded.append(f"External {branch_name} (Fetch failed)")
            continue

        merge_cmd = ["git", "merge", "--no-ff", "--no-edit", f"ext-{branch_name}", "-m", f"Merge external branch '{branch_name}': {title}"]
        merge_res = run_command(merge_cmd, cwd=workspace, check=False)

        if merge_res.returncode == 0:
            print(f"Successfully integrated external branch '{branch_name}'.")
            integrated.append(f"External {branch_name}: {title}")
            integrated_branches.append({"branch": branch_name, "repo": repo_url, "title": title, "status": "Clean merge"})
        else:
            run_command(["git", "merge", "--abort"], cwd=workspace, check=False)
            print(f"Graceful Exclusion: Skipping external branch '{branch_name}'.")
            excluded.append(f"External {branch_name} (Conflict)")

    # 3. Apply Post-Merge Reconciliation Glue Patches
    patches = manifest.get("reconciliation_patches", [])
    for patch_info in patches:
        patch_file = manifest_file.parent / patch_info["file"]
        desc = patch_info.get("description", patch_file.name)
        print(f"\n--> Applying glue patch: {desc}")
        apply_res = run_command(["git", "apply", str(patch_file)], cwd=workspace, check=False)
        if apply_res.returncode == 0:
            run_command(["git", "commit", "-am", f"chore(reconciliation): {desc}"], cwd=workspace)
            integrated.append(f"Patch: {desc}")
            applied_patches.append({"file": patch_info["file"], "desc": desc})
        else:
            print(f"Warning: Failed to apply glue patch: {patch_file}. Skipping.")
            excluded.append(f"Patch {patch_file.name} (Apply failed)")

    # 4. Generate Build Composition Manifest
    print("\n--> Generating EDGE_COMPOSITION.md manifest...")
    write_composition_manifest(
        workspace,
        upstream_repo,
        default_branch,
        upstream_sha,
        upstream_msg,
        upstream_date,
        integrated_prs,
        integrated_branches,
        applied_patches,
        excluded,
    )
    run_command(["git", "add", "EDGE_COMPOSITION.md"], cwd=workspace)
    run_command(
        ["git", "commit", "-m", "chore(metadata): record edge build composition manifest"],
        cwd=workspace,
    )

    # 5. Capture new rerere resolutions
    sync_back_rerere(workspace, rr_cache_dir)

    print("\n==================================================================")
    print("=== Synthesis Summary ===")
    print("==================================================================")
    print(f"Integrated Items ({len(integrated)}):")
    for item in integrated:
        print(f"  [+] {item}")
    if excluded:
        print(f"\nExcluded Items ({len(excluded)}):")
        for item in excluded:
            print(f"  [-] {item}")
    print("==================================================================")

    if args.push:
        print(f"Pushing '{args.target_branch}' to origin...")
        run_command(["git", "push", "--force-with-lease", "origin", args.target_branch], cwd=workspace)

    return 0


if __name__ == "__main__":
    sys.exit(main())
