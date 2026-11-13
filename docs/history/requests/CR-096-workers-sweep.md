# CR-096: workers sweep: each one checks all the work in flight and submits all the new work

- **Requested by / date:** owner, 2026-11-13 ("the client should be able to start workers regularly. The workers will check up on the work being performed and return that information to the client which then goes to the server"; "Those workers should also be able to submit any new work to be done to the cluster even if a current batch of work is being performed by a previous worker"; "agents can be used in lieu of a worker and independent of a client but the subsequent worker can grab information that agent generated and send it off to the client - server"; "I want the workers to be able to saturate the cluster if necessary")
- **Status:** signed off (2026-11-13; the review's points 1 to 14 applied, decisions as recommended), implemented (unreleased), awaiting review; uncommitted
- **Builds on:** CR-095 (one batch per job), whose per-job record this replaces.

## Why
`ponzi-client serve` carries out one job at a time: it claims up to `--max-jobs` leases, then for each in turn calls `ponzi-worker job` every `--step-seconds` until it is done, and only then claims again. So:

- one loop has one SLURM batch on the cluster at a time, however many requests wait;
- a request that comes in while a job runs waits until that job is done, which can be hours;
- `--max-jobs` above 1 does harm: the leases not being worked on get no heartbeat, expire after `lease_seconds` (600), and return to the queue while this loop still holds them;
- every running job costs its own worker call and its own `sacct` call every `--step-seconds`;
- a refusal by `sbatch` for the account's submit limit (QOS or association `MaxSubmitJobs`) fails the job, though it only means "later";
- a batch that failed is never submitted again: a retry of the job plans the same tasks, gets the same batch id, finds that folder `submitted` and fails at once (CR-095 keeps this);
- work someone runs by hand on the cluster (`ponzi-worker run --executor slurm`) is unknown to the loop's calls: a job needing the same tasks submits them again, and waits on nothing.

The owner's design: the client starts a short-lived worker regularly; each worker looks at all the work in flight, submits whatever new work there is, even while earlier workers' batches run, and reports back; and an agent (a person, a script, an AI agent on the cluster) may run work itself, outside any client, which the next worker finds and reports.

## What changes

### Terms
- **Loop:** one `ponzi-client serve` process. The server knows it by its `--worker-id` (the field keeps its name).
- **Sweep:** one short call of the worker (`ponzi-worker sweep`), made by a loop every `--step-seconds`, over every job the loop holds. It plans, submits and checks; it computes nothing.
- **Task:** one job of the worker's plan (one stage on its inputs, named by its content id); one element of a SLURM array, run on a compute node by `python -m ponzi_worker.node`.
- **In flight:** a task in a live batch, whoever submitted it, that has neither finished (its record in the cache) nor failed.
- **Agent:** anything that runs PONZI work on the cluster without a loop: `ponzi-worker run` (local or slurm), by a person, a script or an AI agent.

### ponzi-worker: `sweep` (SLURM)
`ponzi-worker sweep -` reads `{"jobs": [Job, ...], "by": <submitter>, "timeout": <seconds>}` on stdin and answers `{"jobs": {<job id>: <answer>, ...}}` on stdout. It runs with `--executor slurm` only. One sweep, under the sweep lock:

1. **Look at what is in flight.** Every live batch is in `{cache}/slurm/live/` (one empty file per batch id). One `sacct` call covers all their arrays. A live batch closes (its file removed, `batch.json` `done` or `failed`) once each of its tasks has finished or failed; a batch cut short by a refusal is live, and its remaining arrays are submitted first.
2. **Plan each job.** For each job, its tasks are `cached`, `in flight` (in a live batch, of this loop, another loop or an agent), `failed` (its array task failed in a live batch, and no sweep has told of it yet), `waits` (known only once others ran), or `to run`. A failed task dooms the live tasks that read it, directly or not: they would run (`afterany`) and fail on the missing input, so the sweep gives them up with it (the batch's `reported` list), and a retry submits them all again, their old copies' failures never told.
3. **Submit the new work once.** The `to run` tasks of every job, shared tasks once, become one new batch: one array per step, as `prepare` makes for many workflows today. A step's array holds at most the cluster's limits (below); a larger step is split into several arrays. A task whose input is in flight depends (`afterany`) on that input's array, in whichever batch it is; a task whose input did not appear fails at once (`ponzi_worker.node`), so one failed task fails only the tasks that read it, never the rest of a shared array. Nothing in flight is submitted again.
4. **A submit limit is a wait.** When `sbatch` refuses an array for a submit limit (its message names `QOSMaxSubmitJob`, `AssocMaxSubmitJob`, `MaxSubmitJobs`, or "Job violates accounting/QOS policy"), the sweep halves that array and tries again, down to one task; what is refused at one task waits. The arrays submitted stay, the batch stays live, and the jobs needing the rest answer `running` ("waiting for room in SLURM: <reason>"); the next sweep goes on. Any other refusal fails the jobs whose tasks were in that array.
5. **Answer each job.**
   - `failed`: one of its tasks failed; the answer names the task, the batch and its submitter. The task is no longer in flight, so a retry of the job (the server requeues it while attempts remain) submits it again.
   - `running`: some tasks are in flight, waiting or held by a submit limit; the message says how many tasks are done, running and waiting in SLURM, and which batches carry the rest (by id and submitter).
   - `ready`: nothing missing. The sweep does not package the outputs; the client does that with `package` (below).

**The cluster's limits.** An array holds at most the profile's `MaxArraySize` and, when the cluster's snapshot records one, the account's `MaxSubmitJobs` (`qos.psv`, `assoc.psv`). The profile gains `max_submit` for it, made by `ponzi_spec.cluster.create` as the array throttle is. It sizes arrays; it is no ceiling on the work (decision 5).

**The sweep lock.** `{cache}/locks/slurm-sweep` (a directory, as every lock) holds a file naming its holder (host, process, time). A sweep that finds it held waits up to a minute, then answers every job `running` ("another sweep is submitting"). A lock older than the sweep's `timeout` (the client's `--sweep-timeout`, default 600 s) is stale: its holder has been killed, and the lock is taken over.

**Stdout carries the answer only.** While a sweep (or `job`, `package`) works, the worker points its stdout, Python's and the file descriptor its subprocesses inherit (`sbatch`, `sacct`, a stage run in process), at stderr; when it is done it writes the answer as one line of JSON to the real stdout and exits. The client still reads the last line, but nothing else can share it (a stage's progress line, a partial line without a newline). What a remote login prints (a `.bashrc` that echoes) comes before the worker starts and stays ahead of the answer.

A batch records `submitted_by`: the sweep's `by` (`loop:<worker id>`), or the agent's name for `run` and `batch` (`--by NAME`, default `$USER@<host>`).

**From before this change.** The first sweep registers as live every batch whose `batch.json` is `submitted` or `rendered` and not done, and removes CR-095's `{cache}/slurm/by-job/` records.

### ponzi-worker: `package`
`ponzi-worker package -` reads `{"jobs": [Job, ...]}` and answers, for each job with nothing missing, `done` with its final Items (each asset's href a local file: the cached file, or a store folder zipped into `{cache}/work/deliver-<job id>/`, as `job` packages today) and their manifests; a job with something missing answers `failed`. It may take minutes (a large store to zip), so the client runs it apart from the sweeps and without the sweep timeout.

### ponzi-worker: `job`, and the local executor
`ponzi-worker job -` stays: with `--executor slurm`, a sweep of one job followed by `package` when it is ready (for use by hand and by older clients); with `--executor local`, it runs the workflow here to the end and packages it, as today. A loop whose worker runs `--executor local` does not sweep: it calls `job` for each held job in turn, as today, without the sweep timeout.

### ponzi-worker: agents
- `ponzi-worker run --executor slurm` takes the sweep lock, leaves out tasks in flight (depending on them instead), registers its batch as live, splits arrays to the cluster's limits, and records `submitted_by`. So an agent never submits what a loop's sweep already has in flight, and the reverse. `ponzi-worker batch` only reports a batch, as before.
- `ponzi-worker run --executor local` runs as today: each task under its lock, its output in the cache.
- What an agent made is found by the next sweep: a finished task is `cached`, a task in the agent's batch is `in flight` and reported with the agent's name. Work an agent runs that no server job needs is in the cache, ready for a request that comes later; it is not reported to the server (no job holds it).

### ponzi-client: `serve` sweeps
- **Every `--step-seconds`** (counted from the end of one sweep to the start of the next, so sweeps of one loop never overlap): claim the queued jobs its worker can run (at most 100 a claim, the server's limit; with `--max-jobs N`, no more than N held), then run one sweep over every held job not being delivered, then act on each answer: `running` updates the job's heartbeat message; `ready` hands the job to delivery; `failed` fails it. A request that comes in while jobs run is claimed at the next sweep, and its new work is submitted in that sweep, beside every batch already running.
- **Delivery runs apart:** a delivery thread runs `package` for the ready jobs, then delivers their outputs and completes them (or fails them), while the sweeps go on. A job being delivered is not swept.
- **Heartbeats:** one thread heartbeats every held lease every `--heartbeat-seconds`, from the moment it is claimed, so no lease expires while it waits for a sweep or for delivery.
- **A sweep with no answer:** a worker only answers the client that ran it (a subprocess, here or through ssh: the input on stdin, one answer on stdout); it reaches nothing else. A sweep **answers** when the last line of its stdout is a JSON object of the sweep's answer; the jobs in it are answered, `failed` ones included (a failed task, a refused workflow), and those fail as any failed job does. Anything else is **no answer**, whatever the exit code:
  - the command cannot run: the loop's ssh connection is down and cannot be reopened without a prompt (CR-098), or ssh cannot connect at all (the network, the login node down, a host key; ssh exits 255);
  - the worker exits without an answer: a crash, a traceback, a broken environment;
  - the output is cut off or not the answer's shape: the process killed (the login node's OOM killer, an admin), the connection dropped during the call;
  - the call runs past `--sweep-timeout` (default 600 seconds; a sweep takes seconds): the client kills it.

  A held job left out of an answer counts as no answer for that job. A job with no answer is left as it was, not failed (until now a call with no answer failed the job), and swept again at the next tick; the client logs the command's exit code and the last lines of its stderr. After three sweeps in a row with no answer, the client stops heartbeating the jobs concerned, so their leases expire and they return to the queue for another loop, and while no sweep answers it claims nothing new. Their SLURM work goes on, and the next sweep that answers, of this loop or another, finds it in flight or in the cache.
- **`--once`:** one claim, then sweeps until every held job is done or failed.
- **Stop:** stop claiming, finish the current sweep and deliveries, and leave the leases of jobs still running to expire; their SLURM work goes on, and the next loop's sweep finds it in flight.
- **No ceiling by default:** a loop claims every queued job its worker can run, and every sweep submits all their new work, so the work can fill the cluster; SLURM's own limits (the account's QOS and association limits, each array's throttle from the profile) decide what runs, and the rest waits in SLURM's queue or, at the submit limit, in the sweep. `--max-jobs N` stays, unset by default, to cap the jobs one loop holds.

### Replaced
CR-095's per-job record (`{cache}/slurm/by-job/`) goes: a job's batches are the live batches holding its tasks. CR-095 is marked superseded in part.

### Docs
- Running on the cluster (`service/hpc.md`): the sweep and `package`; that the work fills the cluster, and what holds it back (each array's throttle, the account's limits, `--max-jobs` when set); that one loop with no `--max-jobs` claims the whole queue, so two clusters each want a `--max-jobs` or their own stages; that each sweep makes one `sacct` call, so a large run wants a longer `--step-seconds`; agents: what `run --executor slurm` and `batch` share with the sweeps, and `--by`.
- The worker: `sweep`, `package`, `job`.
- The clients: `serve` (claiming at each sweep, `--max-jobs`, `--sweep-timeout`, delivery apart, the heartbeat rule).
- The glossary: loop, sweep, task, in flight, agent, and the three things called "worker" (the `ponzi-worker` program, the `worker` key scope, the server's `worker_id`, which names a loop).

## Do results change?
No. The same tasks run against the same cache and give the same content ids; only when and in which batch they are submitted changes.

## Tests
With an `sbatch` that queues and runs nothing, a fake `sacct`, and the tasks run by the test as SLURM would (`ponzi_worker.node`):
- ponzi-worker:
  - two jobs sharing a task in one sweep: one batch, the shared task once;
  - a job swept while its batch runs, after some tasks finished: nothing submitted again (CR-095's case);
  - a new job arriving while an earlier batch runs: its new tasks are submitted in a new batch, its tasks already in flight are not, and its task reading an in-flight output depends (`afterany`) on that array;
  - one failed task in a shared array: the tasks reading it fail at once, the others of the next array run, only the jobs needing it fail, and a later sweep of such a job (a retry) submits the task again;
  - an agent's `run --executor slurm` batch: a sweep submits none of its tasks, reports them with the agent's name, and reports them ready once they run; and the reverse, `run` after a sweep;
  - a step larger than `max_submit` split into arrays that fit; a refusal for `QOSMaxSubmitJobPerUserLimit`: the array halved until it is taken, the rest answered `running` with the reason and submitted by the next sweep; another refusal fails the jobs of that array;
  - two sweeps at once: the second waits for the lock, and one batch is submitted; a lock older than `timeout` taken over;
  - stdout holds the answer alone: a stage and a fake `sbatch` that print to stdout (one without a newline) leave it on stderr, and the answer parses;
  - a batch closes when every task is finished or failed, and leaves `live/`;
  - batches and `by-job/` records from before the change are taken up by the first sweep;
  - `package` of a ready job and of one with something missing; `job` with `--executor slurm` and with `--executor local`.
- ponzi-spec: `max_submit` read from a snapshot's `qos.psv`/`assoc.psv`, absent when none is set.
- ponzi-client: with a fake sweep: with no `--max-jobs`, every queued job is claimed and swept in one call, and a job submitted meanwhile is claimed at the next sweep; `--max-jobs 2` holds two, and a third is claimed once one is done; every held lease heartbeats from its claim (a short `lease_seconds`, no expiry); a slow `package` does not hold up the sweeps; a sweep with no answer fails no job, for each kind (a fake ssh exiting 255, a worker exiting 1 with a traceback, output cut off, a sweep past `--sweep-timeout`, killed), and a held job left out of an answer is not failed; three in a row stop the heartbeats and the claims, and an answer starts them again; a local worker called per job; `--once`; stop.
- The loop tests (`test_loop.py`, `test_watched.py`, `test_standard.py`, `test_slurm.py`) pass, through the sweep.

## Decided at sign-off
1. **One sweep per loop tick, over every held job,** rather than a call per job: one `sacct`, one lock, one new batch per tick, and (CR-098) one worker process per tick on the loop's one ssh connection. Packaging is apart from the sweep.
2. **What is in flight is per task, whoever submitted it.** New work goes into a new batch even while others run; nothing in flight is submitted twice. Arrays depend `afterany`, and a task fails at once on a missing input.
3. **An agent is a run outside any loop** (`ponzi-worker run`), sharing the sweep lock and live batches; its work reaches the server only through a server job that needs it.
4. **A submit limit waits; a failed task fails the job,** and a retry submits it again. Arrays are split to the cluster's limits.
5. **No ceiling by default** (owner: "I want the workers to be able to saturate the cluster if necessary"): SLURM's limits decide; `--max-jobs` is an optional cap per loop.
6. **No answer is not a failure.** A sweep answers only with its JSON; no answer (the command fails, the worker crashes, the output is cut off, `--sweep-timeout`, default 600 s) leaves the jobs as they were; three in a row let their leases expire, and the loop claims nothing until a sweep answers.
7. **The sweep is SLURM's;** a local worker is called per job, as today.

## Version
- ponzi-worker: minor (`sweep`, `package`; `run` and `job` share the in-flight batches; `--by`; a task fails on a missing input).
- ponzi-client: minor (`serve` sweeps, delivers apart, and runs many jobs at once; `--sweep-timeout`).
- ponzi-spec: minor (the profile's `max_submit`).
- ponzi-suite: the docs above.
- Standard: no change.
