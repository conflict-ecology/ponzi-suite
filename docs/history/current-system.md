# PONZI as it stands: workflow and configuration

A record of the system before the overhaul into packages: what each repository holds, how work flows from a panel to a published model and from a coherence store to an events store, and every configuration surface along the way. Taken on 2026-10-22 from:

| Repository | State |
| --- | --- |
| `ponzi-core` | `main` at `9134468`, release `v0.2.3` (tags `v0.2.0` to `v0.2.3`) |
| `ponzi-models` | `main` at `3b853a7`, no tags |
| `ponzi-service` | empty apart from this file |

Named but not in this workspace: `ponzi-apps` (applications, AOI configs, HPC ops, pages), `ponzi-paper`, and the monorepo `pbarthelme/ponzi` (tag `pre-restructure`), which still holds campaign planning, panel builders, label producers and the decision log.

## 1. What each repository holds

### ponzi-core: the library

One installable package, `ponzi` (hatchling, version from git tags via hatch-vcs), and one command, `ponzi`. Subpackages import one way only; `tests/test_layering.py` enforces it.

| Subpackage | Role |
| --- | --- |
| `contracts` | store formats: readers, writers, validators (bottom layer) |
| `core` | the forecast run: config, context, forecasters, scoring, aggregation, state machine, anchor loop, sinks |
| `calibration` | scores to p-values and uint8 codes, the ceiling lookup, the calibration file |
| `evaluation` | labels, rows at labelled pixels, metrics, events |
| `grid` | geometry only (lattice, mosaic, reprojection, tiles); imports no other subpackage |
| `onboarding` | before a run: validate a coherence store, write its covariates sidecar and pixel sample |
| `products` | after a run: the single-path detection recipe and events stores |
| `models` | the registry: model cards, artifacts, calibrations |

Importing `contracts`, `core`, `evaluation`, `calibration`, `grid` or `models` must not load torch or the geospatial stack. Optional extras: `tide` (torch), `onboarding` (pyproj, rasterio, requests, cdsapi, netcdf4, fsspec, aiohttp), `grid` (shapely, pyproj).

Registered forecasters: `rolling_ols`, `tide`, `stored`, `external`.

Process: every change is a signed-off request in `docs/requests/` (CR-000 to CR-023 so far), done on a branch with tests and released with a tag and a `CHANGELOG.md` entry. Golden files under `tests/data/` lock the numbers. Below 1.0, `0.y` counts as the major version: a calibration built with another `0.y` is refused (CR-020).

### ponzi-models: training, calibration, registration

Plain scripts, not a package. No `pyproject.toml` and no `pixi.toml`: scripts run in a ponzi-core environment, either a tagged release's `.pixi/envs/{ml,ml-gpu}` or a checkout through `PYTHONPATH=<ponzi-core>/src`. Output: entries in the model registry.

| Folder | Content |
| --- | --- |
| `panels/` | `masks.py` (panel as mask layers on full burst stores), `masked_input.py` (the one reader of panel data), `export_pixels.py` (pixel dataset export and check) |
| `training/` | `fit_spec.py`, `prepare.py`, `train.py`, `export.py`, `augment.py`, `tide.py`, `tracking.py` (wandb), `eval_breakdowns.py` (alias `eval_context.py`) |
| `calibration/` | `null_runs.py`, `null_rows.py`, `build.py`, `compare.py`, `panel_files.py`, `mask_check.py` |
| `registry/` | `register_model.py`, `register_calibration.py`, `register_existing.py` |
| `specs/` | fit specs of registered models; `candidates/` for fits under comparison |
| `hpc/` | SLURM job files, one per stage |
| `tests/` | synthetic panels, tiny CPU TiDE, about 30 s |

## 2. Workflows

There are two lifecycles. Both go through the same opener (`ponzi.core.runner.open_input`), so training, calibration and production read identical bytes.

### 2a. Model lifecycle (ponzi-models)

```
panel package ──► 1 masks ──► 1b pixel export (opt.) ──► 2 prepare
                                                             │
5 register model ◄── 4 export ◄── 3 train ◄──────────────────┘
  │
  └──► 6 null ──► 7 calibrate ──► 8 register calibrations ──► registry
```

| # | Stage | Command | Writes | Runs on |
| --- | --- | --- | --- | --- |
| 0 | panel | monorepo `ponzi-paper majortom-package` | package folder `PANEL` | HPC |
| 1 | masks | `python panels/masks.py --panel PANEL --index N` | `PANEL/bursts/<burst>/<burst>_masks.zarr` (layers `sample`, `cell`) | HPC CPU array, `panel_masks.sbatch` |
| 1b | pixel export | `python panels/export_pixels.py --panel PANEL --index N [--check]` | `{PANEL}_pixels_sample/bursts/<burst>/samples/<burst>_sample.zarr` | HPC CPU array, `export_pixels.sbatch` |
| 2 | prepare | `python training/prepare.py --panel PANEL --spec SPEC --out TRAIN [--input pixels --pixels DIR]` | `TRAIN/prepared_<tag>/{features_train.npz, features_val.npz, prepare.json}` | HPC CPU, `train_prepare.sbatch` |
| 3 | train | `python training/train.py --spec SPEC --out TRAIN --device cuda [--seed N]` | `TRAIN/<fit_id>[_s<N>]/{checkpoint.pt, model_card.yaml, history.json, training_log.parquet}` | HPC GPU, `train_fit.sbatch`, `train_one.sbatch`, `train_candidates.sbatch` |
| 4 | export | `python training/export.py --fit TRAIN/<fit_id> --models-root ARTIFACTS` | `ARTIFACTS/NAME/{torchscript/{model_ts.pt, meta.json}, model_card.yaml}` | same GPU job |
| 5 | register model | `python registry/register_model.py --artifact A --from-model ID --config-name CFG` (or `--run-config FILE`) | `<registry>/NAME/{artifact/, run_config.yaml, model.json}` | wherever the registry is |
| 6 | null | `python calibration/null_runs.py --panel P --model M --results RES --index N [--input masked --mask LAYER]`, then `null_rows.py` | `RES/<burst>/<config>_{sample,mask-LAYER}/`, `RES/rows/panel_<config>_*.npz` | HPC CPU array, `null_runs.sbatch`, `null_rows.sbatch` |
| 7 | calibrate | `python calibration/build.py --null ... --scores ... --prefix P --out RES/calibrations` | `RES/calibrations/P-plain`, `P-ceiling` | same job as null rows |
| 8 | register calibrations | `python registry/register_calibration.py RES/calibrations/*/calibration.npz` | `<registry>/<model>/calibrations/<id>/calibration.npz` | wherever the registry is |
| - | compare | `python training/eval_breakdowns.py`, `calibration/compare.py NEW REF` | breakdown JSON, comparison report | HPC CPU, `eval_breakdowns.sbatch` |

The model is registered before the null because the null is a run of a registered model: its weights come from the registry and its scores carry the registered config's hash.

### 2b. Production run lifecycle (the `ponzi` command)

```
coherence store (C1, external)
  │  ponzi validate-store PATH
  │  ponzi weather-prefetch --config F --cache DIR --start D --end D
  │        (optional, once per AOI)
  │  ponzi onboard --store PATH --out DIR [--config F]
  │        → sidecar C2, sample C3, onboard_meta.json
  ▼
ponzi run --coh .. --sidecar .. --config RUN_CONFIG --out RUN_DIR [...]
  │        → score C7, change C8, run_meta C9 (+ optional stores)
  │  ponzi replay SCORE --out PATH        (re-threshold only)
  │  ponzi forecasting-summary --stats FILE
  ▼
ponzi pvalues RUN_DIR --model M --calibration CAL
  │        → pvalues_<cal>.zarr (C22)
  ▼
ponzi detect RUN_DIR --calibration CAL [--recipe PRESET|FILE]
           → events_<cal>.zarr (C25)
ponzi detect-path RUN_DIR... --calibration CAL --out PATH
           [--lattice F] [--overlap max|min|first]
```

Onboarding steps, in order: `built`, `weather`, `pairdiff`, `mask`, `sample`. `ponzi detect` needs `summary.zarr`, so the run needs `--summaries et`. Progressive scoring (`--staged`) adds `staged.zarr`, and with a format-3 calibration it adds staged codes and provisional flags. Monitoring updates are ordinary staged runs written to new folders; there is no append mode.

Campaign planning (AOIs, tracks, bursts, the request and its validation table) is not in the library. It stays in the monorepo until `ponzi-apps` takes it.

## 3. Configuration surfaces

| Config | Where it lives | Schema | Hashed into identity? |
| --- | --- | --- | --- |
| Run config (C4) | `ponzi-core/configs/run/*.yaml` (generated from monorepo `experiments.yaml`); `run_config.yaml` of each registry entry | `ponzi.core.config.RunConfig`, pydantic, `extra="forbid"` | Yes: `config_hash` = BLAKE2b-16 of canonical JSON, without `name` |
| Run request (C4a) | flags, `--args-file` yaml, `PONZI_*` env | `ponzi.core.runner.RunRequest` (pydantic-settings) | No; stamped into stores and `run_meta.json` |
| Command args (C4b) | as above, for `replay` and `forecasting-summary` | `ReplayArgs`, `ForecastingSummaryArgs` | No |
| Onboarding config | yaml with an `onboarding:` section (the monorepo request config C17 loads as is) | `ponzi.onboarding.config.OnboardingConfig`, frozen, `extra="forbid"` | Recorded in the onboarding stamp |
| Detection recipe | `--recipe` preset name or yaml; presets hard-coded in `ponzi.products.recipe.PRESETS` | `DetectionRecipe`, frozen | `digest()` (sha256, 16 hex), in the events store |
| TiDE forecaster params | `forecaster.params` of the run config | `TideParams` (`artifact`, `batch`, `device`, `batching`) | Yes, as part of the run config; `artifact` is a relative path |
| Artifact meta | `artifact/meta.json`, written by `training/export.py` | read by `ponzi.core.forecast.model_inputs.load_artifact` | Covered by `artifact_digest` in the model card |
| Fit spec | `ponzi-models/specs/**/*.yaml` | `training/fit_spec.py` `TideSpec`, unknown keys refused | Prepared-folder tag hashes baselines, covariates, layer and route only |
| Model card | `<registry>/<id>/model.json` | `ponzi.models.registry.ModelCard` | Holds `run_config_hash` and `artifact_digest` |
| Calibration | `<registry>/<id>/calibrations/<cal>/calibration.npz` | `ponzi.calibration.Calibration`, file format 2 (or 3 when staged) | Records the run config hash and `ponzi_version`; refuses a mismatch |
| HPC job parameters | env vars on `sbatch --export` | shell defaults in `hpc/*.sbatch` | No |

### Run config fields

```yaml
schema_version: 1
context: {C: 30, min_support: 6}
forecaster: {name: rolling_ols, params: {harmonic_order: 0, pooled: false}}
scoring: {baseline_days: [12, 24, 36, 48, 60], H: 5, alpha: 3.0}
aggregate: {min_channels: 5, struct_weight: true}
state_machine: {alpha: null, delta: -0.1, recovery_steps: 1, noise_floor: 0.03, nms_window: 0}
```

Nulls resolve before hashing (`state_machine.alpha` → `scoring.alpha`, `nms_window: 0` → `H`). Defaults are load-bearing: an omitted default hashes the same as a written one. A run config never holds paths, dates, modes, dataset names, sinks or thread counts. The one exception is the TiDE `artifact` path.

### Run request fields

Required: `coh`, `config`, `out`. Optional: `sidecar`, `extra_sidecar`, `mode` (`monitoring` or `detection`, inferred from the dates when unset), `event_date` and `event_end_date` or `start_date` and `end_date`, `calibration_window`, `chunks`, `overwrite`, `threads`, `max_memory_gb` (default: refuse when the estimate exceeds 80 % of available memory), `mask_store` + `mask` (CR-014), `strict_covariates` (CR-016), `summaries` (`et`, `et,e`; CR-017, CR-019), `context_keep` (CR-022), `staged` (CR-021), `save_pred`, `save_channels`, `save_all_channels`.

Precedence: flags > args file > environment > model defaults.

### Onboarding config

```yaml
onboarding:
  steps: [built, weather, pairdiff, mask, sample]
  edge_margin: 20
  weather_source: edh             # edh | cdsgrid | edh_cdsgrid
  weather_variables: [...]
  weather_area: [lon_min, lat_min, lon_max, lat_max]   # optional, CR-023; not with edh
  pairdiff_baselines: [12, 24, 36, 48, 60]
```

### Detection recipe

Defaults: `calibration_kind: ceiling`, `code: 50`, `gap: 0`, `dating_pre: 1`, `dating_post: 4`, `windows: exclusive`, `episode_days: null`, `start_date: null`, `provisional: false`. Preset `gaza_release_v4`: `gap: 1`, `episode_days: 60`, `start_date: 2023-10-07`, `windows: overlapping`.

### Fit spec keys

Window: `fit_id`, `model`, `context_length`, `horizon_length`, `baseline_days`, `quantile_levels` (`zu11`), `covariates`, `era5_vars` (every series by name, including pair differences and, in the `_s1` candidate, `s1_pd_vv_db_*`).
Model sizes: `hidden_size`, `num_encoder_layers`, `num_decoder_layers`, `decoder_output_dim`, `temporal_decoder_hidden`, `temporal_width_future`, `use_layer_norm`, `covariate_layer_norm`, `dropout`.
Optimisation: `batch_size`, `lr`, `grad_clip`, `epochs`, `min_epochs`, `early_stopping_patience`, `early_stopping_min_delta`, `mask_missing_targets`, `seed`, `wandb_project`, `wandb_log_steps`.
Fine-tune: `init_from`, `extra_samples`, `extra_until`, `extra_share`, `keep_last_epoch`.
Missing values (CR-016): `missing.{fill,value,flag}`, `future_obs`, `strict_covariates`, `support`.
Augmentation: `augment` (kinds `truncate_context`, `unknown_future`, `drop_acquisitions`, `outage`, `drop_baseline`) and its alias `context_dropout`. Anchor rule: `anchors: inference` (the only value).

Specs on file: `tide_c30_pdcompact.yaml`, `tide_c30_gaza_f1p.yaml` (registered), and the candidates `_constant` (control), `_median`, `_previous`, `_sentinel`, `_sentinel_flag`, `_previous_cd`, `_previous_aug` and `_previous_aug_s1`.

### Environment variables

| Variable | Used by | Meaning |
| --- | --- | --- |
| `PONZI_MODEL_REGISTRY` | `ponzi.models.default_registry_root` | registry folder |
| `PONZI_DATA_ROOT` | same, and job files | data root; registry falls back to `$PONZI_DATA_ROOT/registry` |
| `PONZI_<FIELD>` | every `CommandArgs` model | fills run request and command fields |
| `PONZI_TIDE_WORKERS` | `ponzi.core.forecast.tide` | TiDE worker threads |
| `OMP_NUM_THREADS`, `SLURM_CPUS_PER_TASK` | the runner and jobs | threads, when `threads` is unset |
| `WANDB_*`, `TORCH_HOME`, `XDG_CACHE_HOME`, `TMPDIR` | training jobs | all redirected under `$DR` |
| `SPEC`, `SEED`, `VERSION`, `OUT`, `INPUT`, `MASK`, `MODEL`, `PREFIX`, `RES`, `PANEL`, `PREPARED`, `ARTIFACT(S)`, `EXTRA_DIR`, `SETTING`, `TAG`, `WANDB`, `RELEASE`, `PY`, `CORE`, `MODELS`, `CHECK`, `PACKAGE` | `hpc/*.sbatch` | job parameters, with defaults in each file |

### Software environments (ponzi-core `pixi.toml`)

| Environment | Content | Used for |
| --- | --- | --- |
| `default` | library, tests, geospatial stack; never torch | `pixi run test`, CI (GitHub Actions, fast tier) |
| `ml` | default + torch CPU | TiDE tests, CPU evaluation, ponzi-models tests |
| `ml-gpu` | torch 2.6 (CUDA 12.4, for GTX 1080 Ti SM 6.1) + wandb | HPC training |

Python `>=3.11,<3.13`, linux-64 only. `tools/run_capped.sh` runs heavy commands under a memory cap.

### HPC layout (hard-coded in the job files)

| Name | Path |
| --- | --- |
| `DR` (data root) | `/storage/ceoas-scratch/barthelp/ponzi/data` |
| `LAB` | `/ceoas/Vandenhoek_Lab/home/barthelp` |
| ponzi-models clone | `$LAB/ponzi-models` |
| core release environments | `$LAB/ponzi-core-releases/v0.2.1/.pixi/envs/...` |
| registry | `$DR/registry` |
| panels | `$DR/artifact/majortom/v0.4` (and v0.2) |
| training | `$DR/training/majortom_v0.4_masked/` (prepared folder `prepared_a565ce1d31`) |
| calibration results | `$DR/calibration/<model>/<panel>` |
| S1 extra sidecars | `$DR/side/sar_sm/sidecars` |
| logs | `$DR/logs` |

Partitions and nodes: `ceoas-gpu` on `ayaya*` for GPU work, `hina01` for CPU work (other nodes read scratch slowly). Every submission needs the owner's approval.

## 4. Stores and files that cross a stage boundary

| # | Store | Producer |
| --- | --- | --- |
| C1 | coherence store `(time, y, x, baseline)` | external (S1 engine, NISAR) |
| C2 | `<burst>_covariates.zarr` sidecar (includes `process_mask`) | `ponzi onboard` |
| C3 | pixel sample store | `ponzi onboard`, `export_pixels.py` |
| C5, C6, C21 | `pred`, `channels`, all-channel z (optional) | run sinks |
| C7, C8, C9 | `score.zarr`, `change.zarr`, `run_meta.json` | every run |
| C10 | forecasting stats | L0 sink |
| C11 | label store | monorepo `ponzi_paper` |
| C20 | row set | `ponzi.evaluation.rows` |
| C22 | `pvalues_<cal>.zarr` (uint8 codes `round(20 * -log10 p)`, 255 = none) | `ponzi pvalues` |
| C23 | `<burst>_masks.zarr` | `panels/masks.py`, `write_mask_store` |
| C24 | `summary.zarr` (Et, optionally E) | run sink |
| C25 | `events_<cal>.zarr` | `ponzi detect`, `detect-path` |
| C26 | `staged.zarr` | run sink (`--staged`) |
| C13 to C19 | AOI registry, request, validation table, AOI results, request config, engine report, data package | monorepo |

Full specifications are in `ponzi-core/docs/contracts/`.

### Registry layout

```
<registry>/
  <model_id>/
    model.json            ModelCard: sensor, forecaster, run_config_name,
                          run_config_hash, artifact_digest, provenance
    run_config.yaml
    artifact/             torchscript/model_ts.pt + meta.json (sha256 over
                          files = artifact_digest)
    calibrations/
      <calibration_id>/calibration.npz
```

Entries are immutable, and an existing id is refused. The registry lives on the HPC, not in git. The ponzi-models README lists two models (`tide_c30_gaza_f1p_mt0.2` with `mt02-plain` and `mt02-ceiling`; `tide_c30_pdcompact_mt0.4` with `mt04-plain` and `mt04-ceiling`). The specs and job files also refer to `tide_s1_mt04` and `tide_s1_mt04_aug` as registered, so the README table is behind.

## 5. Invariants the overhaul has to keep

1. **Identity by hash.** `config_hash` covers the resolved algorithm only. Anything that changes the computation goes in the run config. Anything that does not (paths, masks, threads, staged, context_keep, summaries) goes in the request.
2. **Calibration follows the run config.** A calibration is built for one config hash and one library major version, and refuses anything else.
3. **A training window is the inference window.** The trainer and the `tide` forecaster build inputs with the same library builder (`model_inputs`), equal on the bytes, and tests in ponzi-models enforce it.
4. **One opener.** Training, export, null runs and production all read through `open_input` (with masks for panels).
5. **Golden files lock numbers.** Any change that alters results for an existing config is marked RESULTS-CHANGING and is at least MINOR.
6. **Opt-in features are byte-neutral when off.** Each CR adds a field whose default leaves every store, stamp and digest unchanged.
7. **Layering.** The core imports no torch and no geospatial stack; `contracts` sits at the bottom; `grid` stands alone.
8. **Provenance.** Each registry entry records the ponzi-models commit; each store records `ponzi.__version__`.

## 6. Friction points for a packageable system

What currently ties the system to one checkout, one cluster or one person:

- **ponzi-models is not installable.** It has no package metadata and no environment of its own. Scripts import each other through `sys.path.insert(0, 'training')`, and tests run with `PYTHONPATH=<core>/src` and the core's `.pixi/envs/ml/bin/python`.
- **Paths are baked in.** Every job file hard-codes `DR`, `LAB`, the release path and node names. The trainer's defaults point at `$DR/training/majortom_v0.4_masked`.
- **The artifact path is in the hash.** The run configs of the registered models hold the monorepo-relative path to their weights, which is part of `config_hash`. `null_runs.py` works around this by starting each run in `RES/_model/<model>/`, where that path is a symlink into the registry.
- **The registry is a folder.** It is reached by `PONZI_MODEL_REGISTRY` or `PONZI_DATA_ROOT`, with no service, index or remote access. Only the HPC holds the real one.
- **Configs are spread out.** Run configs live in core `configs/run/` and in each registry entry. Recipe presets are Python constants. Onboarding configs live in `ponzi-apps` AOI folders. Fit specs live in ponzi-models. The generator of the run configs (`experiments.yaml`) is in the monorepo.
- **Requests have four sources.** Run requests mix flags, an args file, `PONZI_*` env and defaults. That works locally, but a service would need one serialised request form; `RunRequest.model_dump()` is already close.
- **Pieces are still in the monorepo.** Panel builders (stage 0), campaign planning, label producers, the decision log and the HPC ops rules (`ops/README.md`) have not moved. `ponzi-apps` is referenced but is not in this workspace.
- **The process is file and CLI bound.** Every stage is "path in, folder out", with completeness markers and `--overwrite` guards. There is no job state, queue or API; SLURM array indices (`--index N`) pick bursts.
- **Versions are pinned by folder.** Jobs select a library version by pointing `RELEASE` at a release checkout on the lab share, not by a package version.
- **Linux-64 and Python <3.13 only**, with torch pinned to 2.6 for the GPU nodes.
