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
    - `local` runs each job in the worker's process.
    - `slurm` runs one array per step, behind the approval gate ([Running on the cluster](../guides/hpc.md)).
- **The loop** (`ponzi-worker serve`) claims jobs from the server, runs them, heartbeats meanwhile, uploads the final Items' assets (a store as a zip), and completes the job with the Items and their manifests.
