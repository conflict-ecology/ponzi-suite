# CR-062: no approval gate on SLURM batches

- **Requested by / date:** owner, 2026-11-05 ("remove that approval block. The client should be the one responsible for interacting with a server. The worker is simply there to invoke the core commands in a slurm job to do whatever tasks is requested via the server - client chain.")
- **Status:** implemented on the owner's instruction (2026-11-05)

## Why

Every SLURM batch stopped at `awaiting_approval` until the owner ran `ponzi-worker approve` on the login node, including each of a watched area's several daily batches. The work is already asked for, and authorised, through the client and the server (a request, or a watched area); the worker only carries it out.

## What changes

- **ponzi-spec:** the job status `awaiting_approval` is removed (`JobStatus`, `Heartbeat.status`). `Profile.approval` and the site file's `approval` are removed; the shipped `ceoas` profile is made again from its snapshot and loses only that line.
- **ponzi-worker:**
  - A rendered batch has the status `rendered`; `submit` (formerly `approve`, without the confirmation) submits it.
  - `serve --executor slurm` submits each batch as it is rendered and follows it; the job is `running` meanwhile.
  - `run --executor slurm` submits too; `--dry-run` renders and shows the batch without submitting. `--sbatch CMD` names the submit command.
  - The command `ponzi-worker approve` is removed.
- **ponzi-server:** a held job is `leased` or `running`. `openapi.json` is regenerated, and ponzi-visual's types with it.

## Do results change?

No. The same scripts are rendered and submitted; only the wait before submission is gone.

## Tests

ponzi-worker `test_slurm.py`: rendering submits nothing; a submitted batch equals the direct calls and is never submitted twice; the loop claims, submits and completes a job with no `awaiting_approval`.

## Version

- `ponzi-spec`: minor (a status value leaves the REST models; no stored data or content id changes).
- ponzi-worker, ponzi-server: minor.

This changes the system, not the rules for agents: an agent still submits cluster work only through a server in client mode, or with the owner's approval.
