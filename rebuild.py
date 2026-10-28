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


def transform_package_metadata(workspace_dir: Path, package_name: str) -> None:
    """Transform debian packaging metadata from indi-allsky to indi-allsky-edge."""
    control_path = workspace_dir / "debian" / "control"
    if not control_path.exists():
        print("Warning: debian/control not found, skipping package transform.")
        return

    content = control_path.read_text(encoding="utf-8")
    if f"Package: {package_name}" not in content:
        print(f"Transforming package identity to '{package_name}'...")
        replacement = (
            f"Package: {package_name}\n"
            f"Provides: indi-allsky (= ${{binary:Version}})\n"
            f"Conflicts: indi-allsky\n"
            f"Replaces: indi-allsky"
        )
        content = re.sub(r"^Package:\s+indi-allsky$", replacement, content, flags=re.MULTILINE)
        control_path.write_text(content, encoding="utf-8")

    # Stamp changelog version
    changelog_path = workspace_dir / "debian" / "changelog"
    timestamp = datetime.now().strftime("%Y%m%d.%H%M")
    base_version = "2026.09.01"

    bump_script = workspace_dir / "misc" / "bump_version.py"
    if bump_script.exists():
        try:
            res = run_command([sys.executable, str(bump_script), "--show"], cwd=workspace_dir, check=False)
            if res.returncode == 0 and res.stdout.strip():
                base_version = res.stdout.strip().split()[-1]
        except Exception:
            pass

    edge_version = f"{base_version}~edge.{timestamp}"
    rfc_date = datetime.now().strftime("%a, %d %b %Y %H:%M:%S +0000")

    changelog_entry = (
        f"{package_name} ({edge_version}) edge; urgency=medium\n\n"
        f"  * Automated edge distribution build from PR manifest.\n\n"
        f" -- indi-allsky-edge CI <ci@indi-allsky-edge.internal>  {rfc_date}\n\n"
    )

    if changelog_path.exists():
        old_changelog = changelog_path.read_text(encoding="utf-8")
        changelog_path.write_text(changelog_entry + old_changelog, encoding="utf-8")
    else:
        changelog_path.write_text(changelog_entry, encoding="utf-8")

    run_command(["git", "add", "debian/control", "debian/changelog"], cwd=workspace_dir)
    run_command(
        ["git", "commit", "-m", f"chore(packaging): configure {package_name} {edge_version} metadata"],
        cwd=workspace_dir,
    )
    print(f"Package stamped as: {package_name} ({edge_version})")


def main() -> int:
    parser = argparse.ArgumentParser(description="indi-allsky-edge Rebuild Engine")
    parser.add_argument("--manifest", type=Path, default=Path("manifest.yaml"), help="Path to manifest.yaml")
    parser.add_argument("--workspace", type=Path, default=Path("workspace"), help="Workspace directory for git build")
    parser.add_argument("--target-branch", type=str, default="edge", help="Target branch name")
    parser.add_argument("--no-transform", action="store_true", help="Skip debian packaging metadata transformation")
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

    integrated: list[str] = []
    excluded: list[str] = []

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
            continue

        # Attempt merge
        merge_cmd = ["git", "merge", "--no-ff", "--no-edit", f"pr-{pr_id}", "-m", f"Merge PR #{pr_id}: {title}"]
        merge_res = run_command(merge_cmd, cwd=workspace, check=False)

        if merge_res.returncode == 0:
            print(f"Successfully integrated PR #{pr_id}.")
            integrated.append(f"PR #{pr_id}: {title}")
        else:
            print(f"Merge conflict encountered in PR #{pr_id}.")
            status_res = run_command(["git", "status", "--porcelain"], cwd=workspace, check=False)
            unmerged = [line for line in status_res.stdout.splitlines() if line.startswith("UU") or line.startswith("AA")]

            if not unmerged:
                print("All conflicts resolved automatically via git rerere. Committing merge...")
                run_command(["git", "commit", "--no-edit"], cwd=workspace)
                integrated.append(f"PR #{pr_id} (Resolved via rerere)")
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
        else:
            print(f"Warning: Failed to apply glue patch: {patch_file}. Skipping.")
            excluded.append(f"Patch {patch_file.name} (Apply failed)")

    # 4. Transform Package Metadata
    if not args.no_transform:
        transform_package_metadata(workspace, package_name)

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
