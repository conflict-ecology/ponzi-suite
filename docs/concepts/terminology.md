# Terminology

The words PONZI uses, grouped with the words they are easily confused with. Each group says how its terms differ. Names follow the [naming convention](../reference/naming.md); formats are in the [store contracts](../reference/contracts.md).

## Words with two meanings

| Word | Meaning 1 | Meaning 2 |
| --- | --- | --- |
| **stage** | a unit of a workflow the worker runs: `discover`, `coherence`, `assemble`, `onboard`, `run`, `pvalues`, `detect`, `tile` ([Stages](stages.md)) | in progressive scoring, how many of an anchor's future acquisitions are known: stage 1 to H - 1 is provisional, stage H is final (CR-021) |
| **window** | the span of anchors a run scores (`t_lo` to `t_hi`) | the area of a mask layer a run reads; or the estimator's Gaussian window in coherence |
| **run** | one forecast run of one burst under one run config (`ponzi run`, a `ponzi-run` Item) | loosely, any execution; this documentation uses *job* for that |
| **path** | one track seen in one direction, the bursts a detection combines (`detect-path`) | a file path |

## Where: places on the ground

| Term | What it is | Not to be confused with |
| --- | --- | --- |
| **scene** | one Sentinel-1 IW SLC acquisition as ESA distributes it, about 250 by 170 km; downloads are by scene | a burst: a scene holds about 27 bursts, and its frame shifts from pass to pass |
| **burst** | the fixed unit of processing: one subswath's slice of about 20 by 85 km, the same ground at every pass of its track; id `t028_058198_iw3` (track, burst number, subswath) | a scene; a cell |
| **subswath** | one of the three strips of an IW acquisition, `iw1` to `iw3` | |
| **track** (relative orbit) | the repeating ground path of the satellite, 1 to 175 | a path (a track *and* a direction) |
| **orbit pass** | ascending or descending; one track crosses a place in one pass | |
| **cell** | a square of the Major TOM grid (10 km), the unit of panels and of the delivered outputs | a burst; a pixel |
| **grid**, **lattice** | the fixed raster a burst is processed on (UTM, 40 m), or the raster a path or cell is resampled to | ([Grids](grids.md)) |
| **boundary** | an administrative unit of the World Bank Official Boundaries, level 0 (country), 1 or 2 | an area |
| **area** (watched area) | what the server keeps running: bursts, a standard, a cadence, optionally a boundary, an orbit pass and a first and last day | an AOI |
| **AOI** | area of interest: a place studied (Gaza, Tehran), as a test case or an area | |

## What: the data

| Term | What it is | Not to be confused with |
| --- | --- | --- |
| **acquisition** | one pass's image of a burst, on one date | a pair |
| **pair** | two acquisitions a baseline apart; its coherence is one value per pixel | |
| **baseline** | the days between a pair's acquisitions: 12, 24, 36, 48, 60 | the perpendicular baseline (`bperp`), the satellites' separation in metres |
| **coherence store** | one burst's coherence over time, `(time, y, x, baseline)` (C1) | a pair raster (one pair, before assembly) |
| **sidecar** | a burst's covariates: weather, built-up, the process mask (C2) | the coherence store it sits beside |
| **mask store** | named boolean layers on a burst's grid, such as `sample_test` and `cell_train` (C23) | the process mask (which pixels are scored at all) |
| **pixel sample** | a small store of chosen pixels from a burst (C3) | a mask layer |

## When: time in a run

| Term | What it is |
| --- | --- |
| **anchor** | the acquisition `t` a forecast is scored at |
| **context** (C) | the acquisitions before the anchor the forecaster reads (30) |
| **horizon** (H), **block** | the acquisitions `t` to `t + H - 1` forecast at once (H = 5); the 25 pairs ending on them |
| **pyramid** | the 15 pairs of the block that span the gap before `t`; their z values are averaged into the anomaly score |
| **stage** (progressive) | see *Words with two meanings* |
| **span** | an area's first and last day; a job's `start_date` and `end_date` |

## How strong: scores and codes

| Term | What it is | Not to be confused with |
| --- | --- | --- |
| **z** | one pair's observed coherence against its forecast | the anomaly score |
| **anomaly score** | the aggregate z of an anchor's pyramid (`score.zarr`, C7) | a p-value |
| **ceiling score** | the score the pixel would get if every pair were observed at the noise floor: the largest alarm it can raise | the anomaly score |
| **noise floor** | the coherence a fully decorrelated target still reads, from the estimator's looks and window | zero |
| **null** | the anomaly scores of the panel's test cells, where nothing happened | |
| **p-value** | the share of the null at or above a score | |
| **code** | `round(20 * -log10 p)` stored as one byte (C22); code 50 is p = 0.003 | a score |
| **flag** | an anchor whose code is at or above the recipe's threshold | an event |
| **provisional**, **withdrawn** | a flag at an early stage, and one the final stage does not confirm (CR-021) | |
| **Et** | the break statistic that dates a run of flags (`summary.zarr`, C24) | E, the difference of means Et is made from |
| **event** | a dated change of a pixel: a run of flags, dated by Et (C25) | a flag |

## The model side

| Term | What it is | Not to be confused with |
| --- | --- | --- |
| **forecaster** | a kind of forecasting method, the code that predicts coherence (`tide`, `rolling_ols`) | a model |
| **fit spec** | a forecaster file: everything one training fixes (C, H, inputs, missing values, augmentation, seed) | a run config |
| **candidate** | a fit spec being compared with the base (`candidates/`), not a registered model | |
| **fit** | one training of a fit spec on a panel; `-seed43` for another seed | |
| **artifact** | the exported TorchScript folder with its `meta.json` | a model (the artifact plus its registry entry) |
| **model** | a registered artifact with its run config and model card, `tide-weather--majortom-global-0.4.0` | a forecaster |
| **run config** | how a model is run: C, H, scoring, aggregation, state machine (C4); its hash is fixed when the model is registered | a run request (C4a: paths, dates and options of one run) |
| **registry** | the folder of models and their calibrations, `{home}/registry` | the server's database |

### From forecaster to model, step by step

Each step makes the next thing from the one before, with one command:

| Step | Command | Makes | Example |
| --- | --- | --- | --- |
| 1. Choose a forecaster | | the kind of method | `tide`, the TiDE neural network (`ponzi.core.forecast`) |
| 2. Write a fit spec | | what one training fixes: context, horizon, inputs, missing values, augmentation, seed | `forecasters/tide/weather.yaml`, named `tide-weather` |
| 3. Train | `ponzi-models train` | a **fit**: the trained weights of the spec on a panel, as a checkpoint | `tide-weather`, or `tide-weather-seed43` at another seed |
| 4. Export | `ponzi-models export` | an **artifact**: the fit as self-contained TorchScript with its `meta.json` (window layout, channels, scalers, missing values) | a `torchscript/` folder; inference needs nothing else |
| 5. Register | `ponzi-models register-model` | a **model**: the artifact filed with one run config and a model card | `tide-weather--majortom-global-0.4.0` in `{home}/registry` |

Only a model can be used: calibrations are made for it, and run configs and standards name it as `registry:<model id>@sha256:<digest>`. Two things follow from the steps:

- **A model may have no artifact.** A rolling forecaster such as `rolling_ols` fits itself as it runs and has no trained weights, so steps 3 and 4 do not apply: its model is its run config and model card.
- **One artifact can make two models.** The same weights registered with another run config give another model, of another run config hash, and its calibrations are its own: a calibration belongs to one run config.

## Calibration and panels

| Term | What it is | Not to be confused with |
| --- | --- | --- |
| **panel** (definition) | the git-tracked set of cells and bursts in `panels/<id>/`, `majortom-global@0.4.0` | a built panel |
| **built panel** | the panel's stores, masks and draw, made into `{home}/panels/<id>@<version>` | |
| **split** | train, val or test; test is the calibration null | |
| **calibration** | the mapping from scores to codes, filed under one model for one run config | a recipe |
| **plain**, **ceiling** calibration | against the whole null, or against the null of the pixel's ceiling class | the ceiling score (which the ceiling calibration uses) |
| **format 2**, **format 3** | a calibration file of the final stage only, or with one mapping per stage (staged) | |

## Bundles: what fixes a result

| Term | What it fixes | Not to be confused with |
| --- | --- | --- |
| **recipe** | the detection rules: threshold code, dating, gaps, episodes | a calibration |
| **workflow** | the stages and their order for one burst, with variables | a job (one workflow for one burst and span) |
| **standard** | everything an area runs, under one id and version (`s1-general@1.0.0`): the workflow, the coherence and onboarding configs, the model, its run config, its calibrations, the recipe ([Standards](../guides/standards.md)) | a release of the library |
| **test case** | a place used for testing, `testcases/<case>/`: its area, recipe and forecaster | a standard |

## The service

| Term | What it is | Not to be confused with |
| --- | --- | --- |
| **server** | keeps the areas, requests, jobs and final outputs; computes nothing | the worker |
| **worker** | claims jobs, runs their stages, saves the outputs | |
| **client** | the Python `ponzi-client`, or ponzi-visual in the browser | |
| **request** | a one-off run of bursts under a standard | an area (which keeps making jobs) |
| **job** | one unit the server hands out: a workflow for one burst and span | a run |
| **lease** | a worker's hold on a job, renewed by heartbeats | |
| **home** | the folder everything computed lives in, `~/.ponzi` or `$PONZI_HOME` | a repository |
| **cache** | the worker's store of outputs by content id, `{home}/cache` | |
| **Item**, **collection**, **asset** | a STAC record of one output, its kind (`ponzi-run`), and one of its files ([STAC profile](stac-profile.md)) | |
| **manifest** | the readable provenance of an output: every step and input that made it ([Manifests](manifests.md)) | |

## Identity and versions

| Term | What it identifies | Changes when |
| --- | --- | --- |
| **content id** | one output, from its stage, its stage version, its inputs' ids and its parameters ([Content ids](content-ids.md)) | any of those change |
| **stage version** | a stage's identity, `"1"` | raised by hand when its outputs may change |
| **config hash** | a run config, composed | any key changes |
| **digest**, **sha256** | the bytes of a file or store | the bytes change |
| **library version** | a release of `ponzi` (git tag, `0.2.4`); a calibration refuses another major | a release |
| **panel version** | a panel definition, semver in `panel.yaml` | its files change |
| **standard version** | a standard, semver | anything in it changes |
| **name** | a readable label (`tide-weather`), never an identity on its own | |
