# Paths and environment variables

Where PONZI keeps things on a machine, and the variables that move them. Secrets are in [Authentication](authentication.md); the deployment config is in [Configuration](../service/configuration.md).

## The PONZI home

`$PONZI_HOME` in these docs is the PONZI home: the variable when it is set, else `~/.ponzi` (`ponzi_spec.home`). A worker's home is `roots.data` of its `ponzi.yaml` when that is a local path, and `roots.data` defaults to the PONZI home, so without a config it is `~/.ponzi` for every part; where a worker's `roots.data` is set, read `$PONZI_HOME` in a worker's paths as that folder. The server makes the folders when it starts and the worker each time it is called; nothing needs setting up by hand.

```
$PONZI_HOME/                            ~/.ponzi by default, or the worker's roots.data
  server/
    server.db                           the server's database: areas, requests, jobs, key hashes
  keys/                                 key files, readable by the owner only (mode 700)
    <name>.key                          as `ponzi-server keys add --out` writes them
  standards/
    <id>-<version>.yaml                 the standards the server runs (from `ponzi-models standard-workflow`)
  outputs/                              the final assets the server serves (settings: outputs.root)
  catalog/
    opera-burst-bbox-only.sqlite3       the OPERA burst map the worker reads (pinned, sha256 checked)
    burst-id-geometries-simple-*.geojson.zip   the OPERA burst footprints, as downloaded
    bursts.sqlite3                      the burst catalog the server builds from them
    boundaries.sqlite3                  the World Bank boundaries, admin 0 to 2 and the disputed areas (CR-053, CR-069)
    boundaries/                         the World Bank GeoParquet files it is built from, as downloaded
    availability/<burst>.json           ASF acquisitions the server has looked up (CR-060)
  cache/                                the worker's content-addressed cache (roots.cache)
    <collection>/<content id>/          one output: item.json and its files, never changed
    jobs/<job id>.json                  what a finished job made
    work/<job id>/                      a running job's scratch
    locks/<job id>.lock                 held while a job runs
    slurm/<batch>/                      rendered SLURM scripts and batch.json
  registry/                             models and their calibrations (roots.registry)
    <model id>/                         the model card (model.json), the artifact, scoring_spec.yaml, training_spec.yaml
      calibrations/<calibration id>/    calibration.npz and its record
    standards/<id>@<version>/           a registered standard: standard.yaml and record.json, written once
    specs.json                          the hash each spec name was first used with
  panels/
    <id>/                               a built panel: masks, draw, catalogue, panel.json
  training_specs/                       working copies of the specs, looked in before ponzi-suite's (CR-070)
  scoring_specs/
  panel_specs/<id>/
  detection_specs/
  coherence_specs/
  onboarding_specs/
  downloads/                            inputs shared by every run
    slc/                                Sentinel-1 SLCs (the parent SLC zip of each burst, `<granule>.zip`)
    orbits/                             orbit files
    dem/                                stitched DEMs, tiles/ the GLO-30 tiles
  cluster/                              the site file and SLURM profiles of a worker's cluster; none is shipped (CR-061, CR-065)
    sites/<site>.yaml                   the site file, written once for the cluster
    profiles/<site>.yaml                the current profile, made from the site file and a snapshot
    profiles/<site>-<version>.yaml      every version made
    snapshots/<site>/<YYYY-MM-DDTHHMMSS>/   the last 10 snapshots
  logs/                                 every log PONZI writes to files (CR-064)
    slurm/<batch>/<stage>_<job>_<task>.out   the output of each SLURM task of a batch
    client/                             the client loop's own log, when it runs as a SLURM job or under `pixi run dev-up`
    server/, visual/                    the server's and the front end's logs under `pixi run dev-up`
```

A home records its own files by paths relative to itself, so a home copied to another machine runs unchanged with the same repositories.

## Other paths

| Path | What | Changed by |
| --- | --- | --- |
| `./ponzi.yaml`, `~/.config/ponzi/config.yaml` | the deployment config, the first found of `--config`, `$PONZI_CONFIG`, `./ponzi.yaml`, `$XDG_CONFIG_HOME/ponzi/config.yaml` | `--config`, `PONZI_CONFIG`, `XDG_CONFIG_HOME` |
| `~/.netrc` | Earthdata and Earth Data Hub logins | `NETRC` |
| `~/.cdsapirc` | the Copernicus CDS key | the CDS client's own |
| a server settings file | the server's database, outputs, burst catalog and boundaries; every field has a default under `$PONZI_HOME` | `ponzi-server serve --settings FILE` |
| ponzi-suite (beside the code repositories) | the specs (`training_specs/`, `scoring_specs/`, `panel_specs/`, `detection_specs/`, `coherence_specs/`, `onboarding_specs/`), standards and test cases: the files PONZI runs from | `PONZI_SUITE`, else the checkout beside ponzi-core |
| `<repo>/.pixi/envs/<env>` | the pixi environments of a checkout (`default`, `ml`, `ml-gpu`, `isce3`) | `pixi install` |

## Environment variables

### Where things are

| Variable | Sets | Default |
| --- | --- | --- |
| `PONZI_HOME` | the PONZI home | `~/.ponzi` |
| `PONZI_CONFIG` | the deployment config file | the lookup above |
| `PONZI_ROOTS__DATA`, `PONZI_ROOTS__CACHE`, `PONZI_ROOTS__REGISTRY`, `PONZI_ROOTS__SCRATCH` | `roots.*` of the config | `$PONZI_HOME`, `{data}/cache`, `{data}/registry`, `{data}/tmp` |
| `PONZI_SERVER__URL`, `PONZI_SERVER__KEY_ENV` | `server.*` of the config | |
| `PONZI_CLUSTER_PROFILE` | `cluster_profile` of the config | |
| `PONZI_SUITE` | the ponzi-suite checkout a spec name is looked up in, after the home's spec folders ([Naming](../models/naming.md#spec-folders)) | `ponzi-suite` beside the ponzi-core checkout |
| `PONZI_DATA_ROOT`, `PONZI_MODEL_REGISTRY` | older names of `roots.data` and the registry, below the names above | |
| `XDG_CONFIG_HOME` | where the config is looked up | `~/.config` |

Config variables nest with a double underscore and rank below command-line flags and above the file.

### Keys and logins

| Variable | Read by | For |
| --- | --- | --- |
| `PONZI_KEY` (or the name in `server.key_env`) | ponzi-client, the worker | the server key |
| `PONZI_KEY_FILE` | ponzi-client, the worker | a file holding the server key, read when the variable above is unset |
| `EARTHDATA_USERNAME`, `EARTHDATA_PASSWORD` | `ponzi-pipeline acquire`, the worker | ASF downloads; both set win over the netrc file |
| `NETRC` | `ponzi-pipeline` | another netrc file than `~/.netrc` |
| `WANDB_API_KEY`, `WANDB_ENTITY`, `WANDB_MODE` | `ponzi-models train` | wandb's login, team and mode (wandb's own variables); the trainer sets `WANDB_DIR` and the other wandb folders to its scratch folder |

### Running

| Variable | Read by | For |
| --- | --- | --- |
| `PONZI_<ARGUMENT>` | the `ponzi` commands | any argument of a `ponzi` command (`ponzi run` and the others), below its flag |
| `OMP_NUM_THREADS` | `ponzi`, torch, the BLAS libraries | the threads of a run; the SLURM scripts set it to `$SLURM_CPUS_PER_TASK` |
| `PONZI_TIDE_WORKERS` | the TiDE forecaster | its data loader workers (default min(4, torch threads / 2)) |
| `CONDA_OVERRIDE_CUDA` | pixi | install the `isce3` environment where no NVIDIA driver is found (`12.9`) |
| `PONZI_URL` | ponzi-visual's dev server | the server it forwards to (default `http://127.0.0.1:8799`, the demo) |
| `PONZI_ENVS`, `PONZI_REF` | ponzi-suite's `pixi run dev-install` | the extra environments to install, the branch or tag to clone ([For development](install.md#for-development)) |
| `PONZI_SERVER_PORT`, `PONZI_VISUAL_PORT`, `PONZI_SERVER_HOST`, `PONZI_SERVER_SETTINGS`, `PONZI_WORKER_ID` | ponzi-suite's `pixi run dev-up` | its ports, the server's address and settings, the client loop's name ([Quickstart](quickstart.md#development-on-your-own-home)) |
