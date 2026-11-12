# CR-025: one repository, several distributions (the packages layout)

- **Requested by / date:** owner, 2026-10-23 (phase 2 of the overhaul plan, `ponzi-service/docs/overhaul-plan.md`)
- **Status:** implemented on the owner's instruction (2026-10-23), awaiting review; uncommitted (plan decision D10)
- **Superseded in part:** run configs are scoring specs under `specs/scoring_specs/` (CR-048, CR-070, CR-078).

## Why

ponzi-core becomes the home of four distributions: `ponzi-spec` (CR-024), `ponzi`, and later `ponzi-pipeline` and `ponzi-models`. Each needs its own `pyproject.toml`, version and tests, installable alone (`pip install "...#subdirectory=packages/<dir>"`), while the repository keeps one pixi workspace, one change process and one CI.

## What changes

Files move; no code changes.

| Before | After |
| --- | --- |
| `pyproject.toml` (the `ponzi` distribution) | `packages/core/pyproject.toml`; hatch-vcs reads the version from the repository root (`raw-options.root = "../.."`), the tags stay `v0.y.z` |
| `src/ponzi/` | `packages/core/src/ponzi/` |
| `tests/` (incl. `tests/data/`, `tests/onboarding/`) | `packages/core/tests/` |
| `configs/run/` | `data/run_configs/` (versioned data of the repository; standards will name configs from here) |

`pixi.toml`: `ponzi` and `ponzi-spec` are editable path dependencies of the default environment; `jsonschema` joins it for the spec tests; `pixi run test` runs `packages/core/tests` (same tiers and markers, the pytest config moves with the package), the new `pixi run test-spec` runs `packages/spec/tests`. The lock file is regenerated (and moves to pixi's lock format v7).

Two tests read the reference run config from its new place (`test_config.py`, `test_rolling.py`). `test_layering.py` is unchanged: its paths are relative to the distribution's folder. README, CLAUDE.md and the run-config contract name the new paths.

## Do results change?

No. Same code, same golden files.

## Tests

The fast tier before the move: 571 passed, 14 skipped. After: the same counts, plus `pixi run test-spec` (38).

## Version

`ponzi`: none (no code change; the next release tag carries it). Standard: not affected.
