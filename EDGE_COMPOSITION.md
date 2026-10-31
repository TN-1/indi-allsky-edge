## `indi-allsky-edge` Build Composition

This release is an automated bleeding edge distribution aggregating pending pull requests on top of the official upstream repository. It is mainly for testing purposes, and previewing upcoming features. Please do not report issues with this build on aaronwmorris/indi-allsky.

### Base Upstream Reference
* **Repository**: [aaronwmorris/indi-allsky](https://github.com/aaronwmorris/indi-allsky)
* **Branch**: `main`
* **Base Commit**: [`938bf860`](https://github.com/aaronwmorris/indi-allsky/commit/938bf860b28a472ed71e801d75b7ec9a230b6fef) – *"Merge pull request #3304 from TN-1/fix/sensor-units"* (2026-10-26)

### Integrated Pull Requests (28)

| PR | Title | Author | Status |
|:---|:---|:---|:---|
| [#3322](https://github.com/aaronwmorris/indi-allsky/pull/3322) | fix: ensure form choice options are tuples for WTForms 3.2+ compatibility | [@TN-1](https://github.com/TN-1) | Clean merge |
| [#3329](https://github.com/aaronwmorris/indi-allsky/pull/3329) | fix: ensure float field formatting and validation support WTForms 3.3+ NumberInput | [@TN-1](https://github.com/TN-1) | Clean merge |
| [#3321](https://github.com/aaronwmorris/indi-allsky/pull/3321) | fix(sensors): handle TSL2561 and TSL2591 out-of-range readings | [@TN-1](https://github.com/TN-1) | Clean merge |
| [#3317](https://github.com/aaronwmorris/indi-allsky/pull/3317) | fix: prevent SensorWorker crash on missing Ecowitt outdoor data | [@TN-1](https://github.com/TN-1) | Clean merge |
| [#3316](https://github.com/aaronwmorris/indi-allsky/pull/3316) | fix: respect configured image file type in allsky-map ping | [@TN-1](https://github.com/TN-1) | Clean merge |
| [#3315](https://github.com/aaronwmorris/indi-allsky/pull/3315) | Fix Support Info generation failing when configuration contains Unicode characters | [@nicoloserafino](https://github.com/nicoloserafino) | Clean merge |
| [#3309](https://github.com/aaronwmorris/indi-allsky/pull/3309) | Fix: Local camera freshness after DST changes | [@321MathiasS123](https://github.com/321MathiasS123) | Clean merge |
| [#3305](https://github.com/aaronwmorris/indi-allsky/pull/3305) | Fix: Logging in darks.py | [@TN-1](https://github.com/TN-1) | Clean merge |
| [#3302](https://github.com/aaronwmorris/indi-allsky/pull/3302) | fix(mdns): Harden mDNS hostname's and certificate SAN's | [@TN-1](https://github.com/TN-1) | Clean merge |
| [#3298](https://github.com/aaronwmorris/indi-allsky/pull/3298) | Fix: chart resizing at fractional browser zoom | [@321MathiasS123](https://github.com/321MathiasS123) | Clean merge |
| [#3292](https://github.com/aaronwmorris/indi-allsky/pull/3292) | Bilateral controls and help text stay hidden until Bilateral is selected | [@ikeysolomon](https://github.com/ikeysolomon) | Clean merge |
| [#3290](https://github.com/aaronwmorris/indi-allsky/pull/3290) | WH-SP-RG - Tipping bucket rain gauge | [@ikeysolomon](https://github.com/ikeysolomon) | Clean merge |
| [#3272](https://github.com/aaronwmorris/indi-allsky/pull/3272) | Send *_complete events once the file is written | [@chrisramsay](https://github.com/chrisramsay) | Clean merge |
| [#3257](https://github.com/aaronwmorris/indi-allsky/pull/3257) | Feature: Chart tab enhancement, adds overlaid configurable charts | [@ikeysolomon](https://github.com/ikeysolomon) | Clean merge |
| [#3251](https://github.com/aaronwmorris/indi-allsky/pull/3251) | FC-37 inverse control and help text stay hidden until FC-37 is selected | [@ikeysolomon](https://github.com/ikeysolomon) | Clean merge |
| [#3225](https://github.com/aaronwmorris/indi-allsky/pull/3225) | Feature: Gallery panorama overlay | [@321MathiasS123](https://github.com/321MathiasS123) | Clean merge |
| [#3201](https://github.com/aaronwmorris/indi-allsky/pull/3201) | Support automatic VirtualSky mirroring | [@321MathiasS123](https://github.com/321MathiasS123) | Clean merge |
| [#3009](https://github.com/aaronwmorris/indi-allsky/pull/3009) | fix: don't crash charts endpoint when detection mask size doesn't match image | [@DeepakJaggupalli](https://github.com/DeepakJaggupalli) | Clean merge |
| [#3323](https://github.com/aaronwmorris/indi-allsky/pull/3323) | testing: harden qa script: verify authenticated web route rendering and live WSGI socket binding | [@TN-1](https://github.com/TN-1) | Clean merge |
| [#3318](https://github.com/aaronwmorris/indi-allsky/pull/3318) | refactor: streamline stylesheet architecture | [@TN-1](https://github.com/TN-1) | Clean merge |
| [#3289](https://github.com/aaronwmorris/indi-allsky/pull/3289) | feat(github): add structured issue forms | [@TN-1](https://github.com/TN-1) | Clean merge |
| [#3283](https://github.com/aaronwmorris/indi-allsky/pull/3283) | Add allsky-map.com integration section and screenshot to README | [@TN-1](https://github.com/TN-1) | Clean merge |
| [#3280](https://github.com/aaronwmorris/indi-allsky/pull/3280) | Add setting to disable smoke data checking and reporting | [@TN-1](https://github.com/TN-1) | Clean merge |
| [#3231](https://github.com/aaronwmorris/indi-allsky/pull/3231) | Feature: Add Model Context Protocol (MCP) server for AI agent integration | [@TN-1](https://github.com/TN-1) | Clean merge |
| [#3134](https://github.com/aaronwmorris/indi-allsky/pull/3134) | Feature: Docker Stack Rewrite | [@TN-1](https://github.com/TN-1) | Clean merge |
| [#3049](https://github.com/aaronwmorris/indi-allsky/pull/3049) | Feature: Adds script to generate screenshots | [@TN-1](https://github.com/TN-1) | Clean merge |
| [#3265](https://github.com/aaronwmorris/indi-allsky/pull/3265) | Support sensor devices A-Z with a progressive Add sensor UI | [@ikeysolomon](https://github.com/ikeysolomon) | Resolved via rerere |
| [#3112](https://github.com/aaronwmorris/indi-allsky/pull/3112) | Feature: Dark library builder and dark management in the UI | [@321MathiasS123](https://github.com/321MathiasS123) | Resolved via rerere |

### Applied Reconciliation Glue Patches (1)

| Patch | Description |
|:---|:---|
| `patches/01-edge-packaging.patch` | Configure indi-allsky-edge package identity and packaging workflow |
