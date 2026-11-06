# CR-051: the problems the contract check found, fixed

- **Requested by / date:** owner, 2026-11-05 ("I approve all changes", the problems listed in CR-050).
- **Status:** implemented on the owner's instruction (2026-11-05), awaiting review; uncommitted

## Why

Checking the contracts against the code (CR-050) found places where the code did not do what its contract said, or where two parts of the code disagreed. Three of them would affect real runs: an assembled store could not run under the default config's `noise_floor: derived`, staged runs could only ever get final-stage codes, and a run's STAC Item never listed its all-channel z store.

## What changes

**An assembled store records its estimator (C1).** `ponzi_pipeline.assemble` writes `estimator_params` (`looks_rg`, `looks_az`, `sigma_rg`, `sigma_az`, `truncate`, `kind`) from its `coherence_config` (`assemble.estimator_params`), so `state_machine.noise_floor: derived` is computed from the store. `ponzi.contracts.coherence.noise_floor` uses `truncate` for the window's half width where a store records it, scipy's `int(truncate * sigma + 0.5)`. Without it the half width stays 2, as before. A `bperp` table with no value is left out of the store: an all-NaN table writes no chunk, which both checkers read as a torn array.

**A command builds a staged (format 3) calibration (C22).**
- `ponzi-models null-runs --staged` makes staged panel runs (`staged.zarr`), in their own folders (`..._mask-{layer}_staged`).
- `ponzi-models calibrate-staged --runs DIR... --model ID --panel ID --prefix P --out DIR` builds the plain and the ceiling format 3 calibration from them with `ponzi.calibration.staged_inputs`. It writes the same layout as `calibrate`, and refuses an existing file or a folder with no staged run.
- `provenance.n_null_by_stage` is keyed `1 .. H` as the file's meta is, instead of `final` for the last stage.

**A run's STAC Item lists `channels_z.zarr` (C21).** `ponzi.stac.items.RUN_ASSETS` names the file the runner writes, under the role `all_channels`.

**`calibration_window` is removed.** It was accepted, recorded in `run_meta.request` and never acted on, yet it entered the worker's run content id. It is removed from `RunRequest` (and so from `ponzi run`'s flags) and from the worker's `RunParams`.

**A composed run config is copied as its composed document (C4).**
- `ponzi_spec.compose.uses_extends` tells whether a document names a base anywhere.
- `ponzi.core.config.composed_run_config` gives a run config's flat document with its name, and `load_run_config` uses it.
- The registry files a run config that uses `extends` as that document (`ponzi_models.registry.copy_run_config`); one without is still copied byte for byte. Either way the copy loads to the same name and hash.
- `standard-workflow` reads the registered config composed.
- The worker's `run` stage refuses a `RunParams.config` that still names a base, since its relative paths would not resolve from the work folder.
- The server reads its standards files composed, as every config is (CR-043).

**The engine's checks and PONZI's agree (C18).** `ponzi_pipeline.engine` now reads the catalogue as `ponzi.contracts.validate` does:
- `structure` passes a float64 `coh`, and checks the pair tables' shapes;
- `dtype` is written for a float64 `coh`;
- `chunk_completeness` counts `coh` chunks by time and baseline block, and checks every other array's chunks;
- `pairs_declared` warns on `n_cell_collisions`.

C18's note on where the two differ is replaced by the test that shows they agree.

**Small things.**
- `ponzi --help` (and `ponzi` alone) lists all eight commands.
- `make_coherence_fixture` takes `.coh` off a `*.coh.zarr` name for its `burst_id`.
- `run_meta.written` lists `pred.zarr` only when the store was made.
- Two runner docstrings name `tools/run_capped.sh` and a SLURM script, instead of `ops/` paths that no longer exist.

Contracts C1, C4, C4a, C18, C21 and C22 and the suite's `contributing/new-model.md` follow.

## Do results change?

- **Scores and codes:** no, for every existing store and run config.
  - Stores already assembled have no `estimator_params`, so `noise_floor: derived` refuses them as before. Newly assembled ones carry it.
  - The derived noise floor of a store that records `estimator_params` without `truncate` is unchanged.
- **Worker content ids: yes.** Every run content id the worker computes changes, because `calibration_window` (null) is no longer among the hashed parameters. Runs already in a worker cache are recomputed once.
- **Calibration provenance:** a staged calibration's `n_null_by_stage` names the final stage `H` instead of `final`. That record is provenance only; codes are unchanged.
- **Engine reports:** an engine report written for a float64 store would now say `structure` ok with a `dtype` warning, where it said fail.

## Tests

- ponzi-pipeline:
  - `test_engine_agreement.py`: the engine and PONZI give every shared check the same severity on a conforming store, a float64 store and a torn store.
  - The assembly test checks `estimator_params` and the derived noise floor.
- ponzi-models:
  - `test_calibration.py`: `null-runs --staged`, then `calibrate-staged`, then `ponzi pvalues` coding every stage.
  - `test_registry_store.py`: a composed run config is filed flat with its name and hash, and a flat one is filed byte for byte.
- ponzi-spec: `uses_extends`.
- ponzi-core: `ponzi --help` and the fixture's `burst_id`.
- Every suite of ponzi-core and ponzi-service is run.

## Version

- `ponzi` (core): patch. The flag `--calibration-window` goes, but it never acted.
- `ponzi-pipeline`: minor (a new store attr).
- `ponzi-models`: minor (a new command and flag).
- `ponzi-spec`: patch.
- Standard: none.
