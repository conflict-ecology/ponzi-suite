# Roadmap

This page tracks what the overhaul has done and what is left. Each open item says where the work lives, what it needs, how to do it, and when it counts as done.

Pick an open item, read the pages it links to, and follow the [change process](process.md).

**Labels:**

- **local:** runs on any machine with the repositories checked out; the tests use synthetic data.
- **HPC:** needs the cluster.
- **owner:** needs a decision or an approval from the owner.

!!! warning "Before you take an HPC item"
    - A rule for contributors and agents: you submit nothing to a cluster yourself without the owner's approval, which may cover many submissions at once ([Cluster approvals](agents/usage.md#cluster-approvals)). The worker itself submits the work it claims, with no approval step (CR-062).
    - Render and show the scripts first: `ponzi-worker run --executor slurm --dry-run` gives the job count, runtime and resources without submitting.
    - Never submit from a machine outside the cluster or from a CI runner.

!!! note "Before you take any item"
    Code changes are reviewed and committed by the owner (decision D10). Leave your work uncommitted in the working tree, or on a branch the owner asked for.

**Getting set up:** clone the four repositories side by side (the tests of the suite's files and the agent instructions read ponzi-suite from beside the others), then follow [Install](../getting-started/install.md#for-development) and the [Quickstart](../getting-started/quickstart.md). The test commands of each repository are in the [Change process](process.md#tests).

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
| 12 | Retire the old repositories | done |

## Phase 8: the SLURM executor

- [x] The cluster profile, the script template, batches with dependencies, status from the cache and `sacct`, and the SLURM route of `ponzi-worker job` under `ponzi-client serve` (CR-063).
    - The tests render the scripts from the profile of a made-up cluster (`test_slurm.py`); no cluster's job files are compared any more (CR-065).
    - A fake `sbatch` runs them locally, and the result equals the direct calls.
- [x] Workers sweep: under SLURM a loop runs one `ponzi-worker sweep` over every job it holds; each sweep submits the new work while earlier batches run, never submits a running batch again, and finds the work an agent submitted (CR-095, CR-096).
- [x] What the sweeps see reaches the server: each job's progress, SLURM ids and batches, and each loop's last report (`ponzi-client job`, `jobs --worker`, `workers`; CR-097).
- [x] The client runs anywhere: its worker here or on another host over one ssh connection (`serve --worker-host`), the final outputs sent from the worker's machine with one-time upload tickets (CR-098).
- [x] One home on three tiers: `$PONZI_HOME` (the hot tier), `$PONZI_HOME_WARM` and `$PONZI_HOME_COLD`; `ponzi-worker promote`, `evict --to` and `evict --promoted` (CR-099).
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
    - `pixi run -e ml ponzi-models rehearse [--out DIR]` fits a tiny TiDE model in about 10 s; `--model rolling` needs no torch.
- [x] The coherence chain as worker stages: `discover`, `dem`, `coherence` (one job per pair) and `assemble`. The assembled store passes `ponzi validate-store` (`test_standard.py`).
- [x] `ponzi-models standard-workflow`: a standard bundle as the server runs it. A rehearsed standard runs through the server and a worker (`test_standard.py`).
- [x] Definitions in git, data in the PONZI home. The specs and test cases are in ponzi-suite, and commands take their paths (CR-046 to CR-048), or their names (CR-070). Panel specs are checked by `ponzi-models panel-check`. The coherence stores, the registry, built panels, standards and the catalogs are in `$PONZI_HOME`, made at start by the server and the worker (CR-045, CR-047); since CR-088 everything is in the one home, and no setting moves a folder out of it.
- [x] Composable yaml: every spec and standard can build on another with `extends:`; presets are gone, and the detection rules are yaml files (CR-043), now detection specs (CR-070). Specs, models and standards follow one [naming convention](../models/naming.md) (CR-052, CR-070).
- [x] A staged calibration from commands: `null-runs --staged`, then `calibrate-staged` (CR-051).
- [ ] **Coherence stores for the panel's bursts.** HPC.
    - List the Major TOM bursts with `ponzi-models panel-cells --burst-map`. Make their stores with the worker's chain: `discover`, then `dem`, `coherence` and `assemble`, as SLURM batches.
    - Earthdata credentials come from `EARTHDATA_USERNAME` and `EARTHDATA_PASSWORD`, else from `~/.netrc` (CR-044).
    - Done when each burst has a store in the cache that passes `ponzi validate-store`.
- [ ] **Build the panel from those stores.** HPC.
    - Command: `ponzi-models panel-build`.
    - The builder takes per-cell windows and builds from the ponzi-suite panel spec (`panel-build --panel-spec majortom-global`, CR-056, CR-070); its `panel.yaml` holds the draw and the coherence spec.
    - Done when the `Panel` reader opens it and its split matches the spec.
- [ ] **Train on the GPU.** HPC.
    - Steps: `ponzi-models prepare`, then `train`, on the cluster's GPU partition (the `gpu` role of the site file) in the `ml-gpu` environment, then `export` and `register-model`.
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
    - A TiDE standard (the default forecaster) needs the ERA5 series in its sidecars: its onboarding runs `weather` and `pairdiff`, as the defaults do (the draft `s1-general` takes them, through the onboarding spec `all-steps`).
    - Done when a TiDE standard runs through the worker on a real burst.
- [ ] **Model stages as worker stages.** local.
    - `prepare`, `train`, `export`, `null-runs`, `null-rows` and `calibrate` run today as `ponzi-models` commands. Making them stages, with content ids, would put the lifecycle itself in the cache and its manifests.
    - Done when `ponzi-models rehearse` can be expressed as a worker workflow.
- [ ] **Decide the default platforms.** Owner.
    - Either S1A only, which is a 12-day series, or S1A with S1C. Today it is S1A.
    - Done when the decision is recorded in the plan and `CoherenceSpec`'s default follows it.
- [ ] **Set the grid default (D9).** Owner.
    - The default is set with the first standard; 40 m, the posting in use today, is the starting point.
- [ ] **The CDSE download route.** local, then HPC.
    - A CDSE fallback search and download when ASF misses a burst. Done when `discover` and `coherence` can take CDSE as the source.
- [ ] **Publish `s1-general`.** Owner.
    - Steps: fill the model and calibrations, set `status: published`, `ponzi-models register-standard`, then `ponzi-models standard-workflow ... --source pipeline`, which writes the server's file into the PONZI home's `standards/`, where the server of that home reads it (CR-088, CR-089).
    - The draft is ponzi-suite `standards/s1-general.yaml` (CR-055, CR-070, CR-089); it waits for its model and calibrations.
- [x] **Enforce a standard's `requires`.** `check-standard` and the worker check it (CR-055).
- [x] **A standard names its panel.** The model and the calibrations must match it; no training cell may be a test cell (CR-055).
- [x] **What a version changes is known.** A standard's version is its content hash; `check-standard` and `register-standard` report and record what it changes from the one before: the runs, the products, or neither (CR-055, CR-089).
- [x] **Library versions in content ids.** The majors of the code that computes a stage (CR-054).
- [x] **Specs, and only the standard versioned.** The files a person writes are training, scoring, panel, detection, coherence and onboarding specs, in folders of those names in ponzi-suite and the PONZI home, each known by its name and recorded in a `specs:` block with its suite commit. A standard is `<sensor>-<scope>`, names its specs, and is written and registered by `new-standard` and `register-standard` (CR-070); since CR-089 it is named by its file and versioned by its content hash, so nothing a person writes has a version number.
- [x] **Versions from hashes and tags.** A spec's version is its hash, cited `name@<hash8>`, and the registry archives every version used (CR-083); a standard lists no stages (CR-084); stages have no version, store contracts and record files are versioned by the hash of their declaration, and every distribution by its git tags (CR-085). See [Versions](../reference/versions.md).

## Phase 9: watched areas

- [x] The server's scheduler, with one job per burst at each area's cadence; `POST /v1/areas/{id}/discover`; `GET /v1/jobs`.
- [x] Discovery is named by what it found, not by the day it looked; a pair keeps its id however the series grows.
- [x] Monitoring updates are new staged runs. A new acquisition computes only its new pairs and makes exactly one new staged run (`test_watched.py`).
- [x] An area's `start_date` and `end_date` bound its jobs (CR-053).
- [x] Areas from an administrative boundary on one orbit pass (CR-053, chosen tracks CR-057), then from one Major TOM cell (CR-066). Both were replaced by areas from tiles only (CR-067); the boundaries are now for drawing only.
- [x] Areas from Major TOM tiles only: tiles over land, every burst of both passes meeting them, its jobs made at once, and tags the server adds to the analysis outputs of its tiles (CR-067). Areas made before from bursts or a boundary keep running.
- [x] An area may be more than 64 tiles: the map and the form warn past 64, the server makes it and logs a warning (CR-074).
- [x] The monitored tiles on the map: monitored in one colour, with outputs and not monitored in another, each opened in a side panel that replaces the Monitored page (CR-075).
- [x] Select tiles by an Admin 1 or Admin 2 boundary: a click adds every tile over land that meets it; a whole country cannot be selected (CR-076).
- [x] The server chooses an area's standard when none is given: `default_standard`, else the one standard it holds, else a 422 saying to set it (CR-068).
- [x] The World Bank's disputed areas (NDLSA) are level 0 boundaries and land, so their tiles can be watched; the map draws the land from the level 0 boundaries (CR-069).
- [x] A job lists the Items it made (`Job.items`), so an area's outputs are its done jobs' Items (CR-042).
- [x] Outputs reach the server by upload or by a shared path, as the server's `outputs` setting says (CR-041).
- [x] The tiles are the only upload: a job delivers its `ponzi-events-cell` Items, not the per-burst `ponzi-events` (CR-100).
- [x] A job is named by its burst's newest acquisition, so a look with nothing new makes no new job, and an upload the server already holds is answered `held` and not sent (CR-101 part a).
- [ ] **Input layers and SAR features (CR-102).** local, then HPC.
    - Signed off: (a) input layers in place of the coherence store and its sidecar, and `scoring.target` (implemented, awaiting review); (b) the features module, the pair chain refactored onto it with byte parity, and amplitude; (c) the stack coregistration and the CSLC cache entry; (d) the stack against pair comparison (owner, cluster).
    - Part (a) lands before CR-101 part (b). Done when a run reads a list of layers, every existing store gives the same outputs bit for bit, and a SAR spec makes coherence and amplitude from CSLCs.
- [ ] **Per-pixel covariates (CR-103).** HPC, then local.
    - Signed off, not started: (0) amplitude as a past-only channel in a ponzi-models experiment, which decides (1) to (4); (1) the model records its input grid and refuses another; (2) the channel kinds and roles; (3) the runner; (4) training. The experiment's margins are the owner's, set before it runs.
    - Follows CR-102 (a) and (b).
- [ ] **Tile series (CR-101 parts b to e).** local, then HPC.
    - Signed off, not started: (b) the burst series, appended update by update, and its parity with a full run; (c) detection with carried state and one tile series per cell and track; (d) delivery of the changed chunks only, and the server's versioned copy of each series; (e) offers, a loop sending the server the series made without it.
    - Each part is implemented and reviewed on its own. Done when a new acquisition sends only the tail chunks of each tile series, and an appended series equals the full run bit for bit.
- [x] People log in with their own key and ask for areas to be watched; an admin user decides, and manages the watched tiles as tracts (CR-093, CR-094).
- [ ] **Presigned uploads to object storage.** local.
    - Assets go to the server's disk for now, by upload or by a shared path.
    - Done when the loop can upload a final asset straight to object storage, through a URL the server signs.
- [ ] **Run the scheduler in a deployment.** Owner.
    - `scheduler_seconds` in `server.yaml`, default 300; set 0 to turn it off.
    - Done when an active area's jobs appear daily on a deployed server.

## Phase 10: ponzi-visual

- [x] The app's TypeScript client (`src/client` in ponzi-visual), generated from ponzi-server's committed `openapi.json`; `pixi run check-gen` fails when it is stale.
- [x] The full burst catalog:
    - `ponzi-pipeline burst-catalog` reads the OPERA burst database, as the release GeoJSON or the bbox SQLite, and writes an R-tree SQLite catalog (1,127,661 bursts from burst_db 0.18.0);
    - the server answers box queries with a page limit, plus `/v1/bursts/summary` and `/v1/bursts/{id}`;
    - the map no longer draws the catalog; it draws the footprints of the bursts meeting the selected tiles (CR-067);
    - with no catalog in the home's `catalog/`, the server builds it there at its first start, from the pinned OPERA file (`fetch_catalog`, CR-045, CR-088).
- [x] The app. Its first versions (a burst map with burst picking, runs, a Results tab, then areas chosen from administrative boundaries, CR-053, and from Major TOM cells, CR-066) were replaced step by step; what it is now:
    - the manifest view;
    - an area's page with its outputs (CR-042), a cell's events store drawn with its dates;
    - areas made from tiles only, clicked on the map, with tags; the boundaries as view-only overlays with their names; the burst footprints of the selected tiles by pass; the skin on a settings page (CR-067).
    - tile submission only: the selected tiles, their tags and a first and last day, the standard and cadence left to the server; a collapsible navigation drawer (CR-068); the areas watched now, first on a Monitored page, now as the monitored tiles on the map (CR-075).
    - a box tool for the tiles from ×32: each box adds the tiles it meets, Shift removes them, Clear empties the selection.
- [x] Tests:
    - unit tests on the server's own answers (fixtures from `ponzi-worker demo --fixtures`);
    - an end-to-end run against a real server (`pixi run e2e`).
- [ ] **Browser end-to-end tests.** local.
    - Playwright on the built app against the demo server: box tiles, create an area, open a manifest.
    - Done when it runs in CI.
- [ ] **Raster display (D12).** local.
    - An area's page already draws a cell's events store, read in the browser from the zipped store (`src/events.ts`). Left: a `visual` COG per events Item (the Collections declare it, optional; no stage writes it yet), and a tiling endpoint only if that is slow.
    - Done when the area's page draws the events Items' `visual` COG.
- [ ] **Burst catalog updates.** local.
    - burst_db publishes new versions. The server builds its catalog from the file pinned in `ponzi_spec.catalog` (burst_db 0.18.0) only when its home has none; a catalog of the format in the home's `catalog/` is used whatever built it (CR-088). For a new version, run `ponzi-pipeline burst-catalog --source FILE`, which writes the home's `catalog/bursts.sqlite3`.
    - Done when the server's `/v1/bursts/summary` names the new source.
- [ ] **Map tiles in production.** Owner.
    - An area's page draws its map on OpenStreetMap's tile servers (the main map is a vector world and needs none). They are for light use; a deployment needs its own tile source or a provider.

## Phase 11: documentation

- [x] Pages for the quickstart, authentication, standards, watched areas, the HPC route, the worker, the service, the clients, the paths and the references. This roadmap.
- [x] The store contracts checked against the code (CR-050), and kept in this suite with the change requests (CR-071).
- [x] Every public function has a docstring in ponzi-service, ponzi-spec and ponzi-pipeline. The tests hold that, and a ratchet in ponzi-core (`test_docstrings.py`) holds the rest.
- [ ] **Burn down the docstring backlog.** local.
    - 175 names in `ponzi` (123) and `ponzi_models` (52), listed in `packages/core/tests/data/docstring_allowlist.txt`. Document a module, take its names off the list, and run `pixi run test`.
    - Done when the list is empty.
- [ ] **Link check in CI.** local.
    - Add a link checker to the docs workflow. Done when broken links fail the build.
- [x] **Hosting (D15).** The repositories are under the GitHub organisation `conflict-ecology`, and the site is at `https://conflict-ecology.github.io/ponzi-suite` (CR-049); the docs workflow deploys Pages on a push to main.

## Phase 12: retire the old repositories

- [x] **Retire the old repositories.** Nothing runs from them or refers to them; what was ported is in ponzi-core's history, and the readers of their formats are removed (CR-082, CR-086).

## Decisions still open

| # | Decision | Recommendation |
| --- | --- | --- |
| D11 | The server database | SQLite on one machine (done), Postgres in the cloud |
| D12 | Raster display | a `visual` COG per events Item, in-browser first |
| D13 | Where the registry lives | served by ponzi-server from its storage; the worker caches artifacts by digest |
| new | The default platforms | S1A only until S1C's series is long enough |
