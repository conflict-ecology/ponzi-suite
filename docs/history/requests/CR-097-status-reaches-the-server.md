# CR-097: what the workers see reaches the server

- **Requested by / date:** owner, 2026-11-13 ("how do I keep track of what a worker is doing via agent or client?"; "add to the change a way for client to keep track of worker / slurm status"; "The workers will check up on the work being performed and return that information to the client which then goes to the server")
- **Status:** signed off (2026-11-13; the review's points 8 and 9 applied, decisions as recommended), implemented (unreleased), awaiting review; uncommitted
- **Builds on:** CR-096 (the sweep, which sees every batch in flight).

## Why
After CR-096 each sweep knows, for every job a client holds, which tasks are done, running, waiting in SLURM or failed, in which batches and submitted by whom, agents included. Little of it reaches anyone:

- a sweep's answer is a sentence per job (`message`);
- the server stores a job's `worker_id`, `progress` and `message` from claims and heartbeats, but the API returns none of them, nor the job's last `error`;
- the SLURM job id a heartbeat can carry (`scheduler_job`) is accepted and dropped;
- a client loop that holds no job leaves no trace: the server cannot say which loops exist or when one was last heard from;
- what a sweep sees beyond the held jobs (batches of other loops and of agents) goes nowhere.

A person or an agent following the work from anywhere, without `squeue` on the cluster, needs all of it from the server.

## What changes

### ponzi-worker: the sweep answers in fields
Each `running` answer gains, beside its `message`:
- `progress`: the job's tasks done over its tasks, 0 to 1;
- `scheduler_job`: the SLURM job ids of the arrays carrying its tasks, comma separated;
- `detail`: the batches carrying its tasks, each with its id, `submitted_by`, and per step the stage, the array's SLURM id and the job's tasks in it that are `done`, `running`, `pending` and `failed` (`running` and `pending` from `sacct`, `done` from the cache's records).

The sweep's answer gains `sweep`: what it saw of the whole cluster's PONZI work: every live batch, with its id, `submitted_by`, created and submitted times, and its tasks done, running, pending and failed; and any submit limit met.

### ponzi-client
- **Heartbeats carry the job's fields:** `progress`, `message`, `scheduler_job` and `detail`, sent with every heartbeat and at once when they change.
- **One heartbeat call for all held jobs:** with no ceiling (CR-096) a loop may hold hundreds of leases, so it heartbeats them together, `POST /v1/jobs/heartbeat` with a list (each job's id, lease and fields), at most 500 a call; the answer gives each lease's new expiry, or that it is no longer held (as a 409 does today). The one-job route stays.
- **Each sweep is reported:** after each sweep, `PUT /v1/workers/{worker_id}` with the loop's host, the stages its worker has, its `--max-jobs`, the jobs it holds, the sweep's `sweep` view, and, through ssh (CR-098), its `connection`: the worker host, `up` or `down`, when it was opened, how many times it was reopened, and the last error. A loop whose sweeps get no answer still reports, so its connection being down shows on the server.
- **New commands** (and the same calls on `Client`):
  - `ponzi-client job ID`: one job, with the new fields;
  - `ponzi-client jobs --worker ID`: the jobs a loop holds or last held;
  - `ponzi-client workers`: every loop the server has heard from, its last report, and when.

### The contract (`ponzi_spec.api`, C-API)
- `Job` gains, all optional: `worker_id` (who holds it, or last held it), `progress`, `message`, `scheduler_job`, `detail`, `heartbeat` (the time of the last heartbeat), `lease_expires`, and `error` (the last failure, already stored).
- `Heartbeat` gains `detail`.
- New `WorkerReport` (what a loop sends, `connection` optional) and `Worker` (what the server returns: the report, `first_seen`, `last_seen`).
- `detail` and `sweep` are at most 64 KB each; larger is refused (422).

Every new field is optional. But the API models forbid unknown fields, so a client older than its server refuses a job that carries the new ones (an operations key's view): clients and server are updated together. A loop hands its worker only the fields a worker reads (`JOB_WORK_FIELDS`), so a worker need not match its loop's version; null fields are left out of the server's answers.

### Who sees what
The new fields say where and how the work runs: cluster paths in errors, `$USER@<host>` in `submitted_by`, host names, SLURM ids. They are for the people running the service, not for everyone who may read jobs (`client:read`, which `user` keys hold). A new permission, `operations`, held by `user-admin`, `client:write`, `worker` and `admin` (implied, as `areas` is; no key's own scope), covers them:

- with `operations`: every field of a job, and `GET /v1/workers`;
- without it (`user`, `client:read`): a job's `status`, `progress`, `attempts`, `items`, as today plus `progress`; `message`, `scheduler_job`, `detail`, `worker_id`, `heartbeat`, `lease_expires` and `error` are left out (null), and `GET /v1/workers` is refused (403).

### ponzi-server
- The job row gains `scheduler_job`, `detail` and `heartbeat` (nullable columns, added at startup as other new columns are). A heartbeat stores all it carries. `worker_id` is no longer cleared when a lease expires or a failure is requeued: it says who held the job last until another loop claims it.
- A `workers` table, one row per `worker_id`: the last report, written by `PUT /v1/workers/{worker_id}` (`worker` scope; a key reports for any id), and `last_seen`, also moved by every claim and heartbeat.
- `GET /v1/jobs?worker=ID` (`client:read`; the filter needs `operations`) and `GET /v1/workers` (`operations`), the most recently heard from first. The server never decides that a loop is gone: it gives `last_seen`, and the reader judges.

### Docs
Running on the cluster: following the work (`workers`, `jobs --worker`, `job ID`; what `pending`, `running` and `submitted_by` say). The clients: the new commands. The REST API: the new routes and fields; `openapi.json` regenerated.

## Do results change?
No. Only what is recorded and shown about the work under way.

## Tests
- ponzi-worker: a sweep against a fake `sacct` with pending, running, completed and failed tasks across two batches, one an agent's: each job's `progress`, `scheduler_job` and `detail`, and the `sweep` view.
- ponzi-client: heartbeats for all held jobs in one call, carrying the fields, and sent at once when they change; a report after each sweep, answered or not, with the connection's state through a fake ssh; `job`, `jobs --worker`, `workers`.
- ponzi-server: a heartbeat's fields stored and returned by `GET /v1/jobs/{id}`, to a key with `operations` and not to a `user` key (the fields null, `/v1/workers` 403); `POST /v1/jobs/heartbeat` for many leases, one of them no longer held, and over 500 refused; `detail` and `sweep` over 64 KB refused; `worker_id` kept after an expired lease and a requeued failure and replaced by the next claim; `GET /v1/jobs?worker=`; `PUT` and `GET /v1/workers` with two loops; a database from before this change gains the columns and table at startup.
- ponzi-spec: the new and changed models; an old `Job` and `Heartbeat` still validate.

## Decided at sign-off
Each is written above as recommended; the owner confirms or changes it.
1. **Status travels the existing path:** worker answer → client → server (heartbeats, a report per sweep). The worker sends the server no status (CR-098 lets it send outputs, nothing else).
2. **A loop is known by its `worker_id`;** the server keeps no liveness rule and shows `last_seen`.
3. **Agents' batches reach the server in the sweep view** of whichever loop sees them, named by `submitted_by`; the server keeps no record of agents of its own.
4. **`worker_id` stays on a job** after its lease ends, as who held it last.
5. **ponzi-visual is not in this change;** a later request can show it.
6. **The operational fields need `operations`** (`user-admin`, `client:write`, `worker`, `admin`); people with `user` keys see a job's status and progress only.
7. **Heartbeats go in one call** per round for all held jobs.

## Version
- ponzi-spec: minor (optional fields on `Job` and `Heartbeat`; `WorkerReport`, `Worker`).
- ponzi-server: minor (`/v1/workers`, `?worker=`, `/v1/jobs/heartbeat`, the stored heartbeat fields, the `operations` permission).
- ponzi-client: minor (the reports; `job`, `jobs --worker`, `workers`).
- ponzi-worker: minor (the answer's fields and the `sweep` view).
- ponzi-suite: the docs above.
- Standard: no change.
