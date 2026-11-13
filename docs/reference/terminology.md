# Glossary

The words PONZI uses, grouped with the words they are easily confused with. Each group says how its terms differ. Names follow the [naming convention](../models/naming.md); formats are in the [Store formats (contracts)](contracts.md).

## Words with two meanings

| Word | Meaning 1 | Meaning 2 |
| --- | --- | --- |
| **stage** | a unit of a workflow the worker runs: `discover`, `dem`, `coherence`, `assemble`, `onboard`, `run`, `pvalues`, `detect`, `tile`, and the `ingest-coherence` and `ingest-calibration` stages ([Stages](../method/stages.md)) | in progressive scoring, how many of an anchor's future acquisitions are known: stage 1 to H - 1 is provisional, stage H is final (CR-021) |
| **window** | the span of anchors a run scores (`t_lo` to `t_hi`) | the area of a mask layer a run reads; or the estimator's Gaussian window in coherence |
| **run** | one forecast run of one burst under one scoring spec (`ponzi run`, a `ponzi-run` Item) | loosely, any execution; this documentation uses *job* for that |
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
| **grid**, **lattice** | the fixed raster a burst is processed on (UTM, 40 m), or the raster a path or cell is resampled to | ([Grids: processing and outputs](../method/grids.md)) |
| **tile** | a cell of the Major TOM grid over land, as a watched area is made from it | |
| **boundary** | an administrative unit of the World Bank Official Boundaries, level 0 (a country, or a disputed area of non-determined legal status), 1 or 2; drawn on the map and the land a tile must meet, never what an area is made from | an area |
| **tract** | watched tiles that touch by an edge, of one or more areas: what an admin user manages together; computed from the areas, named by its first tile (CR-094) | an area (one approved request); a region (a panel spec's) |
| **area** (watched area) | what the server keeps running: 1 or more tiles, every burst of both passes meeting them, a standard (the server's `default_standard` when none is given), a cadence, tags and optionally a first and last day | an AOI |
| **tag** | one word of an area (letters, digits, `-`, `_`), added by the server to the analysis outputs of its tiles as it serves them; never part of a content id | a name; a label (C11) |
| **watch request** | a person's request to watch tiles over a span of days, which an admin user approves (making the area) or denies | a run request (one-off bursts) |
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
| **flag** | an anchor whose code is at or above the detection spec's threshold | an event |
| **provisional**, **withdrawn** | a flag at an early stage, and one the final stage does not confirm (CR-021) | |
| **Et** | the break statistic that dates a run of flags (`summary.zarr`, C24) | E, the difference of means Et is made from |
| **event** | a dated change of a pixel: a run of flags, dated by Et (C25) | a flag |

## The model side

| Term | What it is | Not to be confused with |
| --- | --- | --- |
| **forecaster** | a kind of forecasting method, the code that predicts coherence (`tide`, `rolling_ols`, `stored`, `external`); TiDE is the default today; any registered forecaster works the same way | a model |
| **training spec** | how a model is trained: everything one training fixes (C, H, inputs, missing values, augmentation, seed), `specs/training_specs/` | a scoring spec; the forecaster (the code) |
| **candidate** | a training spec being compared with the base (`candidates/`), not a registered model | |
| **fit** | one training of a training spec on a panel; `-seed43` for another seed | |
| **artifact** | the exported fit of a trained forecaster: for TiDE, the default, a TorchScript folder with its `meta.json` | a model (the artifact plus its registry entry) |
| **model** | a registered artifact with its scoring spec and model card, `<training spec>@<hash8>--<panel spec>@<hash8>` (`tide-weather@59bfd3dc--majortom-global@2436d8cb`) | a forecaster |
| **scoring spec** | how a model is applied to a burst: C, H, scoring, aggregation, state machine (C4), `specs/scoring_specs/`; its hash is fixed when the model is registered | a run request (C4a: paths, dates and options of one run) |
| **registry** | the folder of models and their calibrations, the home's `registry/`, on the warm tier (CR-099) | the server's database |

### From forecaster to model, step by step

Each step makes the next thing from the one before, with one command. The examples use TiDE, the default forecaster; another forecaster follows the same steps:

| Step | Command | Makes | Example |
| --- | --- | --- | --- |
| 1. Choose a forecaster | | the kind of method | `tide`, the TiDE neural network and today's default, or any other registered in `ponzi.core.forecast` (`rolling_ols`, ...) |
| 2. Write a training spec | | what one training fixes: context, horizon, inputs, missing values, augmentation, seed | `specs/training_specs/tide/tide-weather.yaml`, named `tide-weather` |
| 3. Train | `ponzi-models train` | a **fit**: the trained weights of the spec on a panel, as a checkpoint | `tide-weather`, or `tide-weather-seed43` at another seed |
| 4. Export | `ponzi-models export` | an **artifact**: the fit in a self-contained form; for TiDE, TorchScript with its `meta.json` (window layout, channels, scalers, missing values) | a `torchscript/` folder; inference needs nothing else |
| 5. Register | `ponzi-models register-model` | a **model**: the artifact filed with one scoring spec and a model card | `tide-weather@59bfd3dc--majortom-global@2436d8cb` in the registry |

Only a model can be used: calibrations are made for it, and scoring specs and standards name it as `registry:<model id>@sha256:<digest>`. Two things follow from the steps:

- **A model may have no artifact.** A rolling forecaster such as `rolling_ols` fits itself as it runs and has no trained weights, so steps 3 and 4 do not apply: its model is its scoring spec and model card.
- **One artifact can make two models.** The same weights registered with another scoring spec give another model, of another scoring spec hash, and its calibrations are its own: a calibration belongs to one scoring spec.

## Calibration and panels

| Term | What it is | Not to be confused with |
| --- | --- | --- |
| **panel spec** | the git-tracked folder of cells, bursts and build settings, `specs/panel_specs/<id>/` (`majortom-global`); its version is its hash ([Training panels](../method/panels.md)) | a built panel |
| **built panel** | the panel's stores, masks and draw, made into the home's `panels/<id>@<hash8>`, on the warm tier (CR-099) | |
| **split** | train, val or test; test is the calibration null | |
| **calibration** | the mapping from scores to codes, filed under one model for one scoring spec | a detection spec |
| **plain**, **ceiling** calibration | against the whole null, or against the null of the pixel's ceiling class | the ceiling score (which the ceiling calibration uses) |
| **staged** calibration | a calibration file with one mapping per stage, beside the final stage's | |

## Bundles: what fixes a result

| Term | What it fixes | Not to be confused with |
| --- | --- | --- |
| **spec** | a file a person writes, validated by PONZI, that says how something is made: a training, scoring, panel, detection, coherence or onboarding spec, known by its name and hash ([Naming rules](../models/naming.md#spec-folders)) | a standard; the server's settings |
| **detection spec** | the detection rules: threshold code, dating, gaps, episodes, `specs/detection_specs/` | a calibration |
| **coherence spec**, **onboarding spec** | how a burst's coherence store is made (backend, looks, window, grid, DEM), and its sidecar and pixel sample, `specs/coherence_specs/`, `specs/onboarding_specs/` | |
| **workflow** | the stages and their order for one burst, with variables | a job (one workflow for one burst and span) |
| **standard** | everything an area runs, under one id `<sensor>-<scope>`, its file's name, and a version, its content hash (`s1-general@3f9a12c4`): the panel, coherence, onboarding and detection specs by name, the model, its scoring spec hash, its calibrations ([Standards](../models/standards.md)) | a release of the library |
| **test case** | a place used for testing, `testcases/<case>/`: its area, detection spec and training spec | a standard |

## The service

| Term | What it is | Not to be confused with |
| --- | --- | --- |
| **server** | keeps the areas, requests, jobs and final outputs; computes nothing | the worker |
| **worker** | the `ponzi-worker` program, run by the client loop in short calls (`sweep`, `package`, `job`); runs the stages or submits their SLURM jobs, keeps the outputs in its cache. Also the name of a key scope (`worker`, what a loop's key holds) and of the server's `worker_id`, which names a loop | the client loop |
| **client** | the Python `ponzi-client`, or ponzi-visual in the browser; `ponzi-client serve` is the client loop, the only long-running process | |
| **loop** | one `ponzi-client serve` process, known to the server by its `--worker-id` | the worker |
| **sweep** | one short call of the worker over every job a loop holds: what is in flight checked, all new work submitted once (CR-096) | a batch |
| **task** | one job of the worker's plan (one stage on its inputs, named by its content id); one element of a SLURM array | a job (the server's) |
| **in flight** | a task in a live SLURM batch, whoever submitted it, neither finished nor failed | |
| **hot**, **warm**, **cold** | the tiers of a home's storage (CR-099): `$PONZI_HOME` (the home, and the hot tier), `$PONZI_HOME_WARM`, `$PONZI_HOME_COLD`; each folder on one by a fixed rule | |
| **agent** | anything that runs PONZI work on the cluster without a loop (`ponzi-worker run`), by a person, a script or an AI agent | a loop |
| **request** | a one-off run of bursts under a standard | an area (which keeps making jobs); a watch request |
| **user**, **admin user** | a person with a key of scope `user` (asks for areas, searches, downloads) or `user-admin` (also decides requests and makes people's keys) | the `admin` scope (the server's operator) |
| **session** | a person logged in to the app: a cookie the page cannot read, swapped for their key at login; the server keeps only its hash | a key |
| **job** | one unit the server hands out: a workflow for one burst and span | a run |
| **lease** | the client loop's hold on a job, renewed by heartbeats | |
| **home** | the one folder an installation keeps everything in, `$PONZI_HOME`, else `~/.ponzi` (CR-088) | a repository |
| **cache** | the worker's store of outputs by content id, `$PONZI_HOME/cache` | |
| **Item**, **collection**, **asset** | a STAC record of one output, its kind (`ponzi-run`), and one of its files ([STAC catalog profile](../using/stac-profile.md)) | |
| **manifest** | the readable provenance of an output: every step and input that made it ([Provenance (manifests)](../using/manifests.md)) | |

## Identity and versions

| Term | What it identifies | Changes when |
| --- | --- | --- |
| **content id** | one output, from its stage, the majors of its code, its inputs' ids and its parameters ([Content ids and reuse](../using/content-ids.md)) | any of those change |
| **code majors** | the major of each distribution that computes a stage, in its content ids and its Items' `ponzi:stage` (CR-054, CR-085); stages have no version of their own | a release's version |
| **spec hash** | a spec, composed and with the code's defaults filled in (`spec_hash`) | any resolved setting changes |
| **contract version** | a store's or a record file's layout: the hash of its declaration (`contract_hash`, CR-085), pinned by a test ([Versions](versions.md)) | its declaration changes |
| **digest**, **sha256** | the bytes of a file or store | the bytes change |
| **library version** | a release of `ponzi` (git tag `vX.Y.Z`, [Versions](versions.md#releases-the-tags)); a calibration refuses another major | a release |
| **standard version** | a standard: the content hash of its file, cited `<id>@<hash8>` (CR-089); nobody writes it ([Versions](versions.md), [Standard versions](../models/versions.md)) | anything in it but its description, or a spec it names, changes |
| **name** | a readable label (`tide-weather`), never an identity on its own; a spec's version is its hash, cited `name@<hash8>`, and the registry archives every version used | |
