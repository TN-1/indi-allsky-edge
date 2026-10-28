# AGENTS.md — Operational Manual for AI Agents & Developers

This document serves as the authoritative operational manual for autonomous agents and human developers maintaining **`indi-allsky-edge`**. 

Read this manual before executing any operations, modifying integration manifests, or resolving conflicts.

---

## 1. System Architecture & Core Axioms

`indi-allsky-edge` is an **automated integration distribution (soft fork)** of `aaronwmorris/indi-allsky`.

### Axiom 1: Dual-Branch Separation
* **Branch `main` (The Orchestrator)**:
  * Persistent, permanent branch.
  * Contains **only** automation machinery: `manifest.yaml`, `rebuild.py`, `rr-cache/`, and `.github/workflows/`.
  * Does **not** contain application source code.
* **Branch `edge` (The Ephemeral Target)**:
  * Destroyed and reconstructed deterministically on every build.
  * Formed by taking `upstream/main` and sequentially merging the PRs and topic branches declared in `manifest.yaml`.
  * Modified with package metadata (`Package: indi-allsky-edge`).
  * Pushed automatically by CI. **Never commit directly to `edge`.**

### Axiom 2: Upstream-First Philosophy
* All features and bug fixes originate from pull requests submitted to `aaronwmorris/indi-allsky`.
* Maintainers must not encourage users to file bugs upstream. All edge issues are routed to `TN-1/indi-allsky-edge`.

---

## 2. Directory Layout & File Roles

```
.
├── .github/workflows/
│   └── build-edge.yml       # GitHub Actions workflow: runs Stage 1 (rebuild.py) and Stage 2 (dpkg-buildpackage)
├── manifest.yaml            # Declarative list of pull requests, external branches, and glue patches
├── rebuild.py               # Deterministic Python synthesis engine
├── rr-cache/                # Tracked Git rerere database (records manual conflict resolutions)
├── AGENTS.md                # This operational guide
├── README.md                # User-facing documentation and installation instructions
└── .gitignore               # Ignores workspace/, build artifacts, and virtual environments
```

---

## 3. Standard Operational Workflows

### Workflow A: Adding a Pull Request to `edge`
When an upstream PR (or new topic branch) is ready to be included in the edge build:

1. **Verify the PR Status**:
   Inspect the pull request in `aaronwmorris/indi-allsky` using GitHub CLI:
   ```bash
   gh pr view <PR_NUMBER> -R aaronwmorris/indi-allsky
   ```
2. **Update `manifest.yaml`**:
   Add an entry under `pull_requests`:
   ```yaml
   - id: 3324
     title: "fix(driver): address camera buffer timeout"
     author: "username"
   ```
   * All merges operate under **Graceful Exclusion**: if a PR merges cleanly, it is integrated into `edge`. If it encounters a merge conflict, it is logged and skipped without halting the build.
   * If a pull request has a noted conflict in GitHub UI against upstream/main, omit it from `manifest.yaml` until the author resolves it. If it only conflicts upon cumulative integration into `edge`, resolve it via `rr-cache/` or a glue patch.
3. **Test the Integration Locally**:
   ```bash
   python3 rebuild.py --workspace workspace --no-transform
   ```
4. **Stage and Commit on `main`**:
   ```bash
   git add manifest.yaml
   git commit -m "feat(manifest): add PR #3324 to edge distribution"
   git push origin main
   ```

---

### Workflow B: Upstream Merges or Closes a PR (Pruning)
When Aaron merges an upstream PR into `upstream/main`, or a PR is rejected/closed:

1. `rebuild.py` automatically detects when a PR is an ancestor of `upstream/main` and reports `[Already upstream]`.
2. To keep `manifest.yaml` pristine, delete the entry corresponding to that PR from `manifest.yaml`.
3. Commit and push to `main`:
   ```bash
   git add manifest.yaml
   git commit -m "chore(manifest): remove merged PR #3304 (absorbed into upstream/main)"
   git push origin main
   ```

---

### Workflow C: Diagnosing and Resolving Merge Conflicts (The 4 Tiers)

If CI reports that a PR was excluded due to a merge conflict, execute the resolution sequence:

#### Step 1: Reproduce Locally
Run the synthesis engine locally to reproduce the exact conflict state:
```bash
python3 rebuild.py --workspace workspace
```
The script will halt at the conflicting commit in `./workspace`.

#### Step 2: Determine Conflict Tier

* **Tier 1: Asset / Lockfile Conflict**
  * If the conflict is in `indi_allsky/flask/static/css/dist.css`:
    ```bash
    cd workspace
    npm run build
    git add indi_allsky/flask/static/css/dist.css
    git commit --no-edit
    ```
  * If in `package-lock.json`:
    ```bash
    cd workspace
    git checkout --ours package-lock.json
    git add package-lock.json
    git commit --no-edit
    ```

* **Tier 2: Code Logic Conflict (Using Git `rerere`)**
  If two PRs touch the same lines in `views.py` or `forms.py`:
  1. Ensure `rerere` is active in `workspace`:
     ```bash
     cd workspace
     git config rerere.enabled true
     git config rerere.autoupdate true
     ```
  2. Open the conflicting file in an editor. Resolve the conflict markers (`<<<<<<<`, `=======`, `>>>>>>>`).
  3. Stage and commit the resolution in `workspace`:
     ```bash
     git add indi_allsky/flask/views.py
     git commit --no-edit
     ```
  4. Export the newly recorded resolution hash from `workspace/.git/rr-cache/` to the root repository:
     ```bash
     cd ..
     cp -r workspace/.git/rr-cache/* ./rr-cache/
     git add rr-cache/
     git commit -m "chore(rerere): record conflict resolution for PR #X and #Y"
     git push origin main
     ```
  5. In all future CI runs, Git will automatically apply this resolution without pausing.

* **Tier 3: Complex Architectural Differences (Glue Patch)**
  If two PRs require substantial adapter glue code:
  1. Create a patch file in `patches/` (e.g. `patches/reconcile-feature-x.patch`).
  2. Declare the patch in `manifest.yaml` under `reconciliation_patches`.
  3. `rebuild.py` will apply it via `git apply` immediately after the conflicting PRs merge.

* **Tier 4: Graceful Exclusion (Failsafe)**
  If a PR cannot be easily resolved and you lack time, simply leave it in `manifest.yaml` without a resolution. The synthesis engine will automatically skip it upon encountering a conflict, allowing all other PRs to compile and release without interruption.

---

### Workflow D: Running Containerized QA Validation
To verify that the synthesized `edge` branch compiles and runs all tests inside a Debian container:

```bash
cd workspace
# Build Debian package
dpkg-buildpackage -us -uc -b

# Run authenticated route and WSGI loopback tests
bash debian/tests/qa_test.sh
```

---

## 4. Operational Guardrails for AI Agents

1. **Never attempt a git commit on the `edge` branch directly.** Always commit configuration, manifests, or resolutions to `main`.
2. **Never push directly to `aaronwmorris/indi-allsky`.** All development occurs in `TN-1/indi-allsky` feature branches or `TN-1/indi-allsky-edge`.
3. **Preserve author integrity.** When merging community PRs, never squash or re-author external commits; preserve original author metadata.
4. **Do not create GitHub Pull Requests unless explicitly requested by the operator.**
5. **Do not bypass Debian packaging checks.** Always ensure `debian/control` maintains:
   ```control
   Package: indi-allsky-edge
   Provides: indi-allsky (= ${binary:Version})
   Conflicts: indi-allsky
   Replaces: indi-allsky
   ```
