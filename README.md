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

Debian packages (`.deb`) are compiled and published automatically to the rolling [Bleeding Edge GitHub Release](https://github.com/TN-1/indi-allsky-edge/releases/tag/edge) across all supported distributions and architectures.

#### Direct `.deb` Installation

1. Navigate to [GitHub Releases (`edge`)](https://github.com/TN-1/indi-allsky-edge/releases/tag/edge).
2. Download the package built for your distribution and hardware architecture:
   * **Debian 12 (Bookworm)**: `indi-allsky-edge_*+bookworm_{amd64,arm64}.deb`
   * **Debian 13 (Trixie)**: `indi-allsky-edge_*+trixie_{amd64,arm64}.deb`
   * **Ubuntu 24.04 (Noble)**: `indi-allsky-edge_*+noble_{amd64,arm64}.deb`
   * **Ubuntu 26.04 (Resolute)**: `indi-allsky-edge_*+resolute_{amd64,arm64}.deb`

3. Install the downloaded package using `apt`, which will automatically resolve and install all underlying dependencies:

```bash
sudo apt update
sudo apt install ./indi-allsky-edge_*+<distro>_<arch>.deb
```

*(Note: Direct APT repository hosting is currently disabled during this initial validation phase. Distribution is conducted exclusively via GitHub Releases.)*

---

### Orchestration Architecture

* **`main` Branch**: Contains the declarative integration manifest (`manifest.yaml`), the synthesis engine (`rebuild.py`), the conflict resolution cache (`rr-cache/`), and GitHub Actions packaging workflows.
* **`edge` Branch**: An ephemeral target branch synthesized automatically from `upstream/main` plus the active pull request queue.
