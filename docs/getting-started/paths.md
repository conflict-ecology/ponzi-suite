# Folders and environment variables

Where PONZI keeps things on a machine, and the variables that move them. Secrets are in [Logins and keys](authentication.md); what is set where is in [Specs and the PONZI home](../service/configuration.md).

## The PONZI home

`$PONZI_HOME` in these docs is the PONZI home: the variable when it is set, else `~/.ponzi` (`ponzi_spec.home`). It is the one folder of every part, the server, the worker, the SLURM tasks and every command run by hand; nothing else names a folder (CR-088). The server makes the folders when it starts and the worker each time it is called; nothing needs setting up by hand.

```
$PONZI_HOME/                     ~/.ponzi by default
  server/                        the server's database
  keys/                          key files, readable by the owner only
                                 (mode 700)
  standards/                     the standards the server runs
  outputs/                       the final assets the server serves (in
                                 path mode the workers write them here)
  catalog/                       the burst map and catalog, the boundaries,
                                 the ASF acquisitions looked up
  cache/                         the worker's content-addressed cache
  registry/                      models and their calibrations
  panels/                        built panels
  training/                      training roots (ponzi-models prepare,
                                 train; CR-080)
  models/<model id>/             exported artifacts before they are
                                 registered (ponzi-models export; CR-080)
  calibrations/<calibration id>/ calibrations made before they are
                                 registered (ponzi-models calibrate; CR-088)
  work/<burst>/                  ponzi-pipeline's coherence work folders
                                 (CR-080), and the store `assemble` writes,
                                 <burst>.sar.zarr (CR-088, CR-102)
  tmp/                           scratch, removed after use (CR-080, CR-088)
  specs/                         working copies of the specs, looked in
                                 before ponzi-suite's (CR-070, CR-078)
  downloads/                     inputs shared by every run
  cluster/                       the site file and SLURM profiles of a
                                 worker's cluster; none is shipped (CR-061,
                                 CR-065)
  logs/                          every log PONZI writes to files (CR-064)
```

Inside the folders, by path in the home:

| Path | What it is |
| --- | --- |
| `server/server.db` | the server's database: areas, watch requests, run requests, jobs, key and session hashes |
| `keys/<name>.key` | as `ponzi-server keys add --out` writes them; under `pixi run dev-up`, dev-visual, dev-worker, dev-admin and dev-user (CR-093) |
| `standards/<id>@<hash8>.yaml` | the standards the server runs (from `ponzi-models standard-workflow`); it reads every file here; under `pixi run dev-up`, also s1-dev@<hash8>.yaml, the development standard (CR-093) |
| `catalog/opera-burst-bbox-only.sqlite3` | the OPERA burst map the worker reads (pinned, sha256 checked) |
| `catalog/burst-id-geometries-simple-*.geojson.zip` | the OPERA burst footprints, as downloaded |
| `catalog/bursts.sqlite3` | the burst catalog the server builds from them (or `ponzi-pipeline burst-catalog` writes) |
| `catalog/boundaries.sqlite3` | the World Bank boundaries, admin 0 to 2 and the disputed areas (CR-053, CR-069) |
| `catalog/boundaries/` | the World Bank GeoParquet files it is built from, as downloaded |
| `catalog/availability/<burst>.json` | ASF acquisitions the server has looked up (CR-060) |
| `cache/<collection>/<content id>/` | one output: item.json and its files, never changed |
| `cache/jobs/<job id>.json` | what a finished job made |
| `cache/work/<job id>/` | a running job's scratch |
| `cache/locks/<job id>.lock` | held while a job runs |
| `cache/slurm/<batch>/` | rendered SLURM scripts and batch.json |
| `registry/<model id>/` | the model card (model.json), the artifact, scoring_spec.yaml, training_spec.yaml |
| `registry/<model id>/calibrations/<calibration id>/` | calibration.npz and its record |
| `registry/standards/<id>@<hash8>/` | a registered standard: standard.yaml and record.json, written once (CR-089); workflow-<source>.json, the workflow standard-workflow built for it (CR-091) |
| `registry/specs/<kind>_specs/<name>/<hash>/` | every spec version used, resolved (CR-083) |
| `panels/<id>@<hash8>/` | a built panel of one panel spec version: masks, draw, catalogue, panel.json |
| `training/prepared_<tag>/` | the prepared files of a panel and a covariate block |
| `training/<training id>/` | one fit: checkpoint.pt, history.json, model_card.yaml, wandb/ |
| `training/wandb/` | wandb's own folders for `train --preflight` |
| `specs/training_specs/`, `scoring_specs/`, `panel_specs/<id>/`, `detection_specs/`, `coherence_specs/`, `onboarding_specs/` | the working copies, one folder per kind of spec |
| `specs/standards/` | standards a person writes, <id>.yaml (`new-standard`; CR-089) |
| `downloads/slc/` | Sentinel-1 SLCs (the parent SLC zip of each burst, `<granule>.zip`) |
| `downloads/orbits/` | orbit files |
| `downloads/dem/` | stitched DEMs, tiles/ the GLO-30 tiles |
| `downloads/ghsl/` | GHSL built-up and land tiles (CR-079) |
| `downloads/era5/` | CDS weather months (CR-079) |
| `cluster/sites/<site>.yaml` | the site file, written once for the cluster |
| `cluster/profiles/<site>.yaml` | the current profile, made from the site file and a snapshot |
| `cluster/profiles/<site>-<version>.yaml` | every version made |
| `cluster/snapshots/<site>/<YYYY-MM-DDTHHMMSS>/` | the last 10 snapshots |
| `logs/slurm/<batch>/<stage>_<job>_<task>.out` | the output of each SLURM task of a batch |
| `logs/client/` | the client loop's own log, when it runs as a SLURM job or under `pixi run dev-up` |
| `logs/server/`, `logs/visual/` | the server's and the front end's logs under `pixi run dev-up` (`server/dev-seed.log`: the Gaza example) |

A home records its own files by paths relative to itself, so a home copied to another machine runs unchanged with the same repositories.

### Tiers: hot, warm and cold

**`$PONZI_HOME` is the home, and the hot tier.** There is no other name for it. Two more variables put parts of the home on other storage (CR-099): `$PONZI_HOME_WARM` and `$PONZI_HOME_COLD`. Unset, cold falls back to warm and warm to hot, so a home without them is one folder, as above.

| Tier | Root | Folders |
| --- | --- | --- |
| hot | `$PONZI_HOME` | `cache/` (where entries are made, with its `work/`, `locks/`, `jobs/`, `slurm/`), `tmp/`, `work/`, `logs/`, `cluster/`, `keys/`, `server/`, `specs/`, `catalog/`, `standards/` |
| warm | `$PONZI_HOME_WARM` | `outputs/`, `registry/`, `models/`, `calibrations/`, `panels/`, `training/` |
| cold | `$PONZI_HOME_COLD` | `downloads/` (`slc/`, `orbits/`, `dem/`, `ghsl/`, `era5/`) |

The rule is fixed in the code: every machine agrees where a folder is without settings. Every tier is mounted at the same path on the login node and every compute node; a SLURM script exports the tiers set.

`cache/` and `downloads/` hold files written once and named by what they are, so a copy in any tier is the same file. New ones are written at the folder's tier (entries on hot, downloads on cold); each is looked up hot, then warm, then cold, and read where it is found. Copies move only when asked:

```
ponzi-worker promote 'downloads/slc/*_202609*'      # copy downloads up to hot (paths, globs, folders)
ponzi-worker promote <content id> ...               # copy cache entries up to hot
ponzi-worker evict --older-than-days 30 --to cold   # move old cache entries down instead of deleting them
ponzi-worker evict --promoted downloads/slc --older-than-days 7   # drop promoted copies; originals stay
```

A record naming a file of the home names it relative to the home, marked `home:` (a panel's `home:cache/ponzi-coherence/<id>/coherence.zarr`), and is read through the tiers: it holds when the file is promoted or evicted to another tier, and when the tiers are copied to another machine (with the variables set there).

## Other paths

| Path | What | Changed by |
| --- | --- | --- |
| `~/.netrc` | Earthdata and Earth Data Hub logins | `NETRC` |
| `~/.cdsapirc` | the Copernicus CDS key | the CDS client's own |
| a server settings file | how the server runs (leases, the outputs mode, downloads, a database server); it names no folder | `ponzi-server serve --settings FILE` |
| ponzi-suite (beside the code repositories) | the specs (`specs/training_specs/`, `specs/scoring_specs/`, `specs/panel_specs/`, `specs/detection_specs/`, `specs/coherence_specs/`, `specs/onboarding_specs/`), standards and test cases: the files PONZI runs from | `PONZI_SUITE`, else the checkout beside ponzi-core |
| `<repo>/.pixi/envs/<env>` | the pixi environments of a checkout (`default`, `ml`, `ml-gpu`, `isce3`) | `pixi install` |

## Environment variables

### Where things are

| Variable | Sets | Default |
| --- | --- | --- |
| `PONZI_HOME` | the PONZI home, and its hot tier | `~/.ponzi` |
| `PONZI_HOME_WARM` | the home's warm tier: outputs, registry, models, calibrations, panels, training (CR-099) | `PONZI_HOME` |
| `PONZI_HOME_COLD` | the home's cold tier: downloads (CR-099) | `PONZI_HOME_WARM` |
| `PONZI_URL` | the server `ponzi-client` and the client loop talk to, without `--url` (CR-088) | |
| `PONZI_SUITE` | the ponzi-suite checkout a spec name is looked up in, after the home's spec folders ([Naming rules](../models/naming.md#spec-folders)) | `ponzi-suite` beside the ponzi-core checkout |

### Keys and logins

| Variable | Read by | For |
| --- | --- | --- |
| `PONZI_KEY` (or the variable `--key-env` names) | ponzi-client and its loop | the server key |
| `PONZI_KEY_FILE` | ponzi-client and its loop | a file holding the server key, read when the variable above is unset |
| `EARTHDATA_USERNAME`, `EARTHDATA_PASSWORD` | `ponzi-pipeline acquire`, the worker | ASF downloads; both set win over the netrc file |
| `NETRC` | `ponzi-pipeline` | another netrc file than `~/.netrc` |
| `WANDB_API_KEY`, `WANDB_ENTITY`, `WANDB_MODE` | `ponzi-models train` | wandb's login, team and mode (wandb's own variables); the trainer sets `WANDB_DIR` and the other wandb folders to the fit's `wandb/` (`--preflight`: the training root's `wandb/`), so nothing is written to `~/.config` or `~/.cache` |

### Running

| Variable | Read by | For |
| --- | --- | --- |
| `PONZI_<ARGUMENT>` | the `ponzi` commands | any argument of a `ponzi` command (`ponzi run` and the others), below its flag |
| `OMP_NUM_THREADS` | `ponzi`, torch, the BLAS libraries | the threads of a run; the SLURM scripts set it to `$SLURM_CPUS_PER_TASK` |
| `PONZI_TIDE_WORKERS` | the TiDE forecaster | its data loader workers (default min(4, torch threads / 2)) |
| `CONDA_OVERRIDE_CUDA` | pixi | install the `isce3` environment where no NVIDIA driver is found (`12.9`) |
| `PONZI_URL` | ponzi-visual's dev server | the same variable as above, here the server the dev server forwards to (default `http://127.0.0.1:8799`, the demo) |
| `PONZI_VISUAL_KEY`, `PONZI_VISUAL_KEY_FILE` | ponzi-visual's dev server | the app's own key (scope `visual`), which it adds to every call it forwards; without either, the demo's `keys.json` ([Logging in to the app](authentication.md#logging-in-to-the-app)) |
| `PONZI_ENVS`, `PONZI_REF` | ponzi-suite's `pixi run dev-install` | the extra environments to install, the branch or tag to clone ([For development](install.md#for-development)) |
| `PONZI_SERVER_PORT`, `PONZI_VISUAL_PORT`, `PONZI_SERVER_HOST`, `PONZI_SERVER_SETTINGS`, `PONZI_WORKER_ID` | ponzi-suite's `pixi run dev-up` | its ports, the server's address and settings, the client loop's name ([Quickstart](quickstart.md#development-setup)) |
