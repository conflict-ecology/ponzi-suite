# Store contracts

Every store that crosses a stage boundary has a written contract, kept here in the suite (`docs/reference/contracts/`, CR-071): its arrays or columns, dtypes, fills, chunks, attrs and invariants, and the functions that open, write and validate it. The code that checks them is in ponzi-core.

The pydantic schemas live in `ponzi.contracts` (and `ponzi.core.scoring_spec`, `ponzi.core.runner`, `ponzi_pipeline.onboard.onboarding_spec`).

Checked against the code on 2026-11-04 (CR-050). Removed then, because no code in ponzi-core or ponzi-service reads or writes them any more: C12 (eval result), C13 (AOI registry), C14 (frozen request) and C19 (data package). C15, C16 and C17 keep only the part that code here still uses.

| # | File | Producer | Read by |
|---|---|---|---|
| C1 | [coherence_store.md](contracts/coherence_store.md) | `ponzi_pipeline.assemble` (`ponzi-pipeline assemble`, worker `assemble`); outside stores through worker `ingest-coherence` | `ponzi.core.runner.open_input`, onboarding, `ponzi_models` |
| C2 | [covariates_sidecar.md](contracts/covariates_sidecar.md) | `ponzi_pipeline.onboard.onboard` (`ponzi-pipeline onboard`, worker `onboard`) | the runner |
| C3 | [pixel_sample.md](contracts/pixel_sample.md) | `ponzi_pipeline.onboard.onboard`, `ponzi-models export-pixels` | the runner, `ponzi_models` training |
| C4 | [scoring_spec.md](contracts/scoring_spec.md) | the user (ponzi-suite `scoring_specs/`), the registry's `scoring_spec.yaml` | `ponzi run`, worker `run`, `ponzi_models` |
| C4a | [run_request.md](contracts/run_request.md) | `ponzi run`, worker `run`, `ponzi-models null-runs` | the runner |
| C4b | [command_args.md](contracts/command_args.md) | the user (`run`, `replay`, `forecasting-summary`) | `ponzi.core.cli` |
| C5 | [prediction_store.md](contracts/prediction_store.md) | the runner (optional, `save_pred`) | `StoredForecaster` |
| C6 | [channel_scores_store.md](contracts/channel_scores_store.md) | the runner (optional, `save_channels`) | `ponzi.evaluation.rows`, `ponzi-models null-rows` |
| C7 | [score_store.md](contracts/score_store.md) | the runner (always) | calibration, evaluation rows, `null-rows` |
| C8 | [change_store.md](contracts/change_store.md) | the runner (always), `ponzi replay` | evaluation rows |
| C9 | [run_meta.md](contracts/run_meta.md) | the runner | `open_run`, calibration, worker, `ponzi_models` |
| C10 | [forecasting_stats.md](contracts/forecasting_stats.md) | the runner (optional, `forecasting_stats`) | `ponzi forecasting-summary`, `ponzi.evaluation.metrics` |
| C11 | [label_store.md](contracts/label_store.md) | `ponzi.evaluation.labels.write_labels` (no caller outside tests today) | `ponzi.evaluation` |
| C15 | [validation_table.md](contracts/validation_table.md) | `ponzi.contracts.validate.validate_store` (`ponzi validate-store`) | onboarding (`refuse_write`), the caller |
| C16 | [aoi_results.md](contracts/aoi_results.md) | `ponzi.evaluation` (the design table, `write_design_table`) | `read_design_table` |
| C17 | [request_config.md](contracts/request_config.md) | the user (its `onboarding:` section) | `ponzi_pipeline.onboard.onboarding_spec`, worker `onboard` |
| C18 | [engine_report.md](contracts/engine_report.md) | `ponzi_pipeline.engine` (through `assemble`) | `validate_store`, worker `ingest-coherence` |
| C20 | [row_set.md](contracts/row_set.md) | `ponzi.evaluation.rows`, `ponzi-models null-rows` | `ponzi-models calibrate` |
| C21 | [channel_z_store.md](contracts/channel_z_store.md) | the runner (optional, `save_all_channels`) | analysis |
| C22 | [pvalue_store.md](contracts/pvalue_store.md) | `ponzi.calibration.write_pvalues` (`ponzi pvalues`, worker `pvalues`) | `ponzi.products` (detect, tile) |
| C23 | [mask_store.md](contracts/mask_store.md) | `ponzi_models.panels.draw` (`ponzi-models panel-build`), `write_mask_store` | the runner, `null-runs`, training |
| C24 | [summary_store.md](contracts/summary_store.md) | the runner (optional, `summaries`) | `ponzi.products` |
| C25 | [events_store.md](contracts/events_store.md) | `ponzi.products.detect`, `detect_path`, `tile_path` (`ponzi detect`, `detect-path`, `tile`; worker `detect`, `tile`) | ponzi-visual, the server's assets |
| C26 | [staged_store.md](contracts/staged_store.md) | the runner (optional, `staged`) | `ponzi.calibration` (staged p-values) |
