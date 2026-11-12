# CR-088: one home, `$PONZI_HOME`, and no deployment config file

- **Requested by / date:** owner, 2026-11-12 ("check the repos that PONZI_HOME ... is used as the ponzi dir that EVERYTHING is stored on by both worker, server, and anyone running anything", then "I want PONZI_HOME to be used")
- **Status:** signed off (2026-11-12), implemented (unreleased)

## Why
An audit of where PONZI keeps its files (2026-11-12, after CR-079 and CR-080) found everything inside the PONZI home by default, but the home had more than one definition, and a service could be told to keep files elsewhere:

1. **Two homes.** The worker's home is `roots.data` of the deployment config (`ponzi.yaml`), which defaults to `$PONZI_HOME`. Everything else asks `$PONZI_HOME` directly: `ponzi-pipeline`'s downloads and `work/`, every `ponzi-models` default (registry, panels, training, models, standards), the panel lookup of `ponzi_models.standards.standard`, and the relative paths a built panel records (`ponzi_models.panels.panel._rel`). A cluster whose `ponzi.yaml` names a shared `roots.data` without `PONZI_HOME` set has its worker in one folder and every command run by hand in `~/.ponzi`.
2. **A third root on clusters.** A site file's `roots.data` is where the SLURM tasks' scratch is redirected (`$DR` in the rendered script), independent of the worker's home. The profile also carries a `cache` that nothing reads.
3. **The server's folders can each be moved.** `server.home`, `data`, `standards`, `outputs.root`, `bursts` and `boundaries` each name a folder or file outside the home. Naming `data` alone moves uploads to `{data}/assets`.
4. **The deployment config does little else.** Nothing reads `cluster_profile`. No code reads or writes a remote root: `s3://` and `gs://` are parsed, and the only use is `local_scratch` falling back to the system's temporary folder. What remains is `server.url` and `server.key_env` for `ponzi-client`, which `--url` and `--key-env` already give. Nothing makes the file; it is written by hand when it is wanted at all.
5. **Leftovers outside the home.** Some outputs, all small and removed after use, are written to the system's temporary folder: the scoring spec `register-model` derives, the throwaway home of `ponzi-server openapi`, and `dev-up.sh`'s settings file. The SLURM tasks find the home only because `sbatch` passes on the submitter's environment.

## What changes
The rule: **the home is `$PONZI_HOME`, else `~/.ponzi`, resolved only by `ponzi_spec.home.ponzi_home`. A service (the server, the worker, the client loop and the SLURM tasks) never keeps a file outside it. A person running a command by hand may still name a file with `--out`.**

**The deployment config goes.** `ponzi_spec.config` is removed: `load_config`, `DeploymentConfig`, `Roots`, `ServerRef`, the lookup (`--config`, `$PONZI_CONFIG`, `./ponzi.yaml`, `$XDG_CONFIG_HOME/ponzi/config.yaml`) and the `PONZI_ROOTS__*` / `PONZI_SERVER__*` variables. If nothing else imports `ponzi_spec.paths` it goes too; `Cache` takes a `Path`.

- ponzi-worker: `worker_layout` becomes `ponzi_spec.home.layout()`. The cache is `{home}/cache`. `--config` and `--cache` are removed from `run`, `job`, `batch`, `manifest` and `evict`; to use another home, set `PONZI_HOME`. `python -m ponzi_worker.node --cache` stays: the worker fills it with its own home's cache.
- Scratch: `local_scratch` becomes the home's `tmp/` (`Layout.tmp`), always local. ISCE3's geocoding scratch is made there.
- ponzi-client: the server is `--url`, else `$PONZI_URL`. The key is unchanged: `$PONZI_KEY`, `--key-env`, `$PONZI_KEY_FILE`. `Client.from_config` is removed.

**The server.** `ServerSettings` loses `data`, `standards`, `outputs.root`, `bursts` and `boundaries` (properties of the home now), and every `ponzi-server` command loses `--home`. `home` stays only as an argument for code that makes a server in its own process (the tests' `local_server`, the demo), never a setting: a settings file naming any of these is refused. The database is `{home}/server/server.db`, the standards `{home}/standards/`, the assets `{home}/outputs/`, the catalog and the boundaries `{home}/catalog/`. In `outputs: {mode: path}` the workers write into `{home}/outputs/`, so the server and those workers must share one home at one path: one machine, or a shared mount. A burst catalog or boundaries file in the home's `catalog/` is used whatever built it, when it is of the format; a small JSON list of bursts is `catalog/bursts.json` (tests, the demo). `ponzi_server.testing.into_home` copies what a test server is given into its home. The demo's folder is its home (`PONZI_HOME=DIR ponzi-server serve --settings DIR/server.yaml`), and its in-process runner is given that home, so the onboarding's `ghsl_dir` and `era5_dir` are filled, which CR-079 had left unset for the demo; a job fetches the burst map only when its workflow names `${burst_map}`. ponzi-visual's `pixi run server` starts the demo's server with `PONZI_HOME` set to the demo folder.

**Other `--home` flags go:** `ponzi-models standard-workflow`, `check-standard`, `new-standard`, `bump-standard`, `register-standard` and `python -m ponzi_spec.cluster.create`. The worker no longer passes `--home` to `profile`.

**The cluster.** A site file's `roots` keeps the folders that are not data (`lab`, where the releases are installed); `data` is no longer a root. In the profile's templates, `{data}` means the home, so redirects such as `TMPDIR: "{data}/tmp/..."` land in the home's `tmp/`. The unused `cache` of the site file and the profile is removed. The rendered script exports `PONZI_HOME` explicitly (`export PONZI_HOME=...`, the worker's home), so a task finds the home without relying on the inherited environment. On a cluster `PONZI_HOME` must be on storage the login node and the compute nodes share; `docs/service/hpc.md` says so where it now says `roots.data`.

**Defaults for the commands that required `--out`.** Each output goes where its kind already lives, or beside the input it is made from, as `ponzi detect` (`<run_dir>/events_<calibration>.zarr`) and `export-pixels` (beside the panel) already do. `--out` stays as an optional override. The layout gains one folder of a kind, `calibrations/`, the calibrations made before `register-calibration` files them, as `models/` holds the artifacts made before `register-model`.

| Command | Reads | Default |
| --- | --- | --- |
| `ponzi-pipeline assemble` | a burst's work folder | that folder, `{home}/work/<burst>/` (the store `<burst>.coh.zarr`); `ingest-coherence` brings it into the cache |
| `ponzi-pipeline onboard` | a coherence store | the store's folder: the sidecar belongs to the store |
| `ponzi-pipeline burst-catalog` | the OPERA burst database | `{home}/catalog/bursts.sqlite3`, the file the server reads |
| `ponzi-models calibrate`, `calibrate-staged` | null runs | `{home}/calibrations/` (`<id>/calibration.npz`) |
| `ponzi detect-path`, `ponzi tile` | several run folders | their common parent folder: `detect-path_<calibration>.zarr`, `tiles_<calibration>/` |
| `ponzi-models rehearse` | (a dry run of training) | `{home}/training/rehearsal/` |
| `ponzi-models eval-breakdowns` | an exported model, a prepared folder | the training root, beside the prepared folder: `eval_breakdowns_<model id>.json` (never inside the model's folder, whose digest it would change) |

**A training spec's paths.** `${PONZI_HOME}` in a training spec's `extra_samples` and `init_from` is the PONZI home whether the variable is set or not (`ponzi_models.training.train.expand_path`); `tide-weather-gaza-finetune` names it for `${PONZI_ROOTS__DATA}`, so its hash changes (nothing pins it).

**The temporary files.** `register-model`'s derived scoring spec, `ponzi-server openapi`'s throwaway home and `dev-up.sh`'s settings file are made under `{home}/tmp/` and still removed after use.

**Docs.** The following are rewritten without the deployment config: `docs/service/configuration.md`, `docs/getting-started/paths.md`, `docs/service/hpc.md` (the home on the shared file system; the site file's roots), `docs/contributing/agents/usage.md`, and the module text of `ponzi_spec.home`. The layout gains `calibrations/`.

**Earlier requests superseded in part** (each marked so):

| Request | No longer holds |
| --- | --- |
| CR-024 | The deployment config of `ponzi-spec` |
| CR-045 | A worker's home is `roots.data` |
| CR-061, CR-065 | A site's `roots.data` and `cache` |
| CR-080 | Scratch is `roots.scratch` |

## Do results change?
No. Where a file is kept is never part of an identity: every content id, spec hash, tag and digest is the same in any home (CR-079, CR-080).

## Tests
- ponzi-spec: `ponzi_home` and `layout` as now, plus `calibrations/` in `test_home_catalog.py`. `test_config.py` is removed. `tmp/` is the scratch.
- ponzi-worker: the home, the cache and the shared inputs follow `PONZI_HOME` (`test_home.py`). A rendered SLURM script exports `PONZI_HOME` and puts a `{data}` redirect under the home (`test_slurm.py`). A profile made from a site file with no `data` root (`test_profile_create.py`).
- ponzi-server: settings with no file put the database, standards, outputs and catalog under the home. A settings file naming a removed field is refused (`extra="forbid"`). Path mode writes into `{home}/outputs/`.
- ponzi-client: `--url`, else `$PONZI_URL`, else an error that says so.
- `ponzi-pipeline` and `ponzi-models`: each command in the table writes its default under the home. No `--home` flag is left.
- Every suite already runs in its own temporary `PONZI_HOME` (CR-080). A test that set `--cache` or `--config` sets `PONZI_HOME` instead.
- A search of the four repositories finds no `load_config`, `roots.data`, `ponzi.yaml` or `PONZI_CONFIG` outside the change requests.

## Version
Library: `ponzi-spec` major (`ponzi_spec.config` removed; the site file and profile lose fields). `ponzi-pipeline` and `ponzi-models` minor (new defaults) and major for `ponzi-models` (`--home` removed). ponzi-service: `ponzi-server`, `ponzi-worker` and `ponzi-client` major (settings fields and flags removed). A server's settings file or a site file that names a removed field must be edited. Standard: no change.

## Decided at sign-off
1. **`database` stays**, for the move to a database server (owner: "eventually I will move over to a database"). A `sqlite:` URL must name a file inside the home; a server URL (PostgreSQL) is not a folder and is allowed.
2. **`--out` stays as an override** on commands run by hand.
3. **No `runs/` folder.** A command's output goes where its kind lives, or beside its input (the table above); the one new folder is `calibrations/`, a folder of a kind.
