# C26: Staged store

Status: CR-021 (2026-10-21), `ponzi.contracts.staged`, `ponzi.core.staged`. Opt-in: written only with `RunRequest.staged` (`ponzi run --staged`; the ponzi-worker `run` stage's `staged` param, which a standard's workflow sets, `ponzi_models.standards.workflow`).

## Purpose

`{out_dir}/staged.zarr` (the `staged` asset of a `ponzi-run` Item; under the worker `{PONZI home}/cache/ponzi-run/<content id>/staged.zarr`): the scores of every anchor at the stages before its pyramid is full, so that a change is scored as its acquisitions arrive (progressive scoring). Anchor t is scored on the observations t .. t + H - 1; at stage s (1 .. H) the acquisitions t .. t + s - 1 exist and the pyramid cells with a horizon below s can be scored. Stage H is the run's final score in `score.zarr` (C7) and is not repeated here.

## Producer and consumers

Producer: the runner (`ponzi.core.sinks.ZarrStagedSink`, through the background writer). Consumers: `ponzi.calibration` (`staged_scores` and `staged_inputs` for a staged calibration, which validate the store; `write_pvalues` for the stage codes, C22, which reads `anomaly_score` and `ceiling_score` and the attrs `stages`, `staged_t_hi`, `staged_rule`), and through the codes the provisional detection spec (C25).

## The rule (`ponzi.core.staged`, recorded as `staged_rule`)

- Cells of stage s: `overlap & (h < s)`. With b5h5 on baselines 12 to 60 days at a 12-day revisit these are 5, 9, 12, 14 and 15 cells; at stage 1 the five pairs ending on acquisition t, so an anchor without that acquisition has no stage 1 score.
- Aggregation: `ponzi.core.aggregate.aggregate` with the stage's cells as `channels` and the run's weights `w_bh` (owner decision D2).
- Minimum of stage s: `m_s = ceil(min_channels * n_s / n_H)` in integers (D2), so `m_H = min_channels`; `min_channels` 9 gives 3, 6, 8, 9, 9 and 5 gives 2, 3, 4, 5, 5.
- The forecast of stage s (D1), as the forecaster declares `future_rows`: `unused` (it reads the context only, so the final forecast serves every stage: the rolling fits; stage s is then exactly the sub-pyramid of the run's channel scores) or `blanked` (it reads the covariate rows of the horizons, so stage s is its own forecast with the rows s .. H - 1 unknown, `AnchorAux.known_future = s`: TiDE, and an `external` callable with that attribute). The unknown rows are built exactly as the `unknown_future` training augmentation of ponzi-models builds them (`ponzi.core.forecast.model_inputs.unknown_future`): every physical channel (`bperp_abs`, `var`) `fcov_fillna`, the `obs` channels 0 under `future_obs: observed` and as the treatment gives a future row otherwise (1), the month kept. A strict model does not refuse a missing value in those rows. The `stored` replay and an `external` callable without the attribute are refused.

Changing the rule is a MAJOR change of the library; `staged_rule` records it so that `ponzi pvalues` can refuse a calibration made under another one (the config hash cannot see it).

## Anchors

The run's anchors as without the option (`t_lo` .. `t_hi` of the stamp, which is unchanged), each at the stages 1 .. H - 1, and then the anchors after `t_hi` up to `staged_t_hi`, each at the stages it has reached and without a final score: the stages whose acquisitions exist (`T - t` at the end of the series) and, for a forecaster that reads covariates, whose covariates over `[t - C, t + s - 1]` are complete (at the end of the series the weather of the newest acquisitions is often not out yet). The tail runs to the request's end (`ponzi.core.staged.staged_end`: the end of the event window in detection mode, else the last acquisition on or before `end_date`, the last acquisition without either, never before `t_hi`) and stops at the first anchor that has reached no stage; `staged_t_hi` is the last anchor reached (`t_hi` when none is). The horizon rows of such an anchor beyond the time axis are missing coherence and missing covariates on the nominal next dates (`revisit_days` apart), which only the month and a rolling fit's harmonics read. A monitoring update is an ordinary staged run over a trailing window (D6): the newest anchor at stage 1, the one before at stage 2, and so on; appending into one store is not part of CR-021.

## Arrays

| Name | Dims | dtype | Fill | Notes |
|---|---|---|---|---|
| `anomaly_score`, `difference`, `sensitivity`, `predicted_median`, `ceiling_score` | `(stage, time, y, x)` | float32 | NaN | C7's arrays at stage s (the full set, D5) |
| `n_channels` | `(stage, time, y, x)` | uint8 | 0 | the cells scored at stage s |
| `stage` | `(stage,)` | int16 | | 1 .. H - 1, one chunk |
| `process_pixels`, `time`, `y`, `x` | | | | as C7 |

Chunks `(1, 1, Y, X)`, whatever the request's `chunks`. Every slice not written reads as the fill. A masked run (CR-014) writes the store on its window. `validate_staged_store` checks the arrays, dtypes and shapes `(S, T, Y, X)`, the stage axis 1 .. H - 1, the stamp, the three attrs `stages`, `staged_t_hi` (not before the stamp's `t_hi`), `staged_rule`, and the consolidated metadata; `open_staged_store` opens it as a lazy Dataset after that.

## Attrs

The input attrs and the `RunStamp` as C7, plus:

| Attr | Meaning |
|---|---|
| `stages` | `[1, .., H - 1]` |
| `staged_t_hi` | the last anchor with any stage written (at least the stamp's `t_hi`) |
| `staged_rule` | `version`, `cells`, `min_channels_rule`, `n_cells` and `min_channels` per stage 1 .. H, `future_rows`, and for `blanked` `unknown_future_fill` |
| `stages_written` | per anchor from `t_lo` to `staged_t_hi`, the highest stage written; H where the anchor has its final score; set last (`finish_staged_store`) |

## Size

Six arrays per stage, 21 bytes per processed pixel, anchor and stage (the C7 set), so about `H - 1` times score.zarr: four times for H = 5.

## Memory and run time

`estimate_run_memory(..., staged=True)` adds `staged`: the pixel scores of the H - 1 stages of the anchors the writer may hold. A `blanked` forecaster makes one forward pass per stage after the final one is freed, so up to H passes per anchor (the run time of the forecast grows by that factor) without a larger peak.

## Invariants

- `score.zarr`, `change.zarr`, `summary.zarr` and every other output are the bytes of the run without the option, and `run_meta.json` differs only in `request.staged` and in `written` (tested for the rolling fits, a pooled fit, external callables and TiDE on a tiny model; compact loop, whole grid and masked).
- `unused`: stage s is `aggregate` of the run's channel scores on the stage's cells with `m_s`, on the bytes.
- What was known when: a staged run on the store cut after an acquisition holds, at its tail anchors, the stage scores of the run on the whole store (tested for the rolling fits, a blanked external and TiDE).
