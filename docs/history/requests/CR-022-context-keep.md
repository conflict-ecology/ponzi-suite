# CR-022: a run whose forecaster sees only the last L acquisitions of its context

- **Requested by / date:** owner, 2026-10-15
- **Status:** merged into main 2026-10-16 (owner), released in v0.2.2. A test option: no production path uses it.

## Why

1. **A controlled test of one calibration across effective context lengths** (CR-021, decision D7). A pixel-anchor with a short effective history (after gaps, in sparse stretches) may have another null than one with a full context, so that one mapping over-flags or under-flags it. Binning the existing null runs by their observed effective context mixes the context length with everything that makes data sparse (season, snow, the satellite switch, the burst). This option removes that confounding: the same panel test bursts, the same anchors and pixels, the same registered model and config, run at L = 12, 16, 20, 25 and 30 kept acquisitions. Only the context length differs, so a difference between the nulls of those runs is the effect of the context length alone. The rule (owner): a 1 in 1,000 rate outside 0.67 to 1.5 times nominal, with its interval excluding nominal, means context classes are needed.
2. **The series start in operations is related, but NOT this option.** A new burst, or a burst after a long outage, has anchors with fewer than C acquisitions behind them. The option emulates the input such an anchor would have (its last L acquisitions, the older slots missing), so its nulls say how well one calibration would serve those anchors; it does not score them. What scoring anchors before C would additionally need is listed under "Follow-up".

## What changes

`RunRequest.context_keep: int | None` (`--context-keep L`), default None. With L set (1 <= L <= C), at every anchor t the forecaster is given its context `[t - C, t - 1]` with the older C - L acquisitions `t - C .. t - L - 1` presented exactly as acquisitions missing from the store are (`ponzi.core.context.ContextKeep`):

- the coherence of every pair ENDING on one of them is NaN (every baseline of those context rows);
- the coherence of every context pair whose EARLIER date is one of them is NaN (a pair of the kept rows reaching back past the first kept acquisition, as far as its partner lies inside the context);
- the `bperp` of all those pairs is NaN (a missing acquisition has no pair, so no baseline), in a copy of the anchor's covariates;
- the obs flags are 0 there, because the model inputs derive them from the coherence (finite and non-zero), with nothing more to do;
- every `(time,)` covariate is left as it is: weather, the month and the pair differences exist whatever the coherence does.

Not changed: a pair whose partner lies BEFORE the context (that acquisition is outside the context, not missing), the horizon rows (the targets and their covariates are the store's), the context buffer of the loop (the forecaster gets a reusable copy; the buffer rolls on unchanged), the other `(time, baseline)` tables (`n_finite`, `platform`, `secondary_date`: no forecaster reads them).

The partner of a pair is its store's `secondary_date` where the input has that table (the actual partner, also across a satellite switch), otherwise the acquisition `baseline_days` earlier by date (`model_inputs.pair_partner_secondary`, `pair_partner_index`).

A consequence worth stating, since it is what real gaps do too: keeping L acquisitions leaves a baseline of k revisits at most L - k pairs, not L (the pair ending on the oldest kept acquisition reaches back to a dropped one). At L = 12 with the b5h5 baselines (12 to 60 days) that is 11, 10, 9, 8 and 7 pairs. The `min_support` gate counts those. For `tide_s1_mt04` (`support: gated`, `min_support` 12, `min_channels` 9 of the 15 pyramid channels, of which a baseline of k revisits holds k) a baseline is supported only for L - k >= 12, so L = 12 to 15 score nothing at all (at L = 15 the 12- to 36-day baselines give at most 6 channels), L = 16 scores only the pixel-anchors whose 48-day baseline has all 12 of its pairs in the kept window (and the 36- and 24-day ones at most one and two missing), and the 60-day channels count from L = 17 on. That is what the same number of real acquisitions would give; the test of purpose 1 should read its short L with this in mind (the analysis script also compares the L on the pixel-anchors scored at every L).

Everything after the forecaster's input is the code of a run on real missing data, with no path of its own: the forecaster (TiDE builds its windows from that context and those covariates through `SingleAnchorTemplate`, the rolling fits fit on the finite values), the support counts the predictive carries, the `min_support` gate (rolling fits, and TiDE models with `support: gated`), the scoring, the aggregation, the state machine, the summaries and every store.

**Record.** `run_meta.request.context_keep`, and an attr `context_keep` (the integer) in every output store, beside the input's attrs (as the mask's `mask_layer`, CR-014), not in the run stamp. Without the option the attr is absent.

**Not part of `config_hash`.** Like the mask it is an input condition: the run config (the model, its context length C, its gate) is unchanged, and a run with the option is stamped with the hash of the run without it. A calibration made from such runs carries that hash too; telling the runs apart is the caller's business, through `run_meta.request` or the store attr (the lab's output folders are named `v0.4_keep<L>`).

**Refused:** L < 1 (by the request), L > C (by the run, naming C), and the `stored` forecaster (its predictions were made elsewhere, from the full context).

**Memory.** The forecaster's copy of the context is C slices on the loop's pixels: `estimate_run_memory(..., context_keep=True)` adds the key `context_keep`, `C * loop_pixels * B * 4` bytes (0 without the option, the key is always present). For a panel run through the masked route that is a few MB.

**What a real missing acquisition does that the option does not.** Where a model reads covariates derived from the acquisition itself (the Sentinel-1 pair differences `s1_pd_*` of the extra sidecar, decision 49, read by `tide_s1_mt04`), a really missing acquisition would have no such value, and decision 42 would cut the anchor. The option leaves those series as they are, so the anchor is scored with real pair differences next to blanked coherence. This is the useful case for the test (a cut anchor has no null) and is stated, not hidden.

## Do results change?

No. Without the option every array is what it was (the results lock `tests/data/runner_golden.npz` passes unchanged), and no store gains an attr. `run_meta.json` gains the request field `context_keep: null`. With L = C nothing is dropped (no pair of the context reaches back past its own first acquisition) and the arrays are those of the run without the option, bit for bit (tested).

## Tests

`tests/test_context_keep.py`:

- the rule written out by hand for one anchor; the context buffer is never written, `bperp` is blanked in a copy and its horizon rows are untouched, the weather is the same object;
- L = C against the run without the option, every array of the score, change, prediction and channel stores on the bytes (rolling and pooled fits); the attr, the request field, the unchanged hash;
- **the invariant**: at every anchor t of the run, a store with the acquisitions `t - C .. t - L - 1` blanked (every pair ending on them and every pair of the series reaching back to them NaN, their `bperp` NaN) and a single-anchor run of it, against the anchor t of one run with `context_keep L`. Rolling and pooled fits, L = 1, 3, 4 and 6 (C 8, the longest baseline 4 revisits): the predictive (mean, std, support) on the bytes at every L; the channel scores and the pixel scores (`anomaly_score`, `ceiling_score`, `n_channels`) on the bytes for L >= 4, also from the compact loop. For L below the longest baseline in revisits, horizon pairs reaching back to a dropped acquisition exist: the blanked store has no target there and the run with the option keeps the store's, so the scores are compared from L = 4 on (the panel test, L >= 12, is far from that case);
- TiDE (`ml`, the tiny TorchScript model of `test_tide_missing.py`): the same invariant at every anchor for L = 3 and 5 (C 7, longest baseline 3 revisits), the predictive quantiles, the channel and the pixel scores on the bytes; L = C is the run of before; a gated model (min_support 4) forecasts nothing from 4 kept acquisitions (at most 3 pairs per baseline) while the ungated one does, and forecasts from 5;
- `min_support` (rolling mean, min_support 3): nothing is scored with L = 3 (at most 2 pairs), channels are scored with L = 4, and the support of the prediction store is L - k per baseline;
- a masked window (CR-014): at the masked pixels the masked run with the option holds the bytes of the unmasked run with the option; the store attr beside `mask_layer`;
- the refusals (L = 0, L = C + 1), the memory term and the command line flag.

## Version

Library: minor (a new opt-in request option; every existing run config and request stays bit-identical). Standard: no new major; a calibration built from runs with the option is a side analysis, not a registered calibration, unless the owner decides context classes are needed (then that is its own request).

## Follow-up: scoring anchors before C (the series start), not in this request

The option emulates the input; scoring an anchor t < C would additionally need:

- **the window**: `windows.full_anchor_range` and `resolve_run_window` clip every monitoring and detection window to anchors `>= C` (the scorable range `[C, T - H]`), with a warning; a new minimum (for example `min_context` in the request, with anchors `[max(min_context, ...), T - H]`);
- **the context buffer**: `ContextBuffer._check_range` refuses anchors below C, and `prime` reads `t - C .. t + H - 1`, which would start before index 0; rows before the series would be NaN slices, not reads;
- **the anchor slices**: `ContextBuffer.aux` slices `times[t - C : t + H]` and `_anchor_covariates` slices every covariate the same way, which with `t < C` silently wraps around (a negative start); the dates of the rows before the series (for the month and the harmonic design of the rolling fits) and their weather would have to be made up or declared missing;
- **decision 42**: `covariate_complete_window` checks the `var` covariates over `[t - C, t + H - 1]`, which before the series do not exist, so every such anchor would be cut: the check would have to cover the existing rows only, or a model would have to declare that it accepts missing past covariates (a CR-016 style key);
- **the partner table and this option**: the pairs of the first acquisitions reach back before the series and are NaN already (the store's own early pairs), so with those three points an anchor `t < C` would get exactly the input of `context_keep = t` minus the weather of the missing rows;
- **calibration**: the anchors before C have their own effective context lengths; whether one mapping serves them is what this request's test answers first.
