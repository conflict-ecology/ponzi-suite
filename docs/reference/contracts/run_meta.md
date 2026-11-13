# C9: Run meta

`ponzi.contracts.run_meta` (package `packages/core`). `{out_dir}/run_meta.json`: the human- and machine-readable record of one run. Everything a reader needs to reproduce the run and to sanity-check it without opening the stores.

## Producer and consumers

Producer: `ponzi.core.runner` at finalise; its presence marks a finished run. Consumers: `ponzi.evaluation.rows.open_run` (C20: checks `scoring_spec.hash` and the window against the score store's stamp, takes the scored steps from `anchors`, finds C10 by `scoring_spec.name`); `ponzi.calibration` (`write_pvalues` checks `scoring_spec.hash` against the calibration and `ponzi_version` against its library, C22; `staged_scores` reads the window); the worker stage `run` (`scoring_spec.hash` into the `ponzi-run` Item); `ponzi-models null-runs` (a folder with the file is skipped as finished) and `null-rows` (`mask.layer`); the byte-identity tests (`packages/core/tests/test_runner.py`, `test_run_meta.py`: the file minus `timings`).

## Schema

`RunMeta` (pydantic, `extra="forbid"`), written with sorted keys, indent 2 and a trailing newline.

| Key | Type | Content |
|---|---|---|
| `contract_version` | str | the hash of the contract's declaration (ponzi-core CR-085; pinned in `test_contract_versions.py`) |
| `ponzi_version` | str | `ponzi.__version__` |
| `package_versions` | dict[str, str] | numpy, scipy, xarray, zarr, pydantic |
| `scoring_spec` | object | `ScoringSpecRecord`: `name`, `hash`, `resolved` (the full `ScoringSpec.model_dump()`) |
| `request` | object | `RunRequest.model_dump(mode="json")` (C4a), every field; typed as a free `dict[str, Any]` |
| `window` | object | `mode`, `t_lo`, `t_hi`, `t_requested`, `anchor_date_lo`, `anchor_date_hi`, `n_anchors`, and `covariate_cut`: null, or the record of the anchors not scored because a covariate the model reads is missing somewhere in their context or horizon rows (only at the ends of the range; a gap inside it is an error): `variables` (the ones checked), `t_lo_before`, `t_hi_before`, `t_lo`, `t_hi`, `n_cut`, `last_complete_acquisition`, `cut_anchor_dates`, and `missing` (per incomplete variable, the acquisition dates the cut anchors read at which it is missing). With `RunRequest.strict_covariates` the run fails instead |
| `input` | object | `coherence_store` (path: the layer holding the target, or the sample), `digest`, `target` (the variable forecast, `scoring.target`, CR-102), `layers` (every layer read, in the order given: `path`, `layer`, `digest`; a sample is one layer `sample`), `burst_id`, `sensor`, `T`, `Y`, `X`, `B`, `baseline_days`, `revisit_days`, `sidecar` and `sidecar_digest` (the deprecated `sidecar` of the request), `extra_sidecar` and `extra_sidecar_digest` (null without one). `Y`, `X` are the store's own grid, also in a masked run. Digests are structural ([shared conventions](../contracts.md#shared-conventions)) |
| `pixels` | object | `n_valid`, `n_process`, `edge_margin` (int or null). In a masked run both counts are on the window |
| `mask` | object or null | The named mask the run was restricted by (C23): `store` (path), `digest`, `layer`, `window` (`[y0, y1, x0, x1]` on the store's grid, rows `y0 <= y < y1`, columns `x0 <= x < x1`: the grid of every output store), `n_layer` (pixels of the layer on the whole grid), `n_pixels` (the pixels processed, `pixels.n_process`). Null without a mask |
| `anchors` | list[object] | One entry per scored anchor `t_lo .. t_hi` (a staged run's tail anchors, which have no final score, are not listed): `t`, `date`, `n_scored` (`n_channels > 0`), `n_change` (`change_period`), `n_event` (`change_event`), `n_judgeable` (`detectability > 0`) |
| `written` | list[str] | Files written, in this order where present: `score.zarr`, `change.zarr`, `forecasting_{scoring_spec_name}.npz`, `pred.zarr`, `channels.zarr`, `channels_z.zarr`, `summary.zarr`, `staged.zarr` |
| `threads` | object or null | The thread counts that acted: `requested` (`RunRequest.threads`), `omp_num_threads` (the environment variable while the anchors ran), `torch` (`torch.get_num_threads()` where a torch forecaster loaded it, else null), `pools` (the native pools `threadpoolctl` could see, by library prefix; null where it is not installed) |
| `timings` | object | `setup_s`, `loop_s`, `finalise_s`, `total_s`, and the setup parts `open_s`, `prime_s`, `sinks_s`; the only non-deterministic content |

`pixels.edge_margin` is read from the process mask the input carried, never from the scoring spec: a pixel sample's own margin, or the `edge_margin` attr of the sidecar's `process_mask` layer. It is null when the input has no mask (the run processed the unmodified valid footprint) or the mask carries no such attr. `n_process` always counts the mask the run used.

## Invariants

- No wall-clock timestamps; durations only, under `timings`.
- `threads` records the environment, not the result: two runs of the same request at different thread counts differ in it and in nothing else the file holds. A TiDE run with `batching: legacy` is not bit-reproducible across thread counts (C4a), so it is the field that explains a difference of about 1e-7 in the scores.
- `scoring_spec.hash` equals `ponzi_scoring_spec_hash` in every output store; `window` equals the stamp in every output store (`open_run` refuses a run whose score store disagrees).
- `len(anchors) == window.n_anchors` (enforced by the model) `== t_hi - t_lo + 1`: both modes score a contiguous range.

## Functions

`ponzi.contracts.run_meta`: `RUN_META_CONTRACT_VERSION`, `RunMeta` with its records (`ScoringSpecRecord`, `WindowRecord`, `InputRecord`, `PixelRecord`, `MaskRecord`, `AnchorCount`, `ThreadsRecord`, `Timings`), `write_run_meta(path, meta)`, `read_run_meta(path) -> RunMeta`, `identity_view(meta) -> dict` (the dump without `timings`, what the byte-identity test compares), `store_digest` (re-exported from `ponzi.contracts.base`). `RunMeta`, `read_run_meta`, `write_run_meta` and `identity_view` are also exported by `ponzi.contracts`.
