# CR-021: progressive scoring of an anchor as its pyramid fills

- **Requested by / date:** owner, 2026-10-15
- **Owner decisions 2026-10-15:** D1 the same model serves every stage: train it with the future covariate rows randomly blanked (as the context), the fill of unknown rows is only a stopgap until that model exists. D2 the proportional minimum. D3 one run config, one calibration file with a mapping per stage. D4 provisional flags at every stage. D5 the full set per stage (anomaly and ceiling scores, n_channels, difference, sensitivity, predicted median). D6 start with A (each update a small dated run folder), but B is the target: one growing store per burst, appended per update, where a superseded value is marked as such (which stage it came from, when it was replaced) instead of silently overwritten, plus a write-all-stages mode for analysis that keeps every stage; B gets its own change request. D7 run the effective-context test first on the full-pyramid calibration of tide_s1_mt04, then on the augmented candidate, bins 12 to 15, 16 to 20, 21 to 25, 26 to 30, rule: a bin's 1 in 1,000 rate outside 0.67 to 1.5 times nominal with its interval excluding nominal adds context classes.
- **Status:** signed off and merged into main 2026-10-21 (owner), released in v0.2.3.

## Why

An anchor t is scored on the observations t .. t + H - 1 (`buffer.targets`), so the runner scores it only once the time axis reaches t + H - 1: the scorable range is [C, T - H] (`windows.full_anchor_range`). With H = 5 the first score of a change at gap t arrives four acquisitions after t, 48 days at a 12-day revisit. For near-real-time monitoring the anchor should be scored as its observations arrive: the forecast made at t (all H horizons, from the context before t) is scored at stage s = 1 .. H, where s is the number of horizons whose acquisition date has been reached. No model is refit.

Cells per stage, b5h5 (baselines 12 to 60 days, 12-day revisit, `overlap_mask`: cell (b, h) exists iff `baseline_days[b] > 12 h`; the pyramid cells are the pairs spanning gap t):

| stage s (horizons observed) | 1 | 2 | 3 | 4 | 5 (today) |
| --- | --- | --- | --- | --- | --- |
| pyramid cells n_s | 5 | 9 | 12 | 14 | 15 |
| newest acquisition needed | t | t+1 | t+2 | t+3 | t+4 |

At stage 1 the five cells are the pairs (t - k, t), k = 1 .. 5: all end on the acquisition t, so a missing acquisition t gives no stage 1 score at all, and the five cells share one acquisition (a noisier score than five independent cells, which is why each stage needs its own null).

## A finding that changes the premise: TiDE reads future covariate rows

The owner's premise is "the same forecast, scored as observations arrive". That holds for the rolling fits, whose forecast reads only the context. It does NOT hold for the three registered TiDE models (`tide_c30_gaza_f1p_mt0.2`, `tide_c30_pdcompact_mt0.4`, `tide_s1_mt04`): their `fcov_spec` has, per horizon row t .. t + 4, the |bperp| of the five pairs ending on that date, ERA5 soil moisture and snow and their pair differences, the `obs` flags and the month. TiDE's dense encoder sees all H future rows flattened, so the horizon 0 quantiles depend on the covariates of t + 4. At stage s the rows s .. H - 1 are not known: the bperp of a pair exists only once it is acquired, and the weather of a future date does not exist. Decision 42 already cuts anchors whose covariates over [t - C, t + H - 1] are incomplete, which is exactly the anchors a monitoring update wants.

So for TiDE a staged score needs a staged FORECAST: at stage s the forecaster is called with the covariate rows s .. H - 1 treated as unknown. Proposed fill of those rows (decision D1):

- `obs` flags 0 and bperp `fcov_fillna`: what a future pair that was not acquired looked like in training under `future_obs: observed` (all registered models), so not new to the models;
- `var` covariates (weather, pair differences): never missing in training. Either persistence (the last known row repeated) or `fcov_fillna`; both are out of the training distribution for the registered models;
- month: known, unchanged.

Consequences: the model is unchanged, but the forecast at stages 1 .. H - 1 differs from the final one, and a TiDE run makes up to H forward passes per anchor instead of one. The final stage is today's forecast, made by today's call. A model trained with random blanking of future rows (a ponzi-models fit spec, not part of this request) would make the staged inputs in distribution; the mechanism here is the same for it. Forecasters declare which case they are: `future_rows: "unused"` (rolling fits: one forecast serves every stage), `"blanked"` (TiDE: one forecast per stage with the declared fill), anything else refused for a staged run (the `stored` forecaster; an `external` callable that declares neither).

## What changes (proposed)

1. **The request.** `RunRequest.staged: bool` (`--staged`), default false, recorded in `run_meta.request`. Not part of `config_hash` or the stamp: like `summaries` it adds an output and changes no number of the others. With it the anchor range runs to the last acquisition, [C, T - 1]: an anchor t > T - H gets the stages it has reached and no final score (the context buffer reads NaN for slices beyond T - 1). The stamp's `t_hi` stays the last anchor with a final score; `staged_t_hi` is recorded beside it.
2. **The staged score.** For stage s < H: the channel scores of the stage's forecast on the cells `overlap & (h < s)`, aggregated by today's `aggregate` with that mask as `channels` (CR-010) and the same weights `w_bh`, with the stage minimum below. Stage H is not recomputed: it is score.zarr. The state machine (change.zarr) and the et summary keep reading the final stage only.
3. **min_channels per stage** (decision D2). Recommended: a fixed proportional rule, `m_s = ceil(min_channels * n_s / n_H)` in integers, so m_H = `min_channels` exactly and no new run config field is needed:

   | stage | 1 | 2 | 3 | 4 | 5 |
   | --- | --- | --- | --- | --- | --- |
   | `min_channels` 9 (`mon_tide_s1_mt04`) | 3 of 5 | 6 of 9 | 8 of 12 | 9 of 14 | 9 of 15 |
   | `min_channels` 5 (the mt0.2 and mt0.4 configs) | 2 of 5 | 3 of 9 | 4 of 12 | 5 of 14 | 5 of 15 |

   Which pixels get early scores: at stage 1 a pixel needs 3 of the 5 pairs ending on t, so a pixel missing t, or three of its five secondaries, or with three of its five baselines unsupported (`support: gated`, `min_support` 12 of 30), waits for stage 2 or later. The alternative, an explicit list `aggregate.min_channels_by_stage` in the run config, needs a hash change of its own: `config_hash` hashes the whole resolved dump, defaults included, so any new field changes every existing hash unless the hash leaves it out while it is unset (that exception would be part of this request and tested on the registered configs). Setting the list is then a new run config and a new model card.
4. **The staged store** `staged.zarr` (C26, `ponzi.contracts.staged`): `anomaly_score`, `ceiling_score` float32 and `n_channels` uint8, each `(stage, time, y, x)` for stages 1 .. H - 1, chunks `(1, 1, Y, X)`, coordinates, `process_pixels` and stamp as C7, plus attrs `stages`, `staged_t_hi`, `staged_rule` (the per-stage minima, `future_rows` and the fill of D1). score.zarr, change.zarr and every other store stay byte-identical. Separate variables in score.zarr were considered and rejected (they change C7 for every reader); a stage axis inside score.zarr likewise. Size: 9 bytes per processed pixel, anchor and stage, about 1.7 times score.zarr's 21 bytes for four stages. `difference`, `sensitivity` and `predicted_median` per stage are left out (decision D5).
5. **A monitoring update** is an ordinary staged run over a trailing window ending at the newest acquisition: it writes the newest anchor at stage 1, the one before at stage 2, and so on, and the anchor T - H at its final stage (score.zarr). The window must reach back as far as its consumers need: H anchors for the staged outputs, four more for Et (it reads anchors k - 4 .. k), and the state machine's own memory. Appending into one growing store is not part of this request.
6. **Calibration per stage** (decision D3). Recommended: ONE run config (the model's registered one, hash unchanged) and ONE calibration file per kind holding one mapping per stage. `Calibration` format 3: `null` (the final stage, as today) plus `null_s1 .. null_s{H-1}`, a ceiling lookup of shape `(stages, classes, 256)`, meta `stages`, `n_null_by_stage` and the `staged_rule` it was built under. Format 2 files still load and code the final stage only. Built from staged panel runs by the `run` setting of `null_rows.py`: the null of stage s is the stage s `anomaly_score` of the panel runs where finite.
7. **`ponzi pvalues`** on a staged run and a staged calibration writes, besides `anomaly` and `ceiling` (unchanged), `anomaly_staged` and `ceiling_staged` uint8 `(stage, time, y, x)`, each stage coded with its own mapping. It refuses a calibration whose `staged_rule` differs from the run's (the hash cannot see it, since `staged` is not hashed), and a non-staged calibration on a staged store codes the final stage only, with a warning. Nothing is overwritten as the pyramid fills: every stage keeps its code, so "what was known when" stays readable. The current view is derived: `PValueStore.latest(t)` returns the final code where it exists, else the highest stage present, and the stage it came from.
8. **The detection recipe** (decision D4). Proposed: `DetectionRecipe.provisional: bool`, default false (today's recipe, final codes only). With it an anchor whose latest code is at or above `code` is a provisional flag; at the final stage the final code confirms or withdraws it, and withdrawn flags are kept in the events store as their own state for evaluation. The same `code` holds at every stage, since each stage is calibrated to the same p. Dating stays final only: Et(k) needs the final stage of anchor k (its off-pyramid cells reach k + 4), and the dating window reaches first flag + 4, so an event's Et date is known at acquisition first flag + 8; until then a provisional event carries its first flag as date (the recipe's fallback, recorded as such). In a 12-day series: provisional flag at acquisition t, confirmed at t + 4, dated at t + 8, against flagged at t + 4 and dated at t + 8 today.

## Why one run config with staged calibrations, not one run config per stage

- **Registry.** A model card names one run config hash. One config per stage means H configs per model: H cards, or a card with a list, and every calibration filed under the right one.
- **Hashes and runs.** A stage is a view of the same run, not another computation of the config: one run produces all stages (one context read, one final forecast). Separate configs would need H runs per burst in production and on the panel, or one run stamped with H hashes, which breaks "one run, one hash".
- **CR-020.** Unchanged: one library check per calibration file and run. The staged rule is library code, so a later change of it changes staged scores without changing the hash; the `staged_rule` record and its check catch that, and the CHANGELOG rule (a change of an existing behaviour is MAJOR) applies as well.
- **Picking the stage.** Read from the store's stage axis; no caller chooses a calibration per stage.
- **Storage.** Per stage about 4.4 M null rows (the v04 null is 4,409,649), so a staged file is about five times today's 7 MB, roughly 35 MB per kind. The lookup adds `(5, 3, 256)` int16.
- **Panel runs.** For the rolling fits every stage is already in today's panel runs (stage s is a sub-pyramid of the stored channel z), though the `run` setting wants the run's own staged scores, so a staged rerun is cleaner. For TiDE the staged forecasts are new, so the panel is run once more with `--staged`: the same number of runs and pixels, each with up to five forward passes per anchor.

## Open question: does calibration also depend on the effective context?

Not decided here. The question is whether pixel-anchors with a short effective history (after gaps, sparse stretches, and for a model trained with random context blanking) have another null than the rest, so that one mapping over-flags or under-flags them.

**Test** (ponzi-models side analysis, no library change): on the panel test cells, the existing null runs of `tide_s1_mt04` and, when it exists, a context-blanking candidate (none is in `specs/candidates/` yet).

- Effective context of a pixel-anchor: the number of context slots in [t - C, t - 1] with a finite value in at least one baseline (computed offline from the coherence store), and as a second view the median support over the scored baselines.
- Bins: 12 to 17, 18 to 23, 24 to 29, 30 (only above the `min_support` gate; below it there is no score).
- Per bin, at the final stage and at stage 1, under the one calibration: the exceedance rate at codes 40, 50 and 60 (p 1e-2, 3.2e-3, 1e-3) against nominal, with binomial intervals, the row count per bin, and the same split by ceiling class. Calibrate on half the test bursts and check on the other half, so the check is not in sample.
- Decision rule (proposal): act if any bin with at least 10,000 rows is outside a factor 1.5 of nominal at code 50.

**Bounded remedy, if needed:** a coarse context class (2 or 3 classes above the gate) as one more conditioning dimension inside the same calibration file, like the ceiling classes: the lookup becomes `(stages, context classes, ceiling classes, 256)`, built from the same panel runs, so the number of panel runs does not grow. The run must then write the class or its input (a `(time, y, x)` uint8 effective context in score.zarr and staged.zarr, an opt-in output). Cost in null rows: each lookup cell holds only its own rows; today's smallest ceiling class has 554,866 rows (12.6 %). A conformal code at p needs at least about 10 / p rows to be stable (ten null exceedances): 3,200 for code 50, 10,000 for code 60, 100,000 for code 80. Proposed minimum 10,000 rows per cell; a cell below it falls back to its ceiling class's mapping without the context condition, and the file records which cells did. With three context classes and three ceiling classes a cell holding 2 % of the 4.4 M rows (88,000) is fine to code 70; a context class of 1 % inside the smallest ceiling class (about 5,500 rows) would fall back.

## Do results change?

No, for every existing run config and store: `staged` is off by default, the anchor range, every store and `run_meta.json` (apart from the new null request field) are as before, the results lock `runner_golden.npz` passes, and format 2 calibrations load and code as before. Staged outputs are new.

## Tests

- Final stage against today, bit for bit: a staged run's score, change, summary, channel and prediction stores equal the unstaged run's (rolling fit, pooled rolling fit, an external callable declaring `future_rows`, TiDE on the tiny TorchScript model), compact loop and whole grid, with a mask (CR-014).
- Rolling fits: stage s equals `aggregate` of the unstaged run's channel z restricted to `h < s` with `m_s`, on the bytes.
- TiDE: the inputs of the stage s forward pass equal `SingleAnchorTemplate` windows with the rows s .. H - 1 filled by the declared rule; the final pass is today's pass (same batches, same bytes).
- The proportional minimum (table above, and m_H = `min_channels` for every value 0 .. n_H); a pixel missing acquisition t has no stage 1 score.
- Anchors beyond T - H: stages written up to the time axis, no final score, the stamp unchanged; a run whose window ends at T - 1 gives the newest anchor at stage 1.
- Calibration: format 3 round trip; format 2 loads; the final-stage mapping of a staged calibration equals a plain calibration built from the same final scores; `pvalues` codes each stage with its own mapping, refuses another `staged_rule`, `latest` returns the right stage.
- Recipe: provisional, confirmed and withdrawn states on synthetic codes; `provisional: false` gives today's events store bytes.

**HPC checks** (each submission asked for separately):

1. One burst, registered model `tide_s1_mt04` and its config: staged against unstaged run, score.zarr, change.zarr and summary.zarr identical; run time and peak memory of the staged run (expected up to five forward passes per anchor).
2. Staged panel runs (masked `sample` route) and the staged calibration: rows per stage; exceedance per stage at codes 40, 50 and 60 on the held-out half of the test bursts.
3. Latency and cost on a labelled case (Gaza UNOSAT or BRIGHT): for final detections, the share already flagged at stages 1 to 4; the share of provisional flags withdrawn at the final stage; precision next to the false alarm rate at each stage; the per-anchor gain is H - 1 revisits (48 days at 12 days); the weather latency (about five days for ERA5T) delays every stage alike, so it does not reduce the gain.
4. The effective context test above.

## Version

Library: minor (an opt-in request option, a new store, calibration format 3 read beside format 2, an opt-in recipe option; nothing existing changes). Under CR-020 existing calibrations keep coding existing runs. The staged rule (proportional minima, the fill of D1) becomes library behaviour: changing it later is MAJOR, and the `staged_rule` check refuses a mismatch in any case. Standard: no new major; a product that uses provisional codes names the staged calibration and the recipe option. The explicit per-stage list of D2 would be a new run config, hence a new model card and calibration, but still no new forecast run.

## Decisions for the owner

- **D1.** TiDE staged forecasts: accept one forecast per stage with the future rows not yet known filled (`obs` 0 and bperp `fcov_fillna`; weather by persistence or by `fcov_fillna`), or restrict progressive scoring to forecasters without future covariates until a model trained with future-row blanking exists, or both (mechanism now, the blanking model as a ponzi-models candidate).
- **D2.** Minimum per stage: the proportional rule from `min_channels` (recommended, no config change), or an explicit list in the run config (new hash, new card).
- **D3.** Calibration: one run config with per-stage mappings in one file (recommended), or one run config per stage.
- **D4.** Recipe: provisional flags confirmed or withdrawn at the final stage, the same `code` at every stage, dating final only; or provisional flags only at stages 3 and 4, or a stricter code at early stages.
- **D5.** Staged store content: anomaly, ceiling and `n_channels` only (proposed), or also difference, sensitivity and median per stage.
- **D6.** Monitoring updates as trailing-window runs into new folders (proposed), or an append mode into one growing store (a separate CR).
- **D7.** The effective context test: its bins, the decision rule, and whether to run it before or after the staged calibration.

## Implementation notes (2026-10-21)

Where the code follows the decisions D1 to D7 rather than the proposal text above, or had to settle what the text left open:

1. **D5, the full set.** `staged.zarr` holds all six C7 arrays per stage (`anomaly_score`, `difference`, `sensitivity`, `predicted_median`, `ceiling_score`, `n_channels`), not the three of item 4: 21 bytes per processed pixel, anchor and stage, about H - 1 times score.zarr.
2. **D1, the fill of the unknown rows** is the `unknown_future` training augmentation of ponzi-models (`training/augment.py`), on the bytes (`ponzi.core.forecast.model_inputs.unknown_future`, `SingleAnchorTemplate(known=)`, tested against a transcription of it): every physical channel (`bperp_abs` and every `var`, weather and pair differences alike) `fcov_fillna`, the `obs` channels 0 under `future_obs: observed` and as the treatment gives a future row otherwise (1 under `one`), the month kept. There is no persistence option; for a model trained without the augmentation the same fill is the stopgap. A strict model does not refuse a missing value in the unknown rows (the weather of a date not yet reached), and still refuses one in a known row.
3. **Where `staged_t_hi` is recorded.** In the attrs of `staged.zarr` (and of the p-value and events stores made from it), not in `run_meta.json`, which differs from an unstaged run's only in `request.staged` (false by default, not null) and in `written`.
4. **The tail anchors' stages.** An anchor after the final range gets the stages whose acquisitions exist (`T - t`) AND, for a forecaster with required covariates, whose covariates over `[t - C, t + s - 1]` are complete: decision 42 applied per stage, so an anchor cut from the final range because the newest weather is not out yet is scored at the stages that have it. The horizon rows beyond the time axis carry missing coherence and covariates on the nominal next dates (`revisit_days` apart), which only the month and a rolling fit's harmonics read.
5. **The end of a staged run** is the request's own end: the last acquisition on or before `end_date` in monitoring, the end of the event window in detection mode, the last acquisition without either. `resolve_run_window` is unchanged, so a staged run still needs at least one anchor with a final score (a monitoring window that starts after T - H is refused as before).
6. **Provisional states (D4).** The anchors after the last final score flag by their latest stage code (the highest stage present). The bit `provisional` marks an anchor flagged at ANY stage before the final one, `withdrawn` one whose final code is then below `code`; withdrawal happens at the final stage only, so an anchor flagged at stage 1 and not at stage 2 is provisional, not flagged by its latest code, and not withdrawn. `detect-path` combines the latest codes and the provisional marks of its bursts by the same rule as the codes. Off, the recipe is left out of the dump, so every recipe digest and every events store of before is unchanged (tested against the digest on main).
7. **Calibration from staged panel runs (D3).** The library builds format 3 from staged runs with `ponzi.calibration.staged_inputs` (the `run` setting of `null_rows.py`: the null of stage s is the stage s `anomaly_score` where finite, tail anchors included; each stage's ceiling lookup from the stage's own anomaly and ceiling scores at the same pixel-anchors) and `Calibration.estimate(..., stages=, staged_rule=)`. `null_rows.py` and `build.py` in ponzi-models are not changed by this request; they need a staged mode that calls these (or pass the pooled arrays themselves).
8. **Additions not named above:** the attr `stages_written` of staged.zarr (the highest stage written per anchor), `Calibration.codes_stage`, `PValueStore.staged` and `staged_t_hi`, the `staged_t_hi` attr of a provisional events store (its `period` ends there), and `estimate_run_memory(..., staged=True)` (key `staged`).
9. **Tests.** As listed, with the TiDE final pass checked through the stores (score, change, summary, prediction and channel stores the same bytes) and the stage windows recorded at the module; one more invariant: a staged run on the store cut after an acquisition holds, at its tail anchors, the whole store's stage scores (rolling fit, a blanked external callable, TiDE).
