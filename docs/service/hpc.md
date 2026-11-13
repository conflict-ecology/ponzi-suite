# Running on SLURM

The worker renders SLURM job scripts from a **cluster profile**: versioned data, made on the cluster by ponzi-core's `ponzi_spec.cluster` from the cluster's site file. No cluster's profile is shipped (CR-065). A profile holds the partitions, the Python of each environment of a ponzi-service release, the scratch redirects, and the resources of each stage.

Work is asked for through the server, by a request or a watched area made with ponzi-client (or ponzi-visual). `ponzi-client serve` claims it; that loop is the only long-running process, on the login node or wherever the server can be reached. Every `--step-seconds` it **sweeps** (CR-096): it claims the queued jobs, then runs one `ponzi-worker sweep`, a short command over every job it holds, which checks the work in flight with one `sacct` call, submits all the new work as one batch beside the batches already running, answers each job, and exits. The SLURM tasks invoke the core commands; once a job has nothing missing, the loop runs `ponzi-worker package` for it and delivers the outputs, while the sweeps go on (CR-062, CR-063).

```
# the loop: claims jobs, sweeps them
ponzi-client serve --worker-id login -- --executor slurm
# one workflow, no server
ponzi-worker run WORKFLOW.yaml --executor slurm \
    --each burst=t028_058198_iw3,t028_058199_iw3
# render and show; submit nothing
ponzi-worker run WORKFLOW.yaml --executor slurm ... --dry-run --print-scripts
# (on a machine without SLURM, add --profile FILE to render with a
# profile made on the cluster)
# how far it got: job records in the cache, failures from sacct
ponzi-worker batch BATCH
```

## Sweeps

A sweep plans and submits; it computes nothing, and takes seconds.

- **What is in flight** is per task, whoever submitted it: a loop's sweep, another loop's, or an agent's `ponzi-worker run`. A task in a live batch (`$PONZI_HOME/cache/slurm/live/`) is never submitted again; a new task that reads it waits on its array (`afterany`). New work goes out in a new batch even while others run, so new requests start at once.
- **Filling the cluster.** A loop claims every queued job its worker can run, and each sweep submits all their new work: what runs is decided by SLURM, by the account's limits (QOS and association) and each array's throttle from the profile. `--max-jobs N` caps the jobs one loop holds. One loop without it claims the whole queue: with two clusters, give each a `--max-jobs`, or its own stages. Each sweep makes one `sacct` call; a large run wants a longer `--step-seconds`.
- **Arrays fit the cluster.** A step with more tasks than the profile's `max_array` (`MaxArraySize - 1`) or `max_submit` (the account's `MaxSubmitJobs`, from the snapshot) is split into several arrays.
- **The submit limit waits.** An array `sbatch` refuses for the submit limit is halved until it is taken; the rest waits, and the next sweep goes on (the job's message says "waiting for room in SLURM"). Any other refusal fails the jobs of that array.
- **A failed task** fails the jobs that need it, once, naming the task, its batch and who submitted it. The tasks that read it are given up with it, so a retry of the job (the server requeues it while attempts remain) submits them all again.
- **No answer is not a failure.** A sweep answers with one line of JSON on stdout (everything else it or its commands print goes to stderr). When it gives none (it crashes, its output is cut off, it runs past `--sweep-timeout`, default 600 s), the jobs are left as they were and swept again; after three sweeps in a row with no answer for a job, the loop stops heartbeating it, so its lease expires and the job returns to the queue, and while no sweep answers the loop claims nothing.
- **One sweep at a time.** Sweeps and `run --executor slurm` share a lock (`$PONZI_HOME/cache/locks/slurm-sweep`); a lock older than the sweep's timeout is taken over.
- **A local worker** (`-- --executor local`) is not swept: the loop calls `ponzi-worker job` for each job in turn.

### Following the work

From anywhere the server is reached, without `squeue` beside the worker (CR-097):

```
ponzi-client workers                 # the loops, when each was last heard from, what its last sweep saw
ponzi-client jobs --worker <name>    # the jobs a loop holds, or last held
ponzi-client job <job id>            # one job: message, progress, SLURM ids, per array its tasks' states
```

A job's `running` and `pending` counts come from `sacct` (running, or waiting in SLURM's queue); `done` from the cache's records. `submitted_by` names who submitted a batch: `loop:<worker id>`, or an agent's `--by`. What is shown is as fresh as the last sweep: up to one `--step-seconds` and one sweep old. The server keeps no rule for when a loop is gone; `last_seen` says when it was last heard from.

### Agents

An agent is anything that runs PONZI work on the cluster without a loop: a person, a script, an AI agent. `ponzi-worker run --executor slurm` shares what is in flight with the sweeps: it takes their lock, leaves out the tasks a live batch carries, lists its batch as live and records who submitted it (`--by NAME`, default `<user>@<host>`). The next sweep finds what the agent made: its finished tasks in the cache, its running ones in flight, reported with the agent's name. Work no server job needs stays in the cache for a request that comes later.

## Storage tiers

On a cluster with fast and large storage, put the home on three tiers (CR-099; [Tiers](../getting-started/paths.md#tiers-hot-warm-and-cold)): `$PONZI_HOME` (the home, and the hot tier: the cache and scratch, on the fast NAS), `$PONZI_HOME_WARM` (outputs, models, panels) and `$PONZI_HOME_COLD` (the downloads). Set them where the loop runs its worker; the rendered SLURM scripts export them to the tasks. The cache's entries are made on hot and found in any tier; inputs are read where they are, on cold, unless promoted: before a heavy run, `ponzi-worker promote 'downloads/slc/*_202609*'` stages a month of SLC to hot, and `evict --promoted downloads/slc` drops the copies after. `evict --to cold` keeps the hot cache small without computing anything again. `ponzi-worker profile` warns when a tier is on no mounted file system, or two tiers on one.

## From another machine

The loop can run anywhere the server is reached, a laptop or a VM, and run its worker on the cluster's login node (CR-098):

```
ponzi-client serve --worker-id laptop --worker-host hpc \
    --worker "env PONZI_HOME=/path/to/home /path/to/env/bin/ponzi-worker" \
    -- --executor slurm --site <site>
```

- **One connection.** `serve` opens one ssh connection to the host at start and runs every worker call over it as a new session (OpenSSH connection sharing; `~/.ssh/config` gives the user, key and any jump host). A password or two-factor prompt is answered once, at the terminal that started it; `--ssh-prompt never` opens it without one, for an unattended start, and `serve` exits at once if it cannot. Keepalives hold it through the login node's idle timeout. A connection found closed is reopened without a prompt, once per sweep; when that needs a prompt, the sweeps give no answer, their jobs' leases expire, and the log says to restart `serve` at a terminal.
- **The worker command** is the one on the host. A non-interactive ssh session reads no login profile: give the full path and `PONZI_HOME`, as above. The arguments after `--` reach the worker as given, spaces and quotes included.
- **Outputs.** In `upload` mode the worker sends each output to the server with a one-time ticket the loop asks for: the login node must reach the server's URL (a public address; a server on a VPN the cluster is not on cannot be reached). A file the worker cannot get there is fetched from it and sent by the loop instead, and `--deliver through-client` does that for every file. In `path` mode the worker writes the outputs under the server's home: the cluster must share it.
- **The loop never touches the worker's files.** It reaches them through the worker: `ponzi-worker fetch` (only files under the cache), `upload` and `clean`. A worker here is reached the same way.
- **Sleep and loss.** A laptop that sleeps, or loses its network, stops heartbeating: its leases expire and the jobs return to the queue, where the next sweep (of this loop, once back, or another) finds their work in flight or in the cache. For a loop that must not stop, the login node or a VM remains the place.

## Where the client loop runs

The loop needs little: it polls the server, heartbeats, sweeps for a few seconds at a time, and delivers the outputs. It can run on the login node, or as a small SLURM job of its own.

### As a SLURM job

```
#!/bin/bash
#SBATCH --job-name=ponzi-client
#SBATCH --partition=<partition> --account=<account>
#SBATCH --cpus-per-task=1 --mem=2G
#SBATCH --time=<the longest your partition allows>
# the home, on storage the compute nodes share
export PONZI_HOME=/shared/scratch/ponzi
# a worker key (Authentication)
export PONZI_KEY_FILE=~/ponzi-worker.key
ponzi-client serve --worker-id <name> -- --executor slurm --site <site>
```

Submit it with its log in the home, beside the tasks' logs (`#SBATCH` lines do not expand variables, so the folder is given on the command line):

```
mkdir -p "$PONZI_HOME/logs/client"
sbatch --output="$PONZI_HOME/logs/client/%x_%j.out" client.sbatch
```

On the login node instead, send its output to the same folder: `ponzi-client serve ... >> "$PONZI_HOME/logs/client/serve.log" 2>&1`.

Before relying on it, check on your cluster:

- **The network:** a compute node must reach the server's URL. Many clusters allow outbound connections from the login node only. Try it from a short interactive job, for example `curl -sI <server url>/v1/standards`.
- **Submitting from a job:** with `--executor slurm`, the loop's sweeps run `sbatch` and `sacct` from inside the loop's job. Try `sbatch --test-only <any script>` from an interactive job.
- **The time limit:** the partition's `MaxTime` and your QOS's `MaxWall` (`scontrol show partition`, `sacctmgr show qos`) bound how long the job lives. A snapshot of the cluster records both (`partitions.txt`, `qos.psv`).
- **The shared file system:** the home, `$PONZI_HOME`, must be on storage the compute nodes share, so the loop's job and the SLURM tasks see one cache. Each task's script exports the worker's `PONZI_HOME`, so a task finds the home whatever its own environment (CR-088).

Restarting is safe. When the loop's job ends (its time limit, a node failure, maintenance), the job it held returns to the server's queue once its lease expires; a restarted loop claims it again, finds every finished output in the cache, and does not submit a batch twice. To restart it automatically, use `scrontab` where the cluster enables it, or a cron entry on the login node that submits the job again when `squeue` no longer shows it.

One loop carries out one job at a time. More loops, each with its own `--worker-id`, carry out jobs side by side.

## Logs

Every log PONZI writes to files is in `$PONZI_HOME/logs/` (CR-064): each SLURM task's output in `logs/slurm/<batch>/<stage>_<job>_<task>.out`, the folder made when the batch is rendered, and the client loop's in `logs/client/`. `batch.json` in `$PONZI_HOME/cache/slurm/<batch>/` names its log folder, and `ponzi-worker batch` reads the failed tasks from `sacct`.

## How a batch is made

- **Arrays.** Each step of the workflows becomes one array job, with one task per job that isn't cached. A job shared by several workflows, such as one calibration's ingest, is one task.
- **Dependencies.** Each array runs `afterok` the arrays it reads from.
- **Tasks.** Each task runs `python -m ponzi_worker.node` against the shared cache, under the job's lock. It writes the same records as the local executor.
- **Later steps.** A step known only once others ran waits for the next batch, which the worker renders and submits when the one before is done. That covers the per-pair coherence jobs after discovery, and anything after `tile`.

## The profile

A profile is made, not written by hand, from two inputs:

- **A snapshot of the cluster**: read-only SLURM queries of the partitions, the nodes with their cpus, memory, GPUs and state, your accounts, the limits, and your recent jobs.
- **A site file**, written once for the cluster at `$PONZI_HOME/cluster/sites/<site>.yaml` (or any file given to `--site`). It holds what a snapshot cannot say: the roots other than the home (`lab`, where the releases are installed), the release, which partition plays each role (`cpu`, `scratch`, `gpu`, `bulk`), nodes to avoid, and each stage's request.

Every job checks for the profile first. `ponzi-worker job` and `run` with `--executor slurm` and no `--profile` read `$PONZI_HOME/cluster/profiles/<site>.yaml`; with none, they take the snapshot on the login node, make the profile from it and the site file, and save both in the home's `cluster/` folder (`ponzi_spec.home.Layout.cluster`). `--site` names the site; with one site file in `$PONZI_HOME/cluster/sites/`, it is that one, and with none the job fails saying where to write it. `ponzi-worker profile` takes a new snapshot and makes it again, after a node goes down or new stages have run. A site file names no `data` root (refused): `{data}` in its templates, such as a redirect `TMPDIR: "{data}/tmp/slurm"`, is the home (CR-088). The `cluster/` folder keeps the current profile, every version made and the last 10 snapshots ([Folders and environment variables](../getting-started/paths.md#the-ponzi-home)).

Remaking the profile of an unchanged cluster keeps its version, so a batch already rendered keeps its id and is not submitted twice. A changed cluster, such as a node going down, gives a new version named by the day (`2026.11.05`, then `2026.11.05.2`). `--profile FILE` uses a given profile instead.

By hand, `ROOTS=... RELEASES=... bash snapshot.sh <site>` (in ponzi-core's `packages/spec/src/ponzi_spec/cluster/`) takes the same snapshot on the login node, and `ponzi-worker profile --snapshot DIR --site <site> --out FILE` makes the profile from it anywhere; `python -m ponzi_spec.cluster.create` does the same without the worker.

A snapshot is one folder of files, each the output of a read-only command:

| File | Command | Gives the profile |
| --- | --- | --- |
| `partitions.txt`, `partitions_summary.txt` | `scontrol show partition`, `sinfo -s` | partitions, allowed accounts, state |
| `nodes.psv`, `nodes_full.txt` | `sinfo -N -o "%N\|%P\|%c\|%m\|%G\|%f\|%T"`, `scontrol show node` | nodes out of service (excluded), GPUs, the note of each role, the fit check |
| `assoc.psv`, `qos.psv` | `sacctmgr show assoc`, `sacctmgr show qos` | the user's accounts and limits |
| `config.txt` | `scontrol show config` (limits only) | the array throttle, within `MaxArraySize` |
| `sacct.psv` | `sacct` of the last 60 days | memory and walltime of the stages that ran as `ponzi-<stage>` jobs |
| `storage.txt`, `releases.txt` | `df -h` of the home and the roots, a listing of the release folder | warnings for a missing root or release |

`sacct.psv` lists past job names, nodes and accounts: it stays in the home, never in a repository.

From the snapshot, the profile takes:

- the nodes to exclude: the site's, plus every node that is down, drained or in maintenance;
- the GPU request, checked against the GPUs of the partition's nodes;
- a note per role on its nodes, cpus, memory and GPUs;
- the array throttle, within `MaxArraySize`;
- the memory and walltime of each stage that already ran as `ponzi-<stage>` jobs, from their largest MaxRSS and Elapsed with 50% headroom.

It refuses a profile that cannot run:

- a missing or down partition;
- an account the partition does not allow;
- a GPU request no node meets;
- a stage that fits on no usable node.

A root missing from the file systems, or a release not installed, becomes a warning in the file.

The tests use a made-up cluster: `test_profile_create.py` makes profiles from a small synthetic snapshot and site file, and `test_slurm.py` renders and runs batches from a made-up profile with a fake `sbatch`. Nothing of a real cluster is in any repository.

The stages that never ran on the cluster keep the site's requests until a snapshot holds their jobs. Measuring them is on the [roadmap](../contributing/roadmap.md#phase-8-the-slurm-executor).
