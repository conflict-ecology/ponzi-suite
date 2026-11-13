# CR-103: per-pixel covariates for the learned forecasters, and the grid every input agrees on

- **Requested by / date:** owner, 2026-11-13 ("yes draft piece 3 and fold in the following: And then to be usable in the same model any input data feature just needs to agree on temporal cadence and pixel size which we enforce via the zarr format and specs I guess")
- **Status:** signed off (2026-11-13, "execute"), not started: it follows CR-102 (a) and (b) (D6). Parts 1 to 4 wait on part 0, whose result decides whether they are made (D5).
- **Owner decisions 2026-11-13:** D1 approved (a model on another grid is refused); D2 approved (SAR-derived variables never known-future); D3 approved (static variables as repeated channels); D4 approved (ESA WorldCover, `fraction` per class, `static`); D5 approved (part 0 gates parts 1 to 4; part 1 may be made alone), its margins left open for the owner to set before the run; D6 approved (the order).
- **Builds on:** CR-102 (input layers, variable kinds, `scoring.target`, amplitude, the sample carrying per-pixel variables), CR-016 (the treatment of missing values), CR-021 (unknown future rows), CR-010 (the single-anchor template).
- **Leaves for a later request:** forecasting a variable other than coherence.

## Why
CR-102 lets an input hold per-pixel variables that change over time, such as amplitude or a land-cover fraction, but no forecaster reads them. Today the learned forecasters (`ponzi.core.forecast.tide`, built by `model_inputs`) see three things:

- the targets: `coh` of the model's baselines;
- per-pixel `obs` indicators;
- burst-wide covariates: `bperp_abs` per baseline, `(time,)` variables such as `era5_*` and `era5_pd_*`, and the cyclic month.

Each burst-wide value is one number per date, broadcast to every pixel (`burst_shared_fcov`, `SingleAnchorTemplate`). Every covariate is known-future: it fills the past rows (`x_past = targets | fcov`) and the forecast rows (`x_future = fcov`).

Two things are missing:

1. **Per-pixel covariates.** Amplitude, a second coherence estimate and land cover differ from pixel to pixel. Nothing carries a per-pixel value into a window except `obs`.
2. **Covariates of the past only.** A SAR-derived variable at a forecast date responds to the same change on the ground as the coherence being forecast. Give amplitude at `t .. t + H - 1` to the model and it can forecast the drop, so the drop is no longer an anomaly. The run then detects less, for a reason invisible in its scores. Such a variable may enter the context rows only. Today every covariate is known-future, so a past-only covariate cannot be expressed at all.

The owner's point, folded in here: every input must share the grid before a model can use it. Saying only "the same cadence and pixel size" is not enough, and today only half of it is enforced (section 1).

## What changes

### Part 0. The experiment (ponzi-models only; decides parts 1 to 4)
Before any change to the library, ponzi-models trains two fits of one candidate on one panel: the current inputs, and the current inputs plus `amp_db` as a past-only channel. The channel is added in `prepare` and `gather_batch` behind a candidate-only switch, not in `ponzi.core`.

The two fits are compared on the panel's held-out bursts:
- the validation CRPS on unchanged pixels;
- the z-scores of the labelled change pixels, which must not shrink.

Part 0 needs CR-102 parts (a) and (b), and the panel's bursts made again with the `amp_db` feature. Both the reprocessing and the fits are cluster compute and the owner's to run. The switch and its tests are the implementation's part. The result is written up in `docs/discoveries/` and decides D5.

### Part 1. The grid every input agrees on
**1.1 What "agree" means.** Two variables can go into one model only when they are on the same grid:
- **Space:** the same CRS, lattice origin and posting, so identical `y` and `x`. The same posting is not enough: two 40 m grids whose origins differ by 20 m do not agree.
- **Time:** the identical `time` axis, the SAR series' acquisition dates. The same cadence is not enough: two 12-day series offset by 6 days do not agree.
- **Pairs:** the same `baseline_days` for every `pair` variable.

**1.2 Who enforces it.** Three places, each catching what the one before cannot:
1. **The producer's spec** brings its source onto the grid and says how, in a block that is part of its hash. Every variable not made from the SAR series records that block in an `alignment` attr:
   - spatial: `area_mean` or `fraction` (the source is finer than the grid; `fraction` for one class of a categorical source), `bilinear` or `nearest` (the source is coarser);
   - temporal: `at` (the value at the acquisition instant: ERA5's hour), `asof` (the last value at or before the acquisition: an annual land-cover map, a composite), `accum` (summed over the interval since the previous acquisition: precipitation).

   The onboarding does these already without naming them: GHSL is area-averaged, ERA5 is put on the time axis, and the pair differences use the partner date. This request names them in the onboarding spec (C17) and records them on each variable.
2. **The zarr layers.** `open_input` refuses layers whose `time`, `y`, `x`, `baseline_days`, `epsg` or `burst_id` differ (CR-102 1.4). This checks one input against itself.
3. **The model** (new). A model is trained on one grid and must not be run on another, but today its meta records `baseline_days` only. Training's pyramid takes `revisit_days` as 12 by default (`train.pyramid_cells`), and nothing records the posting. The meta gets:
   - `input_grid`: `posting_m`, `revisit_days`, `baseline_days`, `sensor`, `polarisation`;
   - per channel read from the input: the variable's name, `units`, kind, and the spec hash of its `source`.

   `load_artifact`, given the input, refuses a different posting, revisit, polarisation or units, or a channel whose source hash differs (D1). An artifact without `input_grid` (every artifact today) is not checked and warns once, so the existing standards keep running. Registering it again with its panel's grid adds the key.

### Part 2. Roles and the new channel kinds (`ponzi.core.forecast.model_inputs`)
**2.1 Roles.** A training spec names each variable it reads under one role (`inputs:` in the training spec; `era5_vars` remains the shorthand for known-future series):

| Role | Rows | Allowed kinds (CR-102) | Examples |
|---|---|---|---|
| `target` | past (and loss in future) | `pair` | `coh`; must equal the scoring spec's `scoring.target` |
| `known_future` | past and future | `series`, `pair_table`; `acquisition` and `static` not made from the SAR series | `era5_*`, `bperp`, a land-cover fraction |
| `past_only` | past | `acquisition`, `pair`, `series` | `amp_db`, a second coherence estimate |
| `static` | past and future, constant | `static` | `built`, `land` |

A variable whose `source` is a SAR spec cannot be `known_future`. That is refused when the training spec is loaded and again when an artifact is loaded (D2). This is the guard against the leak described in Why.

**2.2 Channel kinds.** New `fcov_spec` kinds:
- `pixel_var` (`known_future`, `acquisition`): one per-pixel value per date, in the past and future rows;
- `past_var` (`past_only`, `acquisition` or `series`) and `past_pair` (`past_only`, `pair`, one channel per baseline): in the past rows only;
- `static_var` (`static`): one per-pixel value, repeated on every row (D3).

**2.3 Layout.** `x_past` becomes `targets(B) | fcov(F) | past(P)`, and `x_future` stays `fcov(F)`. A meta without `past_*` channels has `P = 0`, so every existing artifact gets the same arrays, bit for bit. Scaling is the MinMax of today, fitted per channel at training (`fit_scalers`).

**2.4 Missing values** follow the model's treatment (CR-016): a missing per-pixel covariate is `fcov_fillna`, or an error under `covariates: strict`. A `past_*` channel may have its own `obs` flag (`flag: true` in its entry). An acquisition the augmentations drop (`drop_acquisitions`, `outage`, `context_dropout`) drops its per-pixel covariates with it, so training sees what a run sees when the acquisition is missing.

**2.5 Functions.**
- `build_features` takes the per-pixel covariates `(n_px, T, K)` beside the targets.
- `SingleAnchorTemplate.fill` writes the per-pixel columns of each batch. The template already keeps pixel-invariant and per-pixel columns apart for `obs`, so this extends it.
- `unknown_future` blanks the `pixel_var` channels of unknown rows like any physical channel. `PER_PIXEL_KINDS` and `PHYSICAL_KINDS` grow accordingly.

### Part 3. The runner
- `ContextBuffer` reads the target's `(C + H, Y, X, B)` slices. A second buffer reads the per-pixel channels a model names, `(C + H, Y, X, K)`, in the same time chunks. Only those channels are read: the forecaster's `required_covariates` gains the per-pixel names.
- `AnchorAux` gains `pixel_covariates`. `working_bytes` counts the K channels.
- A run reading amplitude reads about twice the bytes of one reading `coh` alone: one `(Y, X)` slab per date against B per date, plus the context.
- The rolling forecasters read none of it. A sample run reads the variables CR-102 put in C3.

### Part 4. Training (ponzi-models)
- `prepare` stores per-pixel covariates as `b{i}_pix (n_px, T, K)`, only the K channels a spec reads. Burst-wide channels stay unstored per pixel, as today.
- `gather_batch` and the augmentations carry them. The training spec gains `inputs:` (2.1).
- `export-pixels` and the panels carry the variables (CR-102 1.8).
- The meta gets `input_grid` and the channel sources (1.2).
- Land cover, if used (D4), comes from an onboarding step that writes a `static` or `asof` variable into the onboarding layer.

### Docs
`models/` (inputs and roles, the leak and why `past_only` exists), `method/` (the grid, alignment), contracts C17 (the alignment block), C3 if its layout changes, the training spec reference, the API reference.

## Do results change?
No, for every existing artifact and standard. A meta without the new kinds builds the same windows bit for bit, a meta without `input_grid` is not checked, and the golden files are unchanged. A fit with per-pixel covariates is a new model, so it gets a new registry entry and needs a new standard to be run.

## Tests
- **Parity** (ponzi): `build_features`, `assemble_single_anchor` and `SingleAnchorTemplate` on every existing meta equal today's output byte for byte. The TiDE golden runs are unchanged.
- **Kinds** (ponzi): `pixel_var` is in the past and future rows, `past_var` and `past_pair` in the past rows only, and `static_var` is constant across rows. The template's per-pixel fill equals `assemble_single_anchor` for each kind. `unknown_future` blanks `pixel_var`.
- **The guard** (ponzi, ponzi-models): a SAR-sourced variable as `known_future` is refused by the training spec and by `load_artifact`.
- **The grid** (ponzi): `load_artifact` refuses an input of another posting, revisit, polarisation, units, or channel source hash. An artifact without `input_grid` warns and runs.
- **Alignment** (ponzi-pipeline): `asof`, `at` and `accum` on synthetic series with dates between acquisitions. `fraction` and `area_mean` on a synthetic finer raster.
- **Runner** (ponzi): a run with a per-pixel channel equals the window builder's arrays at sampled pixels. A run without one reads no extra chunk (counted). A sampled run equals the full run at those pixels.
- **Training** (ponzi-models): `prepare`, `gather_batch` and each augmentation with per-pixel channels. A dropped acquisition drops its covariates. A tiny fit with `past_var` trains and its artifact runs.

## Decisions for the owner
- **D1. A model on another grid** — recommended: refused (posting, revisit, polarisation, units, source hash). The alternative is a warning; a model trained at 40 m and run on 20 m would then score silently. A refused case that should run is a new fit, or a later request for an explicit `accept_sources` list.
- **D2. SAR-derived variables as known-future** — recommended: refused with no override. It is the leak, and no use of it is known.
- **D3. Static per-pixel variables** — recommended: a channel repeated on every row. A static branch in TiDE's encoder is the architecture's own design but changes the model code. Do it later if the repeated channel shows a cost.
- **D4. Land cover** — recommended: ESA WorldCover (10 m, static, open download; no Earth Engine) as `fraction` per class, `static`. A land-cover series that changes over time (`asof`) only when a source without Earth Engine is found.
- **D5. The gate** — recommended: parts 1 to 4 are made only if part 0 shows amplitude lowering the validation CRPS on unchanged pixels without shrinking the z-scores of labelled change. The owner sets the margins before the run. Part 1 is useful without amplitude (it guards today's models against another posting) and may be made alone.
- **D6. Order** — recommended: part 0 after CR-102 (a) and (b); then 1, 2, 3, 4, each implemented and reviewed on its own.

## Version
`ponzi` minor: new channel kinds, `AnchorAux.pixel_covariates`, the meta's `input_grid`, the load check, all additive, and old artifacts are unchanged. `ponzi-pipeline` minor (the alignment block of the onboarding spec, WorldCover if D4). `ponzi-models` minor (`inputs:`, `prepare`, augmentations). Standard: none changes; a model using per-pixel covariates is a new standard.
