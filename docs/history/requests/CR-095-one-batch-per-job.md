# CR-095: a job's running SLURM batch is never submitted again

- **Requested by / date:** owner, 2026-11-13 ("fix it first": before the client changes, CR-096 to CR-098)
- **Status:** implemented on the owner's instruction (2026-11-13), awaiting review; uncommitted
- **Superseded in part:** the per-job record `{cache}/slurm/by-job/`, by CR-096's live batches (what is in flight is per task)

## Why
`ponzi-worker job --executor slurm` finds a job's batch by planning again: `prepare` names a batch by the content id of the jobs still to run and the profile, and a batch folder already submitted under that id is checked instead of submitted. That id holds only while nothing has finished. Once a task of the batch writes its output, the next call (every `--step-seconds`, 60 by default) plans fewer jobs, gets another id, finds no batch under it, and renders and submits a new batch holding every job not yet finished, including those still queued or running in the first batch. Each later call that sees progress does it again.

The job locks keep two tasks from computing one output, but every duplicate task takes a SLURM allocation, one whose job runs elsewhere sits on its node waiting for the lock, and the answer reports on the newest batch only, so a task that failed in an earlier one is never seen.

The test of the SLURM route through the loop missed it: its fake `sbatch` runs each script to the end inside the submit, so no call ever met a batch partly done. A test that runs one array's tasks between two calls shows the second call rendering a new batch.

## What changes
- **`ponzi_worker.job`:** a job's current batch is recorded in `{cache}/slurm/by-job/<job id>` (the batch id), written when the batch is rendered. A call with `--executor slurm` first looks there:
  - the batch is rendered but not all submitted (sbatch refused a step): it submits the rest, as `submit` does today (`running`);
  - submitted and not done: it checks that batch (`running`, or `failed` with the failed tasks), and plans nothing;
  - failed: the record is removed and the job fails, as today;
  - done, or no record: it plans as today; a new batch becomes the job's record; nothing left to submit removes the record and the job goes on to delivery (`done`).
- `ponzi-worker run --executor slurm` and `ponzi-worker batch` are unchanged: a person runs those by hand and submits once.

## Do results change?
No. The same tasks run against the same cache; only duplicate submissions stop.

## Tests
ponzi-worker `test_slurm.py`: with an `sbatch` that queues and runs nothing, a first call submits the batch; one array's tasks run (as SLURM would); a second call submits nothing and reports on the same batch; once every task has run, the next call answers `done`, still without submitting. A batch whose tasks `sacct` reports failed fails the job and removes its record.

## Version
ponzi-worker: patch.
