# CR-028: ponzi-models becomes a distribution of this repository

- **Requested by / date:** owner, 2026-10-23 (phase 3 of the overhaul plan; plan decisions: ponzi-models absorbed into ponzi-core, without its git history; a clean slate, D6)
- **Status:** implemented on the owner's instruction (2026-10-23), awaiting review; uncommitted (plan decision D10)
- **Superseded in part:** a standard has no workflow list (CR-084), the run config hash is the scoring spec hash (CR-070), and detection is a spec, not fields or a preset (CR-043, CR-070).

## Why

ponzi-models was a folder of scripts that found each other through `sys.path`, ran in this repository's environments through `PYTHONPATH`, recorded the commit of their own checkout, and served a model's weights to a run through a symlinked working folder because the run config named them by a relative path. The overhaul makes it an installable distribution beside `ponzi`, versioned on its own, with one command.

## What changes

**New distribution `ponzi-models` 0.1.0** (`packages/models/`, import `ponzi_models`), copied from the repository ponzi-models at `3b853a7`:

| Subpackage | From |
| --- | --- |
| `panels` (`masks`, `masked_input`, `export_pixels`) | `panels/` |
| `training` (`fit_spec`, `prepare`, `train`, `export`, `augment`, `tide`, `tracking`, `eval_breakdowns`) | `training/` |
| `calibration` (`null_runs`, `null_rows`, `build`, `compare`, `panel_files`) | `calibration/` |
| `registry` (`store`, `register_model`, `register_calibration`) | `registry/` and `ponzi.models` of this repository |
| `standards` | new |
| `provenance`, `cli` | new |

- Imports are package imports; no `sys.path` edits (a test refuses them, and absolute machine paths, in the code).
- One command, `ponzi-models <command>` (`masks`, `export-pixels`, `prepare`, `train`, `export`, `eval-breakdowns`, `register-model`, `null-runs`, `null-rows`, `calibrate`, `compare-calibrations`, `register-calibration`, `check-standard`); each module keeps a `main(argv)`.
- Every output records `ponzi_models.provenance.commit()`: the short commit of the ponzi-core checkout (`+dirty` with uncommitted changes), or the package version outside a checkout.
- Fit specs move to `data/specs/` of this repository.

**The registry moves out of `ponzi`**: `ponzi.models` is removed; `ponzi_models.registry` holds `ModelCard`, `ModelEntry`, `Registry` and the rest unchanged. `ponzi` finds the registry's artifact resolver through the entry point group `ponzi.artifact_resolvers` (CR-026), which ponzi-models registers, so a run resolves `registry:<id>@sha256:<digest>` without `ponzi` importing `ponzi_models`. `ponzi pvalues RUN_DIR --calibration FILE` takes the calibration file instead of `--model`, `--calibration ID` and `--registry`.

**Weights by reference, no working folder**: `register-model` writes the registry reference into the run config (derived configs) or requires it (hand-written ones; the refusal prints it), computing the digest before the artifact is filed. `null-runs` runs with the registry's resolver and refuses a model with weights whose config names them by a path. The symlinked working folder is gone.

**Standards** (`ponzi_models.standards`): `Standard`, the versioned bundle a watched area runs (workflow, coherence and onboarding configs, model reference, run config hash, calibrations, detection recipe as fields or a preset name, minimum versions), `load_standard`, `Standard.check(registry)` (the model, its reference, its run config and its calibrations as the registry holds them) and `ponzi-models check-standard`. `data/standards/` is empty: the first standard comes with the first model on ISCE3 coherence (plan phase 8b).

**Not carried over**: `registry/register_existing.py` (it registered the monorepo's models; a clean slate), `training/eval_context.py` (the alias of `eval_breakdowns`), `calibration/mask_check.py` (a one-off check of 2026-10-13, superseded by the masked route), the `hpc/` job files (the worker's cluster profile, plan phase 8; they stay in the old repository as the reference). The panel builders and label producers of ponzi-paper are not here yet (plan decision D14).

**Environment**: `ponzi-models` is editable in the pixi environments; `pixi run test-models` (the torch tests skip outside `ml`).

## Do results change?

No number of `ponzi` changes. The scripts compute what they computed; the only behaviour change is that a model with weights must be named by its registry reference (clean slate, nothing registered before is carried over).

## Tests

ponzi-models' tests move with it, adapted to the package imports and to references (the registry tests from this repository, the reference tests of CR-026 that need the registry). New: `test_standards.py`, `test_registry_refs.py` (incl. the installed resolver), `test_layering_models.py`. One test of the old repository was already failing at `3b853a7` (the candidate list lacked `tide_c30_pdcompact_previous_aug_s1`) and is corrected. `pixi run test-models`: 91 passed and 18 skipped (torch); `pixi run -e ml test-models`: 109 passed.

## Version

`ponzi-models` 0.1.0, new. `ponzi`: MAJOR in the contract sense (a subpackage and a command's arguments removed), released under CR-020's reading as `0.3.0`. A tool that imported `ponzi.models` must import `ponzi_models.registry`, and CR-020's check refuses calibrations made with `0.2` for runs of `0.3`; on the clean slate (D6) no such calibration is used. Standard: not affected.
