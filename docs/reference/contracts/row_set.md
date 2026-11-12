# C20: Row set

`ponzi.contracts.row_set` and `ponzi.evaluation.rows` (package `packages/core`). The rows of ONE finished run for the evaluation primitive: `signal` rows and `null` rows read out of the run's stores at labelled pixels, with the pixel id, the step, the label code and the provenance of every row. Every metric of `ponzi.evaluation.metrics` runs on a row set; `ponzi.evaluation.events` concatenates row sets across bursts and pools events; the caller names the runs, the nulls and the classes. Nothing is recomputed from coherence: whatever a run's state machine or context rule did to its pixels is what the metrics see.

## Producer and consumers

Producers: `ponzi.evaluation.rows.score_rows` (C7, optionally C8's as-run flag), `channel_rows` (C6), `bag_rows` (C7 over C11's `bag` layer), `quiet_rows` (C7 or C6, LABEL FREE: the whole process mask at every scored step on the null side and an empty signal side). Consumers: `ponzi.evaluation.metrics`, `ponzi.evaluation.events` (burst to event, `concat_rows`, `pool_rows`); `ponzi-models null-rows` (`calibration.null_rows`: `quiet_rows` per burst of a panel, `concat_rows(offset_pixels=True)`, written with `RowSet.save` as `panel_{scoring_spec_name}_{setting}.npz`) and `ponzi-models calibrate` (`calibration.build`: `RowSet.load` of that file).

## Arrays

Arrays of one side share their first dimension `n`; `signal` and `null` are `(n,)` at level `scores` and `(n, B * H)` at level `channels` (column `b * H + h`, `ChannelAxis`).

| Field | Shape, dtype | Meaning |
|---|---|---|
| `level` | `scores` or `channels` | one value per row, or one per channel |
| `null_kind` | `temporal`, `spatial`, `spatiotemporal`, `bags`, `external`, `quiet` | how the null rows were selected; `quiet` is signal free by construction (`SIGNAL_FREE_KINDS`) |
| `signal`, `null` | `(n,)` or `(n, B * H)`, f32 as read, f64 once aggregated | the rows; NaN only at channel level (an invalid channel) |
| `signal_pixel`, `null_pixel` | `(n,)` int64 | the pixel id: the flat index `y * X + x` on the run's grid (`pixel_id_kind = flat`); the ground cell id after the ground dedup (`dedup_ground_cells`) (`ground_cell`); a flat id shifted by a per member offset after `concat_rows(offset_pixels=True)` (`offset`) |
| `signal_step`, `null_step` | `(n,)` int32 | the anchor index of the row (a bag's first acquisition) |
| `signal_label`, `null_label` | `(n,)` int16 | the label code of the row's pixel (its class); the class SET names are in the provenance |
| `signal_weight`, `null_weight` | `(n,)` f32 or absent | optional row weights |
| `signal_flag`, `null_flag` | `(n,)` uint8 or absent | `change_event` of the change store at the row (`flags=True`), the as-run threshold source |
| `signal_stratum`, `null_stratum` | `(n,)` int16 or absent | a reporting dimension per row; bags: the ordinal (0 null, 1 single, 2 first of a repeat pixel, 3 repeat) |
| `signal_extra`, `null_extra` | dict of `(n,)` arrays | builder side information; bags: `t0`, `t1`, `length`, `n_marked`, `n_scored`, `t_max`, `gap_steps`, `censored` |
| `channels` | `ChannelAxis` or absent | `baseline_days`, `H`, `overlap (B, H)`, `variable` (`z` or `u`); channel level only |
| `provenance` | `RowProvenance` | below |

## Provenance

`RowProvenance` (pydantic, `extra="forbid"`): `contract_version` (the hash of the row set's declaration, ponzi-core CR-085), `run_dir`, `scoring_spec_name`, `scoring_spec_hash`, `forecaster`, `run_mode`, `run_window {mode, t_lo, t_hi, date_lo, date_hi}` (the stamp), `input_store`, `input_digest` (C9's `input.digest`), `sidecar_digest`, `mask_digest` (BLAKE2b over the score store's `process_pixels` shape and bytes, so a subset run without a sidecar has one), `extent {T, Y, X}`, `context_window`, `horizon_length`, `min_channels`, `baseline_days`, `revisit_days`, `label_store`, `label_digest`, `class_sets` (name to codes, as passed), `null_spec` (the `NullSpec` dump), `signal_steps`, `null_steps` (sorted unique), `pixel_set_digest` (BLAKE2b over the sorted unique pixel ids of both sides), `pixel_id_kind` (`flat`; `ground_cell` after the ground dedup (`dedup_ground_cells`); `pooled` for a pool; `offset` for a concatenation of different runs whose flat ids were shifted apart), `aggregated_cols` (set by `aggregate`), `dropped {signal, null}` with `outside_process`, `unscored`, `below_finite_rule`, `label_zero`, `external_null` (the external null's own provenance), and for an event set or a pool `members` (one record per burst or event, in order, the fields above then holding the shared values and the joined digests) and `dedup` (the ground dedup or pooling record). `check_comparable` compares two event sets member by member.

## Null specifications

`NullSpec` (`ponzi.evaluation.rows`): `temporal(steps)` (the signal pixels' own rows at the steps, every step a fake event), `spatial(codes, step=None)` (the pixels of the null codes at the signal step), `spatiotemporal(codes, steps)`, `bags(codes)` (the bags of the label store whose class is in the codes), `quiet(steps)` (`quiet_rows`' own kind: no codes and no labels, every processable pixel at every step), `external(rows, side)` (one side of another row set taken as it is; the pairing checks are not applied between the two sides, the provenance records the source). Every step index and code is an argument the caller derived from its own dataset rules; core hard codes none.

## Invariants

- Rows come from finished runs only: `run_meta.json` and `score.zarr` exist, the store stamp equals the record (`scoring_spec.hash`, window; `open_run`).
- A step of the signal or of a temporal, spatial or spatiotemporal null was scored by the run (`run_meta.anchors`); otherwise the builder refuses and names the missing steps with their dates. A detection run serves the spatial null only.
- A row with a NaN score at a scored step is not in the set and is counted in `dropped.unscored` (at channel level: a row with every channel NaN). A bag none of whose acquisitions was scored is dropped the same way; a partially scored bag is kept with `n_scored`.
- Labelled pixels outside the run's process mask are counted in `dropped.outside_process`.
- The label grid is the run grid; at least one code of the class sets (and of a null class) must occur in the label store, a class an event lacks simply yields no rows.
- `aggregate(cols)` turns channel rows into score rows by the unweighted NaN aware mean with the 60 percent finite rule (`aggregate_rows`), dropping and counting the rows below it.
- Pairing (`pair`, `check_comparable`) intersects each side on the pixel id and REFUSES when the input digest, the mask digest, the extent, the pixel id kind, the signal steps or the null steps differ; a different stamped run window, level, null kind or label digest is reported as a warning (the compared rows must agree, not the range a run happened to score).
- `select(codes, null_codes=None)` keeps the signal rows of the codes; the null side follows the same codes only when it is the pixels' own rows (temporal), else it is kept whole unless `null_codes` is given.

### Quiet rows

`quiet_rows(run, *, steps=None, level="scores"|"channels", variable="z", stratum=None, weight=None)` is the label free builder: the background panel a design table is read against.

- The NULL side is every pixel of the run's process mask at every step of `steps`, by default every anchor the run scored (`run_meta.anchors`); a step the run did not score is refused by name, as for every other builder. The SIGNAL side is empty, shape `(0,)` at level `scores` and `(0, B * H)` at level `channels`.
- There is no label store and no class set: every label is `-1`, `provenance.label_store` and `label_digest` are the empty strings, `class_sets` is empty and `null_spec` is `{"kind": "quiet", "steps": [...]}`. A NaN value at a scored step is dropped and counted `unscored`, so `n_null = pixels * steps - unscored`.
- `stratum` and `weight` are optional `(Y, X)` arrays the CALLER derived (a settlement class, a cell, an inclusion weight); core only gathers them at the kept pixels and learns nothing about the dataset. A map that is not the run grid is refused.
- `aggregate`, `where`, `save`, `load`, and `ponzi.evaluation.events`' `concat_rows` and `pool_rows` work unchanged. `select` is REFUSED (every label is `-1`, so a class selection would silently return nothing: filter on the stratum with `where`), and so is `pair` on either side (a quiet set is a reference over its own pixels, never a variant of the same event).
- Metrics: the groups that need a signal (`separation`, `rank`, `channels`, `bag_extras`) REFUSE a signal free set by name instead of returning NaN; the null only groups (`distribution`, which reports the signal half as NaN, `operating_points`, whose `fpr` is the panel's point and whose `recall` is NaN, `calibration`) run on it, and `metrics(rows)` defaults to those three. The refusal is on the null KIND, not on an empty signal side as such: an event that simply lacks a class keeps the NaN rows the summaries count and exclude.

## Metrics on a row set

`ponzi.evaluation.metrics`: one function per group, `group(rows, thresholds=None, *, as_run=False, cls="", group_ids=None, pit_reference=None) -> DataFrame`, on a score level set (`channels(rows, geometries, reference, ...)` on a channel level set with a geometry dictionary, `forecasting(run, t_lo, t_hi, *, cls="")` on a `RunHandle` over C10); `metrics(rows, groups=None, ...)` concatenates several, by default `distribution`, `separation`, `rank`, `operating_points`, `calibration` (plus `bag_extras` on bag rows). Weights are the set's own; thresholds are a name to value mapping the caller derived (core derives none); `group_ids` names the event of every row for the PIT transform. Output columns: `metric, value, n, k, lo, hi, threshold_name, threshold_value, null_kind, cls, stratum`; `k`, `lo`, `hi` are the count and Jeffreys interval of a rate. Groups: `distribution`, `separation` (`dprime`, `dprime_robust`, `dprime_pit` against the `pit_reference` null with `dprime_pit_bound`, `dprime_pit_matched` against the rows' own null, `dprime_auc`), `rank` (`auc`, `prauc`, `prevalence`), `operating_points` (`fpr` per 1,000, `recall`, `threshold` per threshold; `as_run` from the flags), `calibration` (`exceed_z2`, `exceed_z3` with the Gaussian values, `coverage_90`; on `u` channel rows `pit_ks`, `pit_coverage_90`, `pit_bin_*`), `channels` (per geometry: the aggregated rows' distribution and separation, `n_cells`, `n_eff`, `n_eff_plain`, `dprime_robust_reference`, `skill_ratio`, `skill_diff`; per channel `channel:b{b}h{h}`: `null_sd`, `null_rsd`, `n_null_rows`), `bag_extras` (`null_pixel_years`, `alarms_per_pixel_year`, `share_pixels_alarmed`, `latency`). Bags are a level of the rows: every group runs on bag rows.

## File

`RowSet.save(path)` writes one compressed `.npz` (`np.savez_compressed`): the arrays under their field names (absent optional ones left out; `signal_extra__name` for extras) and `meta`, a canonical json string with `contract_version`, the level, the null kind, the provenance and the channel axis (null at level `scores`). `RowSet.load(path)` reads it back without pickles.

## Functions

`ponzi.contracts.row_set`: `RowSet` (`select`, `where`, `aggregate`, `with_weights`, `pair`, `save`, `load`, `n_signal`, `n_null`, `n_pixels`, `pixel_ids`), `RowProvenance`, `RunWindowRecord`, `ExtentRecord`, `ChannelAxis`, `DropCounts`, `PairReport`, `RowSetError`, `check_comparable`, `aggregate_rows`, `pixel_set_digest`, and the constants `LEVELS`, `NULL_KINDS`, `PIXEL_ID_KINDS`, `SIGNAL_FREE_KINDS`, `MIN_FINITE_FRAC` (0.6), `ROW_SET_CONTRACT_VERSION`. `ponzi.evaluation.rows`: `NullSpec`, `open_run(run_dir) -> RunHandle` (a context manager over the record, the score store and the paths of the change, channel and forecasting stats files), `score_rows`, `channel_rows`, `bag_rows`, `quiet_rows`. `ponzi.evaluation.events`: `concat_rows(parts, *, dedup=None, pixel_id_kind=None, weights=None, member_key="burst", offset_pixels=False)`, with `offset_pixels=True` and `pixel_offsets` (each part shifted by the grid sizes `Y * X` of the parts before it) for parts that are different places rather than the same ground read twice (a background panel's bursts); `pool_rows`, `dedup_ground_cells`, `event_rows`.
