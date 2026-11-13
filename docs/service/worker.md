# Workflows and the cache

`ponzi-worker` runs workflows. A workflow is a list of stages written as data; the worker plans it, skips what exists, and runs the rest against a content-addressed cache.

- **Stages** are registered under the entry point group `ponzi.stages`. Each declares a `StageSpec`: inputs, outputs, identity params, request params and resources. They are thin adapters over `ponzi`, `ponzi_pipeline` and `ponzi_models`. See [Stages](../method/stages.md).
- **Identity.**
    - A job's id is the content id of its stage, its input ids, its identity params and its code's majors ([Content ids and reuse](../using/content-ids.md)).
    - A stage may look identity params up when it is planned (`derive`): an ingest's digest, a discovery's acquisitions, a burst's box.
    - A stage may expand into one job per entry of an input (`expand_role`), as `coherence` does with one job per pair. That input lists the jobs but is no part of their ids.
- **The cache.**
    - Entries live at `<collection>/<content id>/item.json`, with their files beside it.
    - A job record sits in `jobs/`, and each job writes in `work/<job>/` under a lock.
    - Entries never change once written. Eviction removes the least recently used ones past an age or a size cap.
- **Executors.**
    - `local` runs the job in the worker's process, to the end, in one call.
    - `slurm` submits one array per step, split to the cluster's limits. A sweep checks every live batch and submits the new work as a new batch beside them; nothing in flight, whoever submitted it, is submitted again ([Running on SLURM](hpc.md#sweeps)).
- **The home.** The worker's home is the PONZI home, `$PONZI_HOME`, else `~/.ponzi` (CR-088), so a worker on the server's machine shares the server's home. The cache is `$PONZI_HOME/cache`. `$PONZI_HOME` is the home, and the hot tier; with `$PONZI_HOME_WARM` and `$PONZI_HOME_COLD` set, the cache's entries are also looked up on the warm and cold tiers, and the downloads are on cold ([Tiers](../getting-started/paths.md#tiers-hot-warm-and-cold); `promote`, `evict --to`, `evict --promoted`). `ponzi-worker job` and `run` download the OPERA burst map into the home when a workflow needs it and it is missing, and a job's `burst_map`, `slc_dir`, `orbit_dir`, `dem_dir`, `ghsl_dir` and `era5_dir`, when unset, come from the home.
- **No loop of its own** (CR-063). The worker talks to no server. `ponzi-client serve`, the only long-running process, claims jobs and calls the worker in short calls, the input as JSON on stdin and the answer, one line of JSON, on stdout (all else goes to stderr). With a SLURM worker it calls `ponzi-worker sweep -` over every held job every `--step-seconds` (answers `running`, `ready` or `failed`), then `ponzi-worker package -` for the ready ones (CR-096); with a local worker it calls `ponzi-worker job -` for each job, a run to the end. A `done` answer lists the final Items with each asset as a file on the worker's machine (a store zipped into `work/deliver-<job>/` in the cache), with each file's size and sha256. The loop never touches those files (CR-098): in `upload` mode the worker sends them with one-time tickets the loop hands it (`ponzi-worker upload`), or the loop fetches them through the worker (`ponzi-worker fetch`, only files under the cache) and sends them; in `path` mode the worker writes them to `$PONZI_HOME/outputs/<item_id>/<asset>` itself (the lease's `root`). The loop completes the job with the Items and their manifests, and has the worker remove the zips (`ponzi-worker clean`). `upload` is the worker's one call to the server: it holds no key, only the tickets.

## A workflow

A workflow is a yaml file of ordered steps. Each step names a stage, its inputs (earlier steps), its identity params (hashed into the step's content id) and its request params (paths and the like, not hashed); `${name}` variables are filled from `--set name=value` (an example is ponzi-service's `packages/worker/tests/data/chain.yaml`).

`ponzi-models standard-workflow` writes the one a standard runs, inside the standard's server file, with its `variables`, `requires` and `final` steps. `ponzi-worker run` takes that file too (told apart by its `standard:` key; ponzi-core CR-090): it runs its workflow with the file's variables, `--set` over them and the home's shared inputs under them, as a server's job has them, so every step has the content id a server gives it; it refuses when the installed distributions do not meet `requires`, or when the workflow is not the one the registry recorded for the standard ([One key, one workflow](../models/versions.md#one-key-one-workflow); a server job is held to the same record), and prints the outputs of the final steps (`final <step> <content ids>`).

- **Plan.** Every job's id is known before anything runs, except for what reads a stage with many outputs, which waits until that stage has run. `--dry-run` prints each job with its id, its status (`cached`, `to run`, or `waits`) and its resources.
- **Run.** A job writes into `work/<job>/`; each output folder is renamed into `<collection>/<content id>/` with its `item.json`, and the job record is written last. A second submission finds every record and runs nothing.
- **Provenance.** `ponzi-worker manifest <content id>` walks an Item's lineage through the cache back to its external sources ([Provenance (manifests)](../using/manifests.md)).
- **Eviction.** `ponzi-worker evict` removes the least recently used entries past an age or a size cap. It never removes an entry given to `--keep` or anything that entry derives from, and does nothing while a job runs. An evicted entry is made again the next time a workflow needs it.

## Commands

```
ponzi-worker stages
ponzi-worker run WORKFLOW.yaml|STANDARD_FILE --set NAME=VALUE ... [--dry-run]
ponzi-worker manifest CONTENT_ID
ponzi-worker evict --older-than-days N | --max-gb G [--keep CONTENT_ID] [--to warm|cold]
ponzi-worker evict --promoted FOLDER [--older-than-days N]
ponzi-worker promote CONTENT_ID|PATH|GLOB ... [--to hot|warm]
ponzi-worker run WORKFLOW.yaml --executor slurm [--profile NAME|FILE]
    [--site NAME|FILE] [--each NAME=V1,V2] [--dry-run] [--print-scripts]
    [--sbatch CMD] [--sacct CMD] [--by NAME]
ponzi-worker batch BATCH
ponzi-worker job FILE|- [--executor local|slurm] [--profile NAME|FILE]
    [--site NAME|FILE] [--sbatch CMD] [--sacct CMD] [--by NAME]
ponzi-worker sweep - [--profile NAME|FILE] [--site NAME|FILE]
    [--sbatch CMD] [--sacct CMD]
ponzi-worker package -
ponzi-worker upload - | fetch PATH | clean JOB_ID ...
ponzi-worker profile [--site NAME|FILE] [--snapshot DIR]
ponzi-worker demo --out DIR [--url URL] [--model rolling|tide]
    [--fixtures FILE] [--burst-catalog FILE] [--boundaries FILE]
```

The SLURM commands are in [Running on SLURM](hpc.md), and `demo` makes the installation of the [Quickstart](../getting-started/quickstart.md), its `--out` folder the home it serves (CR-088).
