# indi-allsky-edge (Community Bleeding Edge Distribution)

`indi-allsky-edge` is an automated, upstream-first integration distribution of [indi-allsky](https://github.com/aaronwmorris/indi-allsky).

It aggregates the latest upstream trunk with validated community pull requests, hardware drivers, and critical bugfixes that are awaiting upstream review, compiling them nightly into installable Debian packages.

---

### Upstream-First Charter

1. **Not a Hard Fork**: This repository does not represent a divergent project. Every enhancement and bugfix incorporated here originates from a pull request submitted to [aaronwmorris/indi-allsky](https://github.com/aaronwmorris/indi-allsky).
2. **Field Validation**: The express objective of `indi-allsky-edge` is to provide real-world observatory testing for pending patches, establishing empirical stability data to assist upstream review.
3. **Strict Support Boundaries**: If you run `indi-allsky-edge`, **do not file bug reports on Aaron's upstream repository**. All issues, anomalies, or questions regarding edge builds must be submitted to the [indi-allsky-edge Issue Tracker](https://github.com/TN-1/indi-allsky-edge/issues).

---

### Package Architecture & Drop-In Interoperability

The compiled package is designated `indi-allsky-edge`. It declares full Debian drop-in replacement compatibility:

```control
Package: indi-allsky-edge
Provides: indi-allsky (= ${binary:Version})
Conflicts: indi-allsky
Replaces: indi-allsky
```

* **Seamless Upgrades**: Installing `indi-allsky-edge` replaces the official package binaries while preserving all configuration files (`/etc/indi-allsky/`), the SQLite/MySQL database (`/var/lib/indi-allsky/`), and systemd service state without disruption.
* **Frictionless Rollback**: Should you wish to return to the official upstream release, executing `sudo apt install indi-allsky` restores the upstream package without data loss.

---

### Installation

#### Method 1: APT Repository (Recommended)

```bash
# Add the indi-allsky-edge APT component
sudo curl -fsSL https://tn-1.github.io/apt/KEY.gpg | sudo gpg --dearmor -o /etc/apt/keyrings/indi-allsky-edge.gpg
echo "deb [signed-by=/etc/apt/keyrings/indi-allsky-edge.gpg] https://tn-1.github.io/apt edge main" | sudo tee /etc/apt/sources.list.d/indi-allsky-edge.list

sudo apt update
sudo apt install indi-allsky-edge
```

#### Method 2: Direct .deb Installation

Download the latest `.deb` for your architecture from [GitHub Releases](https://github.com/TN-1/indi-allsky-edge/releases/tag/edge-latest) and install via dpkg:

```bash
sudo apt update
sudo apt install ./indi-allsky-edge_*+trixie_arm64.deb
```

---

### Orchestration Architecture

* **`main` Branch**: Contains the declarative integration manifest (`manifest.yaml`), the synthesis engine (`rebuild.py`), the conflict resolution cache (`rr-cache/`), and GitHub Actions packaging workflows.
* **`edge` Branch**: An ephemeral target branch synthesized automatically from `upstream/main` plus the active pull request queue.
