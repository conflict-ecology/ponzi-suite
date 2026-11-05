# The worker

`ponzi-worker` runs workflows. A workflow is a list of stages written as data; the worker plans it, skips what exists, and runs the rest against a content-addressed cache.

- **Stages** are registered under the entry point group `ponzi.stages`. Each declares a `StageSpec`: inputs, outputs, identity params, request params and resources. They are thin adapters over `ponzi`, `ponzi_pipeline` and `ponzi_models`. See [Stages](stages.md).
- **Identity.**
    - A job's id is the content id of its stage, its input ids and its identity params.
    - A stage may look identity params up when it is planned (`derive`): an ingest's digest, a discovery's acquisitions, a burst's box.
    - A stage may expand into one job per entry of an input (`expand_role`), as `coherence` does with one job per pair. That input lists the jobs but is no part of their ids.
- **The cache.**
    - Entries live at `<collection>/<content id>/item.json`, with their files beside it.
    - A job record sits in `jobs/`, and each job writes in `work/<job>/` under a lock.
    - Entries never change once written. Eviction removes the least recently used ones past an age or a size cap.
- **Executors.**
    - `local` runs the job in the worker's process, to the end, in one call.
    - `slurm` submits one array per step; each later call checks it, and submits the next batch once it is done ([Running on the cluster](../guides/hpc.md)).
- **The home.** The worker's home is the deployment config's `roots.data` when that is a local path, else the PONZI home, so a worker on the server's machine shares the server's home. The cache defaults to `$PONZI_HOME/cache`. `ponzi-worker job` and `run` download the OPERA burst map into the home when a workflow needs it and it is missing, and a job's `burst_map`, `slc_dir`, `orbit_dir` and `dem_dir`, when unset, come from the home.
- **No loop of its own** (CR-063). The worker talks to no server. `ponzi-client serve`, the only long-running process, claims a job and calls `ponzi-worker job -` with the job as JSON on stdin, again and again until the answer is `done` or `failed`. Each call is short: a local run to the end, or a SLURM batch submitted or checked. A `done` answer lists the final Items with each asset as a local file (a store zipped into `{cache}/work/deliver-<job>/`); the client uploads them in `upload` mode, or writes them to `<root>/<item_id>/<asset>` in `path` mode, completes the job with the Items and their manifests, and removes the zips.
