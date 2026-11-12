# Store contracts

Every store that crosses a stage boundary has a written contract: its arrays or columns, dtypes, fills, chunks, attrs and invariants, and the functions that open, write and validate it. The schemas and checks are code in ponzi-core: `ponzi.contracts` (one module per store), `ponzi.core.scoring_spec`, `ponzi.core.runner`, `ponzi.core.sample`, `ponzi.core.forecasting_stats` and `ponzi_pipeline.onboard.onboarding_spec`.

Each contract's version is the hash of its declaration in the code, pinned by a test ([Versions](versions.md#store-contracts-and-record-files-the-hash-of-the-declaration)).

The code is the authority: where a contract and the code disagree, the contract is fixed ([Changing what a store holds](../contributing/agents/contributing.md#changing-what-a-store-holds-code-first)).

| # | File | Producer | Read by |
|---|---|---|---|
| C1 | [coherence_store.md](contracts/coherence_store.md) | `ponzi_pipeline.assemble` (`ponzi-pipeline assemble`, worker `assemble`); a store made elsewhere enters through worker `ingest-coherence` | `ponzi.core.runner.open_input`, `ponzi validate-store`, `ponzi_pipeline.onboard`, `ponzi_models` (through `open_input`) |
| C2 | [covariates_sidecar.md](contracts/covariates_sidecar.md) | `ponzi_pipeline.onboard.onboard_store` (`ponzi-pipeline onboard`, worker `onboard`) | the runner (`open_input`), the onboarding's `sample` step, `ponzi_models` (masked input) |
| C3 | [pixel_sample.md](contracts/pixel_sample.md) | the onboarding's `sample` step (`ponzi.core.sample.extract_sample`), `ponzi-models export-pixels` | the runner (`open_input`), `ponzi_models` training, `export-pixels --check` |
| C4 | [scoring_spec.md](contracts/scoring_spec.md) | the user (ponzi-suite `specs/scoring_specs/`, the PONZI home's), the registry's `scoring_spec.yaml` | `ponzi run`, worker `run`, `ponzi_models` (`null-runs`, the registry, the standards workflow) |
| C4a | [run_request.md](contracts/run_request.md) | `ponzi run`, worker `run`, `ponzi-models null-runs` | `ponzi.core.runner.run` |
| C4b | [command_args.md](contracts/command_args.md) | the user (flags, `--args-file`, `PONZI_*`) | `ponzi.core.cli` (`run`, `replay`, `forecasting-summary`) |
| C5 | [prediction_store.md](contracts/prediction_store.md) | the runner (optional, `save_pred`) | `StoredForecaster` (forecaster `stored`) |
| C6 | [channel_scores_store.md](contracts/channel_scores_store.md) | the runner (optional, `save_channels`) | `ponzi.evaluation.rows`, `ponzi-models null-rows` |
| C7 | [score_store.md](contracts/score_store.md) | the runner (always) | `ponzi replay`, `ponzi.calibration` (`ponzi pvalues`), `ponzi.evaluation.rows`, `ponzi-models null-rows` |
| C8 | [change_store.md](contracts/change_store.md) | the runner (always), `ponzi replay` | `ponzi.evaluation.rows` |
| C9 | [run_meta.md](contracts/run_meta.md) | the runner | `ponzi.evaluation.rows.open_run`, `ponzi.calibration`, worker `run`, `ponzi-models null-runs`, `null-rows` |
| C10 | [forecasting_stats.md](contracts/forecasting_stats.md) | the runner (optional, `forecasting_stats`) | `ponzi forecasting-summary`, `ponzi.evaluation.forecasting`, `ponzi.evaluation.metrics.forecasting` |
| C11 | [label_store.md](contracts/label_store.md) | `ponzi.evaluation.labels.write_labels` (no command or stage) | `ponzi.evaluation` |
| C15 | [validation_table.md](contracts/validation_table.md) | `ponzi.contracts.validate.validate_store` (`ponzi validate-store`) | the caller |
| C16 | [aoi_results.md](contracts/aoi_results.md) | `ponzi.evaluation.events.write_design_table` | `read_design_table` |
| C17 | [request_config.md](contracts/request_config.md) | the user (ponzi-suite `specs/onboarding_specs/`, or an `onboarding:` section) | `ponzi_pipeline.onboard.onboarding_spec` (`ponzi-pipeline onboard`, `weather-prefetch`), worker `onboard` |
| C18 | [engine_report.md](contracts/engine_report.md) | `ponzi_pipeline.engine` (through `assemble`) | `validate_store`, worker `ingest-coherence` (requires it) |
| C20 | [row_set.md](contracts/row_set.md) | `ponzi.evaluation.rows`, `ponzi-models null-rows` | `ponzi.evaluation.metrics`, `ponzi.evaluation.events`, `ponzi-models calibrate` |
| C21 | [channel_z_store.md](contracts/channel_z_store.md) | the runner (optional, `save_all_channels`) | side analyses only |
| C22 | [pvalue_store.md](contracts/pvalue_store.md) | `ponzi.calibration.write_pvalues` (`ponzi pvalues`, worker `pvalues`) | `ponzi.products` (`ponzi detect`, `detect-path`, `tile`) |
| C23 | [mask_store.md](contracts/mask_store.md) | `ponzi.contracts.masks.write_mask_store`; for a panel `ponzi_models.panels.draw` (`ponzi-models panel-build`) | the runner (`open_input`), `ponzi-models null-runs`, the panel's masked input (training, `export-pixels`) |
| C24 | [summary_store.md](contracts/summary_store.md) | the runner (optional, `summaries`) | `ponzi.products` |
| C25 | [events_store.md](contracts/events_store.md) | `ponzi.products` (`ponzi detect`, `detect-path`, `tile`; worker `detect`, `tile`) | ponzi-visual (`src/events.ts`) |
| C26 | [staged_store.md](contracts/staged_store.md) | the runner (optional, `staged`) | `ponzi.calibration` (staged calibration, stage codes) |

C12, C13, C14 and C19 were removed: no code reads or writes them.

## Shared conventions

What every contract below relies on and does not repeat.

- **Zarr.** Every writer writes zarr v3 with `dimension_names` and consolidated metadata, and every reader refuses another zarr format (ponzi-core CR-086).
- **Open, write, validate.** An `open_*` function that validates raises `ContractError` (`ponzi.contracts.base`) on a failed check. A `validate_*` function returns a `ValidationReport`: a `subject` and one `CheckResult` per named check (`name`, `severity` one of `ok`, `info`, `warn`, `fail`, `detail`, `value`, `items`); `ok` is false when any check failed. The `consolidated` check warns when the metadata is not consolidated.
- **Structural digest.** `store_digest(path)` (`ponzi.contracts.base`) is BLAKE2b (16 bytes, hex) over the canonical JSON of the group attrs and each array's name, shape, dtype, chunks and attrs, never the chunk bytes. It detects a swapped or regenerated store cheaply, not an in-place edit of chunk data (archive stores are immutable). Spec hashes are `ponzi_spec.identity.spec_hash` ([Configuration](../service/configuration.md#specs-and-other-configs)).
- **Time.** An output store writes `time` as int64 nanoseconds with the attrs `units` (`nanoseconds since 1970-01-01`) and `calendar` (`proleptic_gregorian`), so it decodes to `datetime64[ns]` under any xarray setting.
- **A run's stores.** The output stores of one run (C5, C6, C7, C8, C21, C24, C26) share the grid, the copied input attrs and the run stamp defined in [C7](contracts/score_store.md#grid-and-attrs-of-a-runs-stores).
- **Catalog.** Which STAC Collection and asset a store is: [STAC profile](../using/stac-profile.md). Under the worker each output is one cache entry, `cache/<collection>/<content id>/` ([Paths](../getting-started/paths.md)).
