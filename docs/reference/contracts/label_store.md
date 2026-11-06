# C11: Label store

Status: implemented 2026-09-07, `ponzi.evaluation.labels` (packages/core); the `bag` layer added 2026-09-16. STAC collection `ponzi-labels` (asset `labels`).

## Purpose

The only label input evaluation reads. Which codes are positive and which are the null is never stored here: class sets are arguments to every metric.

## Producer and consumers

Producers: whoever calls `write_labels`; no command or ponzi-worker stage writes one (there is no BRIGHT, UNOSAT or crater producer here), so today the tests only. Consumers: `ponzi.evaluation` (`open_labels`, read by `ponzi.evaluation.events.event_rows` and by `score_rows`, `channel_rows` and `bag_rows` of `ponzi.evaluation.rows`); no command or stage reads one.

## Arrays

| Name | Dims | dtype | Fill | Meaning |
|---|---|---|---|---|
| `label` | `(y, x)` or `(time, y, x)` | int16 | 0 | 0 = excluded; `k > 0` caller-defined class. The 3-d form gives the class per acquisition; the bag class is the highest nonzero code over the evaluated anchors |
| `bag` | `(time, y, x)` | int32 | 0 | Optional. `k > 0` = the id of the bag the acquisition belongs to; 0 = in no bag. An id is unique in the store, belongs to one pixel, and `label` is constant inside it. Replaces the former `window` layer: `LabelSet.window` is the derived `bag > 0`, and a legacy store with `window` only is converted on read, one id per contiguous run of a pixel |
| `onset` | `(y, x)` | int32 | -1 | Optional. Index of the first acquisition after the true change |
| `weight` | `(y, x)` | float32 | NaN | Optional |
| `stratum` | `(y, x)` | int16 | 0 | Optional reporting dimension |

Further arrays a producer adds (`write_labels(..., extra=)`, on the label grid, with or without a leading `time`) are ignored by the evaluation. Chunks: one per acquisition, the whole grid each; the store is zarr v3 with dimension names and consolidated metadata. Attrs: `label_schema` (1), `label_names {code: name}`, `stratum_names`, free producer attrs; `open_labels` adds `bag_from_legacy_window` to the attrs it returns for a converted legacy store. The label grid equals the run grid (`expect_shape`; or the `px` pixel order for a sampled run, dims `(px,)`).

## Bags

The producer decides every bag when it writes the store, and the evaluation only ever reduces a score over a bag id (`ponzi.evaluation.rows.bag_rows`: the window maximum of `anomaly_score` over the bag's marked acquisitions). Three kinds of bag live side by side, told apart by their label and their dates: damage bags (one per assessment interval with new damage), negative assessment bags (a pixel assessed and found undamaged over an interval, a null bag with a real meaning), and pre-event quiet bags (disjoint blocks of the pre-event acquisitions, the quiet null of the monitoring use case; the block rule is in the attrs). Which label codes form the signal and which the null is, as always, the caller's class sets.

A worked pixel of the Gaza interval store (UNOSAT codes 1 intact, 2 damaged; conflict start 2023-10-07; assessments A1 2023-11-07 intact, A2 2024-01-06 moderate, A3 2024-03-02 moderate, A4 2024-05-03 destroyed; 12 day cadence):

| t | date | label | bag | why |
|---|---|---|---|---|
| 0..9 | 2022-10 .. 2023-02 | 0 | 0 | before the first pre-event block |
| 10..14, 15..19, 20..24, 25..29 | 2023-02 .. 2023-09 | 1 | 1, 2, 3, 4 | pre-event quiet bags, 60 days each |
| 30 | 2023-10-02 | 0 | 0 | last pre-conflict acquisition, in no interval |
| 31..32 | 2023-10-15, 10-27 | 1 | 5 | conflict start to A1, assessed intact; a negative bag ends at the last acquisition on or before A1 |
| 33..38 | 2023-11-08 .. 2024-01-07 | 2 | 6 | A1 to A2, damage appears; the bag runs to the first acquisition after A2 |
| 39..42 | 2024-01-19 .. 02-24 | 0 | 0 | A2 to A3, same grade: excluded, nothing new to find |
| 43..48 | 2024-03-07 .. 05-06 | 2 | 7 | A3 to A4, grade increase: a repeat damage bag |
| 49..78 | 2024-05 .. 2025-05 | 0 | 0 | destroyed, no further grade possible |

Bags 5 and 6 are adjacent with different labels, which is why the id and not a run of a flag defines the bag. `bag_rows` derives per bag its ordinal among the pixel's signal bags (single, first of a repeat pixel, repeat), the gap to the previous one and whether it is censored at the last marked acquisition.

## Functions

`open_labels(path, *, expect_shape=None, T=None) -> LabelSet` (v2 legacy stores such as the BRIGHT labels open unchanged; `LabelSet.bags()` tabulates the bags), `write_labels(path, label, *, bag, onset, weight, stratum, names, stratum_names, attrs, extra)` (zarr v3; refuses a bag layer that breaks the id invariants), `bag_table(bag, label_t) -> BagTable`, `bags_from_window(window)` (the legacy conversion), `validate_class_sets(labels, positive_sets, negative_sets)`.

## Formats

The `bag` id layer replaced the `window` flag on 2026-09-16; the writer emits zarr v3 and the reader accepts both formats and the legacy flag.
