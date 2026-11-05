# Roadmap

This page tracks what the overhaul has done and what is left. Each open item says where the work lives, what it needs, how to do it, and when it counts as done.

Pick an open item, read the pages it links to, and follow the [change process](process.md).

**Labels:**

- **local:** runs on any machine with the repositories checked out; the tests use synthetic data.
- **HPC:** needs the cluster.
- **owner:** needs a decision or an approval from the owner.

!!! warning "Before you take an HPC item"
    - A rule for contributors and agents: you submit nothing to a cluster yourself without the owner's approval. The worker itself submits the work it claims, with no approval step (CR-062).
    - Render and show the scripts first: `ponzi-worker run --executor slurm --dry-run` gives the job count, runtime and resources without submitting.
    - Never submit from a machine outside the cluster or from a CI runner.

!!! note "Before you take any item"
    Code changes are reviewed and committed by the owner (decision D10). Leave your work uncommitted in the working tree, or on a branch the owner asked for.

**Getting set up:**

Clone the four repositories side by side: the tests of the suite's files and the agent instructions read ponzi-suite from beside the others.

```
cd ponzi-core    && pixi install && pixi run test        # + test-spec, test-pipeline, test-models
cd ponzi-service && pixi install && pixi run test        # worker, server, client
cd ponzi-visual  && pixi run install && pixi run test    # front end; pixi run e2e against a real server
```

The whole system on one machine, with a standard made on the CPU and the registry on disk:

```
cd ponzi-visual && pixi run install
pixi run server        # the demo (the rehearsal, a standard, 5 bursts run) on :8799; prints the key to enter
pixi run dev           # another shell: http://localhost:5173
```

## Where things stand

| Phase | What | State |
| --- | --- | --- |
| 0 | ISCE3 reference comparison | dropped by the owner on 2026-11-05; no further steps |
| 1 to 5b | Spec, core, models, pipeline, panels, grids | done |
| 6 | Worker, local executor | done |
| 7 | Server, Python client | done |
| 8 | SLURM executor | done locally; first real submission open (HPC) |
| 8b | First standard | done on the CPU with synthetic data; the real standard is open (HPC) |
| 9 | Watched areas | done |
| 10 | ponzi-visual | done; browser end-to-end tests open |
| 11 | Docs | done; docstring backlog open |
| 12 | Retire the old repositories | archiving open (owner) |

## Phase 8: the SLURM executor

- [x] The cluster profile, the script template, batches with dependencies, status from the cache and `sacct`, and the SLURM route of `ponzi-worker job` under `ponzi-client serve` (CR-063).
    - The rendered scripts match the 12 reference scripts (`test_slurm.py`).
    - A fake `sbatch` runs them locally, and the result equals the direct calls.
- [x] The release environments `default`, `ml`, `ml-gpu` and `isce3` in ponzi-service's `pixi.toml`.
- [ ] **Install a ponzi-service release on the lab share.** HPC, owner.
    - Tag ponzi-core and ponzi-service. Check both out under `$LAB/ponzi-service-releases/<release>/` (ponzi-core beside it), then run `pixi install` for each of the four environments.
    - Done when the site file's `release` names it, a new snapshot's `releases.txt` lists it (the profile then has no release warning), and `ponzi-worker stages` runs with each environment's Python.
- [ ] **First worker batch.** HPC, owner.
    - Run one burst of the rehearsal standard with `ponzi-worker run ... --executor slurm` (after a `--dry-run`), and watch it with `ponzi-worker batch`.
    - Done when the batch's job records are in the shared cache and the outputs equal a local run of the same workflow.
- [x] Profiles are made from a snapshot of the cluster and a site file, both in the home: `$PONZI_HOME/cluster/sites/<site>.yaml` is written once for the cluster, and every job makes the profile when it is missing (CR-061, CR-065). No cluster's profile is shipped.
- [ ] **Measure the stages not measured yet.** HPC.
    - These are `ingest-*`, `onboard`, `run`, `pvalues`, `detect`, `tile`, `discover`, `dem` and `assemble`.
    - After the first batches, run `ponzi-worker profile`: its new snapshot holds the completed `ponzi-<stage>` jobs, and those stages take their memory and walltime from them.
    - Done when every stage's resources come from a measurement.
- [x] Watched-area batches need no approval (owner, 2026-11-05, CR-062): the worker submits what it claims; the work is authorised by the request or area made through the client.

## Phase 8b: the first standard

The lifecycle runs end to end on the CPU with the registry on local disk: `ponzi-models rehearse`, then `ponzi-models standard-workflow`. What is left is the same lifecycle at scale, on ISCE3 stores.

- [x] `ponzi_models.synthetic` and `ponzi_models.rehearsal` cover panel, prepare, train (CPU), export, register, null runs, null rows, calibrate, register the calibration, and the checked standard bundle.
    - `pixi run -e ml ponzi-models rehearse --out DIR` fits a tiny TiDE model in about 10 s; `--model rolling` needs no torch.
- [x] The coherence chain as worker stages: `discover`, `dem`, `coherence` (one job per pair) and `assemble`. The assembled store passes `validate-store` (`test_standard.py`).
- [x] `ponzi-models standard-workflow`: a standard bundle as the server runs it. A rehearsed standard runs through the server and a worker (`test_standard.py`).
- [x] Definitions in git, data in the PONZI home. Panels, forecasters, run configs and test cases are in ponzi-suite, and commands take their paths (CR-046 to CR-048). Panel definitions are checked by `ponzi-models panel-check`. The coherence stores, the registry, built panels, standards and the catalogs are in `~/.ponzi` (or `$PONZI_HOME`), made at start by the server and the worker (CR-045, CR-047).
- [x] Composable yaml: every config can build on another with `extends:`; presets are gone, and recipes are yaml files (CR-043). Forecasters, panels and models follow one [naming convention](../reference/naming.md) (CR-052).
- [x] A staged (format 3) calibration from commands: `null-runs --staged`, then `calibrate-staged` (CR-051).
- [ ] **Coherence stores for the panel's bursts.** HPC.
    - List the Major TOM bursts with `ponzi-models panel-cells --burst-map`. Make their stores with the worker's chain: `discover`, then `dem`, `coherence` and `assemble`, as SLURM batches.
    - Earthdata credentials come from `EARTHDATA_USERNAME` and `EARTHDATA_PASSWORD`, else from `~/.netrc` (CR-044).
    - Done when each burst has a store in the cache that passes `ponzi validate-store`.
- [ ] **Build the panel from those stores.** HPC.
    - Command: `ponzi-models panel-build`.
    - Needs per-cell windows in the builder first: `majortom-global` gives a window per cell, and a `PanelSpec` has one (CR-047).
    - Done when the `Panel` reader opens it and its split matches the spec.
- [ ] **Train on the GPU.** HPC.
    - Steps: `ponzi-models prepare`, then `train`, on the cluster's GPU partition (job resources from the profile's `train` entry), then `export` and `register-model`.
    - Done when the model card is in the registry and its artifact digest is verified.
- [ ] **Null and calibration at scale.** HPC.
    - Steps: `null-runs` (an array over the test bursts, both layers), `null-rows`, `calibrate`, `register-calibration`. The standard's staged runs need the staged pair as well: `null-runs --staged`, then `calibrate-staged`.
    - Done when `check-standard` passes.
- [ ] **Set the benchmark and pass it.** Owner, HPC.
    - The owner sets the benchmark the first standard must meet. Done when a report shows the standard meeting it.
    - There is no benchmark command yet.
- [ ] **Weather in the onboarding.**
    - local: the code exists.
    - HPC: needs the network and CDS or EDH credentials.
    - A TiDE standard (the default forecaster) needs the ERA5 series in its sidecars, so the standard's `onboarding` lists `weather` and `pairdiff`, not only `mask`.
    - Done when a TiDE standard runs through the worker on a real burst.
- [ ] **Model stages as worker stages.** local.
    - `prepare`, `train`, `export`, `null-runs`, `null-rows` and `calibrate` run today as `ponzi-models` commands. Making them stages, with content ids, would put the lifecycle itself in the cache and its manifests.
    - Done when `ponzi-models rehearse` can be expressed as a worker workflow.
- [ ] **Decide the default platforms.** Owner.
    - Either S1A only, which is a 12-day series, or S1A with S1C. Today it is S1A.
    - Done when the decision is recorded in the plan and `CoherenceConfig`'s default follows it.
- [ ] **Set the grid default (D9).** Owner.
    - The default is set with the first standard; 40 m, the posting in use today, is the starting point.
- [ ] **The CDSE download route.** local, then HPC.
    - A CDSE fallback search and download when ASF misses a burst. Done when `discover` and `coherence` can take CDSE as the source.
- [ ] **Publish `s1-general@1.0.0`.** Owner.
    - Steps: `ponzi-models standard-workflow ... --source pipeline`, then copy the result into the server's standards folder (`$PONZI_HOME/standards` by default).
    - The draft is ponzi-suite `standards/s1-general-1.0.0.yaml` (CR-055); it waits for its model and calibrations.
- [x] **Enforce a standard's `requires`.** `check-standard` and the worker check it (CR-055).
- [x] **A standard names its panel.** The model and the calibrations must match it; no training cell may be a test cell (CR-055).
- [x] **Versions are held against the one before.** Within a major the runs may not change, within a minor the outputs (CR-055).
- [x] **Library versions in content ids.** The majors of the code that computes a stage (CR-054).

## Phase 9: watched areas

- [x] The server's scheduler, with one job per burst and day; `POST /v1/areas/{id}/discover`; `GET /v1/jobs`.
- [x] Discovery is named by what it found, not by the day it looked; a pair keeps its id however the series grows.
- [x] Monitoring updates are new staged runs. A new acquisition computes only its new pairs and makes exactly one new staged run (`test_watched.py`).
- [x] Areas from administrative boundaries (World Bank Official Boundaries, levels 0 to 2): the server picks the bursts of an orbit pass, and an area's `start_date` and `end_date` bound its jobs (CR-053).
- [x] A job lists the Items it made (`Job.items`), so an area's outputs are its done jobs' Items (CR-042).
- [x] Outputs reach the server by upload or by a shared path, as the server's `outputs` setting says (CR-041).
- [ ] **Run the scheduler in a deployment.** Owner.
    - `scheduler_seconds` in `server.yaml`, default 300; set 0 to turn it off.
    - Done when an active area's jobs appear daily on a deployed server.

## Phase 10: ponzi-visual

- [x] The app's TypeScript client (`src/client` in ponzi-visual), generated from ponzi-server's committed `openapi.json`; `pixi run check-gen` fails when it is stale.
- [x] The full burst catalog:
    - `ponzi-pipeline burst-catalog` reads the OPERA burst database, as the release GeoJSON or the bbox SQLite, and writes an R-tree SQLite catalog (1,127,661 bursts from burst_db 0.18.0);
    - the server answers box queries with a page limit, plus `/v1/bursts/summary` and `/v1/bursts/{id}`;
    - the map loads the bursts in view as it moves;
    - with no `bursts` set, the server builds the catalog into the PONZI home at its first start, from the pinned OPERA file (CR-045).
- [x] The app:
    - the burst map and selection;
    - watched areas;
    - runs;
    - results on the map;
    - the manifest view;
    - an area's page with its outputs (CR-042);
    - areas chosen from administrative boundaries, with the days and the orbit (CR-053).
- [x] Tests:
    - unit tests on the server's own answers (fixtures from `ponzi-worker demo --fixtures`);
    - an end-to-end run against a real server (`pixi run e2e`).
- [ ] **Browser end-to-end tests.** local.
    - Playwright on the built app against the demo server: select a burst, create an area, open a manifest.
    - Done when it runs in CI.
- [ ] **Publish ponzi-visual's client to npm.** Needs the package name, the npm organisation and a publishing token.
- [ ] **Raster display (D12).** local.
    - A `visual` COG per events Item, drawn in the browser; a tiling endpoint only if that is slow.
    - Done when the Results tab can show the events raster of a cell.
- [ ] **Burst catalog updates.** local.
    - burst_db publishes new versions. The server's own catalog is built from the file pinned in `ponzi_spec.catalog` (burst_db 0.18.0); a new pin makes the server rebuild it. Or run `pixi run catalog VERSION` in ponzi-visual (or `ponzi-pipeline burst-catalog`) and give the file as the server's `bursts`.
    - Done when the server's `/v1/bursts/summary` names the new source.
- [ ] **Map tiles in production.** Owner.
    - OpenStreetMap's tile servers are for light use; a deployment needs its own tile source or a provider.

## Phase 11: documentation

- [x] Pages for the quickstart, standards, watched areas, the HPC route, the worker, the service and the clients. This roadmap.
- [x] The store contracts checked against the code, and published with the change requests from ponzi-core at build time (CR-050).
- [x] Every public function has a docstring in ponzi-service, ponzi-spec and ponzi-pipeline. The tests hold that, and a ratchet in ponzi-core (`test_docstrings.py`) holds the rest.
- [ ] **Burn down the docstring backlog.** local.
    - 179 names in `ponzi` and `ponzi_models`, listed in `packages/core/tests/data/docstring_allowlist.txt`. Document a module, take its names off the list, and run `pixi run test`.
    - Done when the list is empty.
- [ ] **Link check in CI.** local.
    - Add a link checker to the docs workflow. Done when broken links fail the build.
- [ ] **Hosting (D15).** Owner.
    - The organisation is `conflict-ecology` and the site's address is `https://conflict-ecology.github.io/ponzi-suite` (CR-049); the docs workflow deploys Pages on a push to main. Left: the repositories and Pages on GitHub. The setup instructions are given to the owner separately and are never part of a repository.

## Phase 12: retire the old repositories

- [ ] **Move the model jobs off the old repository.** Owner.
    - The candidate fits on the v0.4 panel still run from the old repository's job files and its lab-share clone. The new chain does not read that panel (D6), so those jobs end with the old repository.
    - Done when the owner has stopped the v0.4 candidates or recorded their results, and the lab-share clone is no longer used.
- [ ] **Archive the repositories.** Owner.
    - Archive the old repositories on GitHub. Leave the old registry and archive stores untouched and unused.
    - The old registry entries name commits of the old repository that made them, so archive rather than delete it on GitHub. Local clones of the old repositories can be removed.
    - Done when they are read-only and every README points to ponzi-core.

## Decisions still open

| # | Decision | Recommendation |
| --- | --- | --- |
| D11 | The server database | SQLite on one machine (done), Postgres in the cloud |
| D12 | Raster display | a `visual` COG per events Item, in-browser first |
| D13 | Where the registry lives | served by ponzi-server from its storage; the worker caches artifacts by digest |
| new | The default platforms | S1A only until S1C's series is long enough |
