# CR-016: the treatment of missing values is declared by the model

- **Requested by / date:** owner, 2026-10-13
- **Status:** signed off 2026-10-13; implemented on branch `missing-treatment` (not merged)

## Why

A learned forecaster is given a number where a coherence value is missing. Until now that number was fixed in the builder: 0.5 (`target_fillna`), with an `obs` channel per baseline saying 0 for "not observed". Three things follow from that, and each is to be tested on new fits (ponzi-models, the candidates of `specs/candidates/`):

- 0.5 is a plausible coherence. A model can only tell it from a real 0.5 through the flag, and the lookback skip of TiDE reads the filled value directly. The Gaza 2026 gap period and the null just after a gap are where this is suspected to cost.
- The `obs` channels of the future rows held the real indicator in training (is the pair of the horizon step acquired) and are constant 1 in a run, where nothing is known about them. Training and inference differ there by construction.
- A missing covariate was filled with a constant (`fcov_fillna`) by the builder. A run does not score such an anchor (decision 42), but the builder itself never refused, and a trainer could build windows on filled weather.

What the model is given has to be the same in training and in a run, so it cannot be decided in two places. It is declared in the model's `meta.json` and applied by the one builder both sides use (`ponzi.core.forecast.model_inputs`).

## What changes

### 1. Meta keys, read by `model_inputs.treatment_of`

```
"missing":    {"fill": "constant" | "median" | "previous" | "sentinel", "value": number, "flag": true | false}
"future_obs": "observed" | "one" | "none"
"covariates": "filled" | "strict"
"support":    "ignored" | "gated"
```

A meta without a key has its old meaning: `constant` at `target_fillna` (0.5), the flags present, `observed`, `filled`, `ignored`. Every existing artifact is read as before.

`missing.fill`, for a missing coherence (not finite, or 0.0, as before) of the PAST window of an anchor:

- `constant`: `value`, default `target_fillna`.
- `sentinel`: `value`, required. A number outside the range of the data (the candidates use -1).
- `median`: the median of the pixel's observed values of that baseline in the window (the mean of the two middle values for an even number).
- `previous`: the last observed value of that baseline before the gap, in the window. A gap at the start of the window takes the first observed value after it.
- `median` and `previous` fall back, for a baseline with nothing observed in the window, on the median of the pixel's observed values of all baselines in the window, and for a pixel with nothing observed at all on `target_fillna`. They take no `value`.

All of them read the context rows of the anchor only. The horizon targets are not inputs; a missing one stays out of the loss and out of the scores as before (in the per-date arrays of `build_features` it holds a placeholder that nothing reads).

`missing.flag` says whether the `obs` channels exist. It must agree with the model's `fcov_spec` (`build_fcov_spec(..., flag=False)` builds a spec without them); a meta that says one thing and lists the other is refused.

`future_obs` is about training, since a run always gives 1: `observed` is the real indicator (the registered models), `one` is constant 1, as in a run. `none` means there are no such channels, and it goes with `flag: false` and only with it. Removing the `obs` channels from the future rows alone was asked for as an option and is NOT offered: TiDE projects the covariate rows of the past and of the future with one block (`fcov_proj` on their concatenation), so the two have the same channels; a future input of another width needs a second projection, which is another architecture and another state dict. Without the flag the channels are gone on both sides, and that case needs nothing: the builder walks the spec.

`covariates: strict`: `burst_shared_fcov` leaves a missing value NaN instead of filling it, and the window builders raise for a missing value of any `var` channel in a window, naming the channel and the dates. The perpendicular baseline is the one exception, and it is forced: where a pair does not exist (a dropped acquisition, the first acquisitions of the long baselines) the store has no `bperp` for it, and a model that refused those windows could not be run or trained on a single gap. So a missing `bperp` is still `fcov_fillna`, but under `strict` only where the coherence of that pair is missing too: a pixel whose pair is observed while its `bperp` is missing raises. This is checked for the context rows, by the template for every batch of a run; for the horizon rows the builder does not see the targets, and a missing `bperp` there is filled without the check. Accepted by the owner (2026-10-13) as it stands: a horizon step without its pair has no target, so it is not scored and not in the loss, and the filled `bperp` of that step informs nothing that is judged; a horizon step WITH its pair and without a `bperp` would be a defect of the store, which the context check finds as soon as that date is in a context.

`support: gated`: the model honours the run config's `context.min_support`, as the rolling fits do. The threshold is a scoring decision and stays where it is, in the run config and its hash; the model only declares that it honours it, and neither the meta nor a fit spec carries a number. For a gated model a channel (a pixel and a baseline) with fewer than `context.min_support` finite values of that baseline in the context gets no forecast: NaN quantiles for every horizon, so no z, and the channel is not counted in `n_channels`, exactly as an unsupported channel of a rolling fit. Without the key (`ignored`) the number is not read by TiDE, as before, so the registered models stay bit-identical although their configs say 6. Training does not filter on the number of observations: sparse windows stay in the loss (only missing targets are masked), and the trainer reports the validation loss by the number of observed values so that the threshold can be chosen from evidence (ponzi-models, `val_by_support`).

What counts: FINITE context values, the count the rolling fits use (`np.isfinite`), the context buffer's `support()` and the `support` array every predictive carries (unchanged). This differs from the fill's "observed" in one case: a coherence of exactly 0.0 is finite, so it counts as support, while the fill treats it as missing. The rolling fits fit on such zeros as values; one definition for both forecasters was preferred over the fill's, and `supported_channels` is that rule.

### 2. The builder

- `fill_gaps(tgt, bad, treatment)`: the fill of the past targets of a set of windows, in place. `median` and `previous` are computed for the windows that have a gap only, each from its own rows, so the result does not depend on the batch.
- `finish_windows(x_past, x_future, bad, meta, times=None)`: the per-window part of a treatment for windows cut from the per-date arrays of `build_features` (the fill, `future_obs: one`, the strict covariates). `assemble_windows` calls it; a trainer with its own window index calls it per batch. For a meta without the keys it does nothing.
- `SingleAnchorTemplate` and `assemble_single_anchor` apply the same treatment (`fill_gaps`; the strict check when the template is built and, for `bperp`, in `fill`). The per-batch buffers of CR-010 are unchanged.
- `build_fcov_spec(..., flag=True)`, `load_artifact` refuses a meta with an unknown treatment.
- `support_gated(meta)` and `supported_channels(ctx_px, min_support)`; `TideForecaster.predict` blanks the unsupported channels of each batch after the forward pass (the inputs of the pass are unchanged by the gate).

### 3. The run

- `covariate_complete_window` (decision 42) checks the `var` covariates over the context AND the horizon rows of every anchor; that was so before and is now stated. Its record in `run_meta.window.covariate_cut` gains `cut_anchor_dates` and `missing` (per incomplete variable, the acquisition dates the cut anchors read at which it is missing).
- `RunRequest.strict_covariates` (`--strict-covariates`, default false): the cut at the series end becomes an error. For reanalysis runs. A gap inside the range was an error before and still is.

### What was found for the existing models

- A `var` covariate (weather, pair differences) that is missing never reaches a scored window of a run: the check covers the context and the horizon rows, and the run cuts or refuses.
- A missing `bperp` does: every anchor whose 35 rows hold a missing pair is scored with `fcov_fillna` (0.0 after scaling, the smallest |bperp| of the training split) in that pair's baseline channel. That is documented in `fcov_required_vars` and is what the registered models were trained with. It is not changed.
- A pixel with nothing observed in its context IS forecast and scored by a TiDE run when its targets are observed: `context.min_support` is applied by the rolling fits only (`rolling.py`), the TiDE predictive carries the support counts and the scoring does not read them. The last fallback of `median` and `previous` (0.5) is therefore a value a run can use, not dead code. `support: gated` is the answer for new models.

### Can a fallback still reach a scored channel of a gated model?

With `support: gated` and `context.min_support >= 1`, for a channel that is scored:

- Its own baseline has at least one finite context value. If one of them is observed in the fill's sense (not 0.0), the same-baseline `median` or `previous` is defined and the channel's own column uses no fallback.
- The fallback on the pixel's median over all baselines is still reachable as an INPUT of a scored channel: the model is multivariate, so a scored 12-day channel of a pixel whose 60-day baseline has nothing observed in the window is forecast with that 60-day column filled by the pixel's median. The 60-day channel itself is not scored.
- The last fallback (0.5) fills a column only when the pixel has no observed value in ANY baseline of the window. Then every baseline has zero non-zero finite values, and the pixel can only be supported through values of exactly 0.0: a scored channel sees 0.5 only if its baseline holds at least `min_support` zeros and the whole context of the pixel is zeros and NaN. If the stores hold no exact 0.0 (the producer writes NaN for no data; not verified here), the 0.5 fallback cannot reach a scored channel.

## Do results change?

No, for every existing model and run config: a meta without the keys goes through the code of before (the constant fill, the same casts), and the results lock (`runner_golden.npz`) and every TiDE test pass unchanged. `run_meta.json` gains the request field `strict_covariates` and, where a run was cut, two keys in the cut's record.

Models that declare a treatment are new models; nothing is compared with them here.

## Tests

- `test_model_inputs_missing.py`: for constant, median, previous and sentinel, with and without the flag, each `future_obs` value, with and without strict covariates: the windows of `assemble_windows` against those of `SingleAnchorTemplate` (batches through one reused buffer) and `assemble_single_anchor`, on the bytes, for every pixel and anchor of a series with gaps at the start, in the middle and at the end of a window, a whole baseline missing, a pixel with nothing observed and a pair missing for every pixel. Under `observed` the future `obs` channels differ where a horizon pair is missing, as they always did; the test states that and compares the rest. Each fill against values worked out by hand; a window's fill does not depend on its batch; a meta without the keys gives the bytes of the code of before, written out in the test; strict covariates raise with the channel and the date; the declarations are checked.
- `test_tide_missing.py` (`ml`): gated against ignored on the same tiny model and store (a pixel without history is scored without the key and not with it; a channel of zeros is supported; the channels with a z are exactly those of a rolling fit on the same store and config, and `n_channels` is equal; where the gate does not act the two TiDE runs are the same bytes). A run on a synthetic store with a tiny TorchScript artifact for the default and each treatment; the inputs of the forward pass against `assemble_windows`; a strict model refuses a `bperp` missing for an observed pair; the cut at the series end is recorded and `strict_covariates` refuses it.
- `test_windows.py`: the new keys of the cut's record.

Cost of building the windows of one anchor, C 30, five baselines, 23 covariate channels, 204,800 pixels, one thread, laptop (the forward pass not included): 0.55 to 0.75 s for the default, on `main` and on this branch alike. With a gap in every pixel (10 % of the values missing, at random or as three missing acquisitions) `median` takes about 1.2 to 1.4 s and `previous` about 1.5 s, that is 3 to 4 microseconds more per window; with gaps in 10 % of the pixels both are within 10 % of the default; without gaps there is no difference. `sentinel` costs what the default costs, and without the flag about half (five channels fewer to write).

## Version

Library: minor (new opt-in meta keys, a new request option; every existing run config stays bit-identical). Standard: a model that declares a treatment is a new model, so adopting one is a new forecast run and a new major of the standard; nothing here forces one.
