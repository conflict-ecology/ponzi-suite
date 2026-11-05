# Roadmap

This page tracks what the overhaul has done and what is left. Each open item says where the work lives, what it needs, how to do it, and when it counts as done.

Pick an open item, read the pages it links to, and follow the [change process](process.md).

**Labels:**

- **laptop:** runs on any machine; the tests use synthetic data.
- **HPC:** needs the cluster.
- **owner:** needs a decision or an approval from the owner.

!!! warning "Before you take an HPC item"
    - Nothing is submitted to a cluster without the owner's approval.
    - Scripts are rendered and shown first: `ponzi-worker run --executor slurm` renders them, and `ponzi-worker approve` shows the job count, runtime and resources, then asks.
    - Never submit from a laptop or a CI runner.

!!! note "Before you take any item"
    Code changes are reviewed and committed by the owner (decision D10). Leave your work uncommitted in the working tree, or on a branch the owner asked for.

**Getting set up:**

```
cd ponzi-core    && pixi install && pixi run test        # + test-spec, test-pipeline, test-models
cd ponzi-service && pixi install && pixi run test        # worker, server, client
cd ponzi-visual  && pixi run install && pixi run test    # front end; pixi run e2e against a real server
```

The whole system on one laptop, with a standard made on the CPU and the registry on disk:

```
cd ponzi-visual && pixi run install
pixi run server        # the demo (the rehearsal, a standard, 5 bursts run) on :8799; prints the key to enter
pixi run dev           # another shell: http://localhost:5173
```

## Where things stand

| Phase | What | State |
| --- | --- | --- |
| 0 | Port reference (ISCE3, repeat_ccd's code) | kit ready, **not yet run** (HPC) |
| 1 to 5b | Spec, core, models, pipeline, panels, grids | done |
| 6 | Worker, local executor | done |
| 7 | Server, Python client | done |
| 8 | SLURM executor | done on the laptop; first real submission open (HPC) |
| 8b | First standard | done on the CPU with synthetic data; the real standard is open (HPC) |
| 9 | Watched areas | done |
| 10 | ponzi-visual | done; browser end-to-end tests open |
| 11 | Docs | done; docstring backlog open |
| 12 | Retire the old repositories | check in place; archiving open (owner) |

## Phase 0: the port reference

repeat_ccd's own ISCE3 functions run on one burst (`t028_058198_iw3`, five pyramid pairs from 2025-03-07). The port is then compared with them stage by stage. This was approved by the owner on 2026-10-23 (D16). The kit is in [ponzi-core `packages/pipeline/reference/phase0`](https://github.com/ORG/ponzi-core/tree/main/packages/pipeline/reference/phase0).

- [x] Driver, pairs and job files; `ponzi-pipeline port-check`. Tested on the laptop: `test_port_check.py`, and every repeat_ccd call it makes binds.
- [ ] **Submit the reference.** HPC, approval given.
    - Before submitting:
        - the overhauled ponzi-core is on the lab share, with `pixi install -e isce3`;
        - Earthdata credentials are in `~/.config/ponzi/credentials.env`.
        - No repeat_ccd checkout: the kit carries the five modules it calls, verbatim at `5250ac4` (`repeat_ccd_5250ac4/SOURCE.md`).
    - Commands, from the kit's folder on the login node:
      ```
      j=$(sbatch --parsable setup.sbatch)
      sbatch --dependency=afterok:$j pairs.sbatch
      ```
    - Done when `$DR/reference/phase0/reference.json` exists.
- [ ] **Run the check.** HPC.
    - Command: `sbatch check.sbatch`.
    - Done when `port_check.json` says `"equal": true`. Otherwise: open a change request with the stage and pair that differ, and the size of the difference.

## Phase 8: the SLURM executor

- [x] The cluster profile (`ceoas`), the script template, batches with dependencies, the approval gate, status from the cache and `sacct`, and `serve --executor slurm`.
    - The rendered scripts match the 12 reference scripts (`test_slurm.py`).
    - A fake `sbatch` runs them locally, and the result equals the direct calls.
- [x] The release environments `default`, `ml`, `ml-gpu` and `isce3` in ponzi-service's `pixi.toml`.
- [ ] **Install a ponzi-service release on the lab share.** HPC, owner.
    - Tag ponzi-core and ponzi-service. Check both out under `$LAB/ponzi-service-releases/<release>/` (ponzi-core beside it), then run `pixi install` for each of the four environments.
    - Done when the site file's `release` names it, a new snapshot's `releases.txt` lists it (the profile then has no release warning), and `ponzi-worker stages` runs with each environment's Python.
- [ ] **First approved worker batch.** HPC, owner.
    - Render one burst of the rehearsal standard with `ponzi-worker run ... --executor slurm`, approve it, and watch it with `ponzi-worker batch`.
    - Done when the batch's job records are in the shared cache and the outputs equal a local run of the same workflow.
- [x] Profiles are made from a snapshot of the cluster and a site file. The worker makes its own when it starts with `--executor slurm` and saves it under `~/.config/ponzi-service/`. The shipped `ceoas@2026.10.27` is made from the snapshot of that day.
- [ ] **Measure the stages not measured yet.** HPC.
    - These are `ingest-*`, `onboard`, `run`, `pvalues`, `detect`, `tile`, `discover`, `dem` and `assemble`.
    - After the first batches, restart the worker: its new snapshot holds the completed `ponzi-<stage>` jobs, and those stages take their memory and walltime from them.
    - Done when every stage's resources come from a measurement.
- [ ] **Decide whether watched-area batches need approval each time.** Owner.
    - Today every batch stops for approval. That includes a watched area's daily update, which comes in several batches: the per-pair coherence jobs are known only once discovery ran.

## Phase 8b: the first standard

The lifecycle runs end to end on the CPU with the registry on local disk: `ponzi-models rehearse`, then `ponzi-models standard-workflow`. What is left is the same lifecycle at scale, on ISCE3 stores.

- [x] `ponzi_models.synthetic` and `ponzi_models.rehearsal` cover panel, prepare, train (CPU), export, register, null runs, null rows, calibrate, register the calibration, and the checked standard bundle.
    - `pixi run -e ml ponzi-models rehearse --out DIR` fits a tiny TiDE model in about 10 s; `--model rolling` needs no torch.
- [x] The coherence chain as worker stages: `discover`, `dem`, `coherence` (one job per pair) and `assemble`. The assembled store passes `validate-store` (`test_standard.py`).
- [x] `ponzi-models standard-workflow`: a standard bundle as the server runs it. A rehearsed standard runs through the server and a worker (`test_standard.py`).
- [ ] **Coherence stores for the panel's bursts.** HPC.
    - List the Major TOM bursts with `ponzi-models panel-cells --burst-map`. Make their stores with the worker's chain: `discover`, then `dem`, `coherence` and `assemble`, as SLURM batches.
    - Done when each burst has a store in the cache that passes `ponzi validate-store`.
- [ ] **Build the panel from those stores.** HPC.
    - Command: `ponzi-models panel-build`.
    - Done when the `Panel` reader opens it and its split matches the spec.
- [ ] **Train on the GPU.** HPC.
    - Steps: `ponzi-models prepare`, then `train`, on `ceoas-gpu` (job resources from the profile's `train` entry), then `export` and `register-model`.
    - Done when the model card is in the registry and its artifact digest is verified.
- [ ] **Null and calibration at scale.** HPC.
    - Steps: `null-runs` (an array over the test bursts, both layers), `null-rows`, `calibrate`, `register-calibration`.
    - Done when `check-standard` passes.
- [ ] **Set the benchmark and pass it.** Owner, HPC.
    - The owner sets the benchmark the first standard must meet. Done when a report shows the standard meeting it.
- [ ] **Weather in the onboarding.**
    - laptop: the code exists.
    - HPC: needs the network and CDS or EDH credentials.
    - A TiDE standard needs the ERA5 series in its sidecars, so the standard's `onboarding` lists `weather` and `pairdiff`, not only `mask`.
    - Done when a TiDE standard runs through the worker on a real burst.
- [ ] **Model stages as worker stages.** laptop.
    - `prepare`, `train`, `export`, `null-runs`, `null-rows` and `calibrate` run today as `ponzi-models` commands. Making them stages, with content ids, would put the lifecycle itself in the cache and its manifests.
    - Done when `ponzi-models rehearse` can be expressed as a worker workflow.
- [ ] **Decide the default platforms.** Owner.
    - Either S1A only, which is a 12-day series, or S1A with S1C. Today it is S1A.
    - Done when the decision is recorded in the plan and `CoherenceConfig`'s default follows it.
- [ ] **Set the grid default (D9).** Owner.
    - The default is set with the first standard; 40 m (repeat_ccd's posting) is the starting point.
- [ ] **The CDSE download route.** laptop, then HPC.
    - repeat_ccd's CDSE search and downloads, not yet ported. Done when `discover` and `coherence` can take CDSE as the source.
- [ ] **Publish `s1-general@1.0.0`.** Owner.
    - Steps: `ponzi-models standard-workflow ... --source pipeline`, then copy the result into the server's standards folder.

## Phase 9: watched areas

- [x] The server's scheduler, with one job per burst and day; `POST /v1/areas/{id}/discover`; `GET /v1/jobs`.
- [x] Discovery is named by what it found, not by the day it looked; a pair keeps its id however the series grows.
- [x] Monitoring updates are new staged runs. A new acquisition computes only its new pairs and makes exactly one new staged run (`test_watched.py`).
- [ ] **Run the scheduler in a deployment.** Owner.
    - `scheduler_seconds` in `server.yaml`, default 300; set 0 to turn it off.
    - Done when an active area's jobs appear daily on a deployed server.

## Phase 10: ponzi-visual

- [x] The app's TypeScript client (`src/client` in ponzi-visual), generated from ponzi-server's committed `openapi.json`; `pixi run check-gen` fails when it is stale.
- [x] The full burst catalog:
    - `ponzi-pipeline burst-catalog` reads the OPERA burst database, as the release GeoJSON or the bbox SQLite, and writes an R-tree SQLite catalog (1,127,661 bursts from burst_db 0.18.0);
    - the server answers box queries with a page limit, plus `/v1/bursts/summary` and `/v1/bursts/{id}`;
    - the map loads the bursts in view as it moves.
- [x] The app:
    - the burst map and selection;
    - watched areas;
    - runs;
    - results on the map;
    - the manifest view.
- [x] Tests:
    - unit tests on the server's own answers (fixtures from `ponzi-worker demo --fixtures`);
    - an end-to-end run against a real server (`pixi run e2e`).
- [ ] **Browser end-to-end tests.** laptop.
    - Playwright on the built app against the demo server: select a burst, create an area, open a manifest.
    - Done when it runs in CI.
    - The package name, the npm organisation and the publishing token.
- [ ] **Raster display (D12).** laptop.
    - A `visual` COG per events Item, drawn in the browser; a tiling endpoint only if that is slow.
    - Done when the Results tab can show the events raster of a cell.
- [ ] **Burst catalog updates.** laptop.
    - burst_db publishes new versions. Run `pixi run catalog VERSION` in ponzi-visual (or `ponzi-pipeline burst-catalog`) and replace the server's catalog file.
    - Done when the server's `/v1/bursts/summary` names the new source.
- [ ] **Map tiles in production.** Owner.
    - OpenStreetMap's tile servers are for light use; a deployment needs its own tile source or a provider.

## Phase 11: documentation

- [x] Pages for the quickstart, standards, watched areas, the HPC route, the worker, the service and the clients. This roadmap.
- [x] Every public function has a docstring in ponzi-service, ponzi-spec and ponzi-pipeline. The tests hold that, and a ratchet in ponzi-core (`test_docstrings.py`) holds the rest.
- [ ] **Burn down the docstring backlog.** laptop.
    - 180 names in `ponzi` and `ponzi_models`, listed in `packages/core/tests/data/docstring_allowlist.txt`. Document a module, take its names off the list, and run `pixi run test`.
    - Done when the list is empty.
- [ ] **Link check in CI.** laptop.
    - Add a link checker to the docs workflow. Done when broken links fail the build.
- [ ] **Hosting (D15).** Owner.
    - Repositories, Pages and the `<org>` placeholder. The setup instructions are given to the owner separately and are never part of a repository.

## Phase 12: retire the old repositories

- [x] Nothing of the four distributions imports, edits `sys.path` for, or names a path inside ponzi-models (as a repository), ponzi-apps, ponzi-paper or the monorepo (`test_retired.py`).
- [x] Nothing needs a repeat_ccd checkout. The phase 0 kit carries its own verbatim copy of the five modules it calls, checked against their git blob ids, and `test_retired.py` holds that no file asks for a checkout.
- [ ] **Move the model jobs off the old repository.** Owner.
    - The candidate fits on the v0.4 panel still run from ponzi-models' `hpc/` job files and its lab-share clone. The new chain does not read that panel (D6), so those jobs end with the old repository.
    - Done when the owner has stopped the v0.4 candidates or recorded their results, and the lab-share clone is no longer used.
- [ ] **Archive the repositories.** Owner.
    - Archive ponzi-models (the repository), ponzi-apps and ponzi-paper on GitHub. Leave the old registry and archive stores untouched and unused.
    - The archived repository keeps the history the old registry entries name (each records the ponzi-models commit that made it), so archive rather than delete it on GitHub. Local clones of ponzi-models and repeat_ccd can be removed.
    - Done when they are read-only and every README points to ponzi-core.

## Decisions still open

| # | Decision | Recommendation |
| --- | --- | --- |
| D11 | The server database | SQLite on one machine (done), Postgres in the cloud |
| D12 | Raster display | a `visual` COG per events Item, in-browser first |
| D13 | Where the registry lives | served by ponzi-server from its storage; the worker caches artifacts by digest |
| new | The default platforms | S1A only until S1C's series is long enough |
| new | Standing approval for watched-area batches | approval per batch until the first month of updates has been watched |
