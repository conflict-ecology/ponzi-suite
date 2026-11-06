# CR-063: the client is the only long-running process; the worker runs in short calls

- **Requested by / date:** owner, 2026-11-05 ("I want the client to be the only long running process. the work should be short lived to perform tasks that the client retrieves from the server.")
- **Status:** implemented on the owner's instruction (2026-11-05)

## Why

The loop that claimed jobs, heartbeated, delivered outputs and completed jobs was `ponzi-worker serve`, a long-running worker process that also talked to the server. The owner's design: the client alone talks to the server and is the one process that keeps running; the worker only carries out what the client hands it, and exits.

## What changes

- **`ponzi_client.serve`, `ponzi-client serve --worker-id ID [-- WORKER ARGS]`:** the loop, moved from `ponzi_worker.loop`. It claims jobs for the stages the worker has (`ponzi-worker stages --json`), calls `ponzi-worker job -` with each job as JSON on stdin, heartbeats the lease meanwhile, calls again every `--step-seconds` while the answer is `running`, then delivers the final assets (upload, or in path mode a copy under the lease's `outputs.root`), completes the job, and removes the worker's delivery scratch. A failed answer, or no answer, fails the job. It imports nothing that computes.
- **`ponzi_worker.job`, `ponzi-worker job FILE|-`:** one short call on one job; it talks to no server. With `--executor local` it runs the workflow to the end; with `--executor slurm` it renders and submits the next batch of what is not cached, or checks the one running, and exits. The answer is one JSON object: `running` (with a message), `done` (the final Items, each asset a local file, a store zipped into `{cache}/work/deliver-<job>/`, and their manifests) or `failed`. The content-addressed cache makes each call go on from where the last stopped.
- **The profile** of `--executor slurm` is the site's current one in `{home}/cluster/profiles/`, made from a snapshot only when there is none; `ponzi-worker profile --site ceoas` with no `--snapshot` takes a new snapshot and makes it again (`ponzi_spec.cluster.create`, `--home`).
- **Removed:** `ponzi-worker serve`, `ponzi_worker.loop` and `executors.slurm.SlurmRunner`.

## Do results change?

No. The same stages run against the same cache; the same Items and manifests are delivered.

## Tests

ponzi-worker `test_loop.py`, `test_watched.py`, `test_standard.py` and `test_slurm.py` run the client's loop with the worker called in this process (`tests/serving.py`, `ponzi_worker.job.in_process`), including the SLURM route against a fake `sbatch`. New: the loop runs the real `ponzi-worker job -` as a subprocess, a run and a failure through it, and a worker with no answer fails the job.

## Version

- ponzi-client: minor (`serve`).
- ponzi-worker: minor (`serve` removed, `job` added; unreleased at 0.1.0).
- `ponzi-spec`: minor (`create --home`, `--snapshot` optional).
