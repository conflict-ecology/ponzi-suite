# C9: Run meta

Status: implemented 2026-09-07, `ponzi.contracts.run_meta` (package `packages/core`).

## Purpose

`{out_dir}/run_meta.json`: the human- and machine-readable record of one run. Everything a reader needs to reproduce the run and to sanity-check it without opening the stores.

## Producer and consumers

Producer: `ponzi.core.runner` at finalise; its presence marks a finished run. Consumers: `ponzi.evaluation.rows.open_run` (C20: checks `config.hash` and the window against the score store's stamp, takes the scored steps from `anchors`); `ponzi.calibration` (`write_pvalues` checks `config.hash` against the calibration and `ponzi_version` against its library; `staged_scores` reads the window); the ponzi-worker `run` stage (`config.hash` into the `ponzi-run` STAC Item, where the file is the `run_meta` asset, `ponzi.stac.items.run_item`, `ponzi_spec.collections`); ponzi-models `calibration.null_runs` (a folder with the file is skipped as finished) and `calibration.null_rows` (`mask.layer`); the byte-identity reproducibility tests (`packages/core/tests/test_runner.py`, `test_run_meta.py`: the file minus `timings`); people.

## Schema

`ponzi.contracts.run_meta.RunMeta` (pydantic, `extra="forbid"`), serialised with sorted keys and indent 2.

| Key | Type | Content |
|---|---|---|
| `contract_version` | int | 1 |
| `ponzi_version` | str | `ponzi.__version__` |
| `package_versions` | dict[str, str] | numpy, scipy, xarray, zarr, pydantic |
| `scoring_spec` | object | `name`, `hash`, `resolved` (the full `ScoringSpec.model_dump()`); `ScoringSpecRecord`, named `config` (`ConfigRecord`) before CR-070 |
| `request` | object | `RunRequest.model_dump(mode="json")` (C4a), every field: store paths as given, output dir, mode, dates, calibration window, sink flags, summaries, threads, memory cap, mask, `context_keep`, `staged`. Typed as a free `dict[str, Any]` in the model |
| `window` | object | `mode`, `t_lo`, `t_hi`, `t_requested`, `anchor_date_lo`, `anchor_date_hi`, `n_anchors`, and `covariate_cut`: null, or the record of the anchors that were not scored because a covariate the model reads is missing somewhere in their context or horizon rows (only at the ends of the range, a gap inside it is an error): `variables` (the ones checked), `t_lo_before`, `t_hi_before`, `t_lo`, `t_hi`, `n_cut`, `last_complete_acquisition`, and since CR-016 `cut_anchor_dates` (the dates of the anchors cut) and `missing` (per incomplete variable, the acquisition dates the cut anchors read at which it is missing). With `RunRequest.strict_covariates` the run fails instead of cutting |
| `input` | object | `coherence_store` (path), `digest` (from `store_digest`), `burst_id`, `sensor`, `T`, `Y`, `X`, `B`, `baseline_days`, `revisit_days`, `sidecar` (path or null), `sidecar_digest` (from `store_digest`, null without a sidecar), `extra_sidecar` and `extra_sidecar_digest` (`RunRequest.extra_sidecar`, null without one) |
| `pixels` | object | `n_valid`, `n_process`, `edge_margin` (int or null) |
| `mask` | object or null | CR-014, the named mask the run was restricted by: `store` (path), `digest` (`store_digest` of the mask store), `layer`, `window` (`[y0, y1, x0, x1]` on the store's grid, rows `y0 <= y < y1`, columns `x0 <= x < x1`; the grid of every output store), `n_layer` (pixels of the layer on the whole grid), `n_pixels` (the pixels processed). Null without a mask, absent in a run written before the entry. With a mask `input.Y` and `input.X` are still the store's own grid, and `pixels` counts the window |
| `anchors` | list[object] | One entry per scored anchor `t_lo .. t_hi` (a staged run's tail anchors, which have no final score, are not listed): `t`, `date`, `n_scored` (`n_channels > 0`), `n_change` (`change_period`), `n_event` (`change_event`), `n_judgeable` (`detectability > 0`) |
| `written` | list[str] | Files written, in this order where present: `score.zarr`, `change.zarr`, `forecasting_{scoring_spec_name}.npz`, `pred.zarr`, `channels.zarr`, `channels_z.zarr`, `summary.zarr`, `staged.zarr` |
| `threads` | object or null | The thread counts that acted: `requested` (`RunRequest.threads`), `omp_num_threads` (the environment variable as it stood while the anchors ran), `torch` (`torch.get_num_threads()` where a torch forecaster loaded it, else null), `pools` (the native pools `threadpoolctl` could see, by library prefix, null where it is not installed). Null in a run written before the entry |
| `timings` | object | `setup_s`, `loop_s`, `finalise_s`, `total_s`, plus the setup parts `open_s`, `prime_s`, `sinks_s`; the only non-deterministic content |

`pixels.edge_margin` is read from the process mask the input carried, never from the scoring spec: a pixel sample's own margin, or the `edge_margin` attr of the sidecar's `process_mask` layer. It is null when the input has no mask (the run processed the unmodified valid footprint) and when a mask carries no such attr. `n_process` always counts the mask the run actually used.

`digest` is a structural digest: BLAKE2b (16 bytes, hex) over the store's consolidated metadata (array names, shapes, dtypes, chunks, attrs), not over chunk bytes. It detects a swapped or regenerated store cheaply; it does not detect in-place edits of chunk data (archive stores are immutable, so that is acceptable).

## Invariants

- No wall-clock timestamps; durations only, isolated under `timings`.
- `threads` is a record of the environment, not of the result: two runs of the same request at different thread counts differ in it and in nothing else the file holds. A TiDE run is not bit-reproducible across thread counts, so it is the field that explains a difference of about 1e-7 in the scores.
- `scoring_spec.hash` equals `ponzi_scoring_spec_hash` in every output store; `window` equals the stamp in every output store (`open_run` refuses a run whose score store disagrees).
- `len(anchors) == window.n_anchors` (enforced by the model); `window.n_anchors == t_hi - t_lo + 1` since both modes score a contiguous range.

## Functions

`ponzi.contracts.run_meta`: `RUN_META_CONTRACT_VERSION`, `RunMeta` with its records (`ConfigRecord`, `WindowRecord`, `InputRecord`, `PixelRecord`, `MaskRecord`, `AnchorCount`, `ThreadsRecord`, `Timings`), `write_run_meta(path, meta)` (sorted keys, indent 2, trailing newline), `read_run_meta(path) -> RunMeta`, `identity_view(meta) -> dict` (the dump without `timings`, what the byte-identity test compares), `store_digest(path) -> str` (re-exported from `ponzi.contracts.base`). `RunMeta`, `read_run_meta`, `write_run_meta` and `identity_view` are also exported by `ponzi.contracts`.
