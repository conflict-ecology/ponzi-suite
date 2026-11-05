# Running on the cluster (SLURM)

The worker renders SLURM job scripts from a **cluster profile**: versioned data, made on the cluster by ponzi-core's `ponzi_spec.cluster` from the cluster's site file. No cluster's profile is shipped (CR-065). A profile holds the partitions, the Python of each environment of a ponzi-service release, the scratch redirects, and the resources of each stage.

Work is asked for through the server, by a request or a watched area made with ponzi-client (or ponzi-visual). `ponzi-client serve` claims it; that loop is the only long-running process, on the login node or wherever the server can be reached. For each job it calls `ponzi-worker job`, a short command that renders the job's next batch and submits it, or checks the batch already running, and exits. The SLURM tasks invoke the core commands; when the last is done the client delivers the outputs (CR-062, CR-063).

```
ponzi-client serve --worker-id login -- --executor slurm   # the loop: claims jobs, calls ponzi-worker job
ponzi-worker run WORKFLOW.yaml --executor slurm --each burst=t028_058198_iw3,t028_058199_iw3   # one workflow, no server
ponzi-worker run WORKFLOW.yaml --executor slurm ... --dry-run --print-scripts   # render and show; submit nothing
# (on a machine without SLURM, add --profile FILE to render with a profile made on the cluster)
ponzi-worker batch BATCH            # how far it got: job records in the cache, failures from sacct
```

## Where the client loop runs

`ponzi-client serve` is the only long-running process. It needs little: it polls the server, heartbeats, calls `ponzi-worker job` for a few seconds at a time, and delivers the outputs. It can run on the login node, or as a small SLURM job of its own.

### As a SLURM job

```
#!/bin/bash
#SBATCH --job-name=ponzi-client
#SBATCH --partition=<partition> --account=<account>
#SBATCH --cpus-per-task=1 --mem=2G
#SBATCH --time=<the longest your partition allows>
export PONZI_KEY_FILE=~/ponzi-worker.key          # a worker key (Authentication)
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
- **Submitting from a job:** with `--executor slurm`, the loop's `ponzi-worker job` calls run `sbatch` and `sacct` from inside the loop's job. Try `sbatch --test-only <any script>` from an interactive job.
- **The time limit:** the partition's `MaxTime` and your QOS's `MaxWall` (`scontrol show partition`, `sacctmgr show qos`) bound how long the job lives. A snapshot of the cluster records both (`partitions.txt`, `qos.psv`).
- **The shared file system:** the worker's home (`roots.data` of the cluster's `ponzi.yaml`) must be on storage the compute nodes share, so the loop's job and the SLURM tasks see one cache.

Restarting is safe. When the loop's job ends (its time limit, a node failure, maintenance), the job it held returns to the server's queue once its lease expires; a restarted loop claims it again, finds every finished output in the cache, and does not submit a batch twice. To restart it automatically, use `scrontab` where the cluster enables it, or a cron entry on the login node that submits the job again when `squeue` no longer shows it.

One loop carries out one job at a time. More loops, each with its own `--worker-id`, carry out jobs side by side.

## Logs

Every log PONZI writes to files is in `$PONZI_HOME/logs/` (CR-064): each SLURM task's output in `logs/slurm/<batch>/<stage>_<job>_<task>.out`, the folder made when the batch is rendered, and the client loop's in `logs/client/`. `batch.json` in `$PONZI_HOME/cache/slurm/<batch>/` names its log folder, and `ponzi-worker batch` reads the failed tasks from `sacct`. On a cluster, `$PONZI_HOME` is the home of the cluster's `ponzi.yaml` (`roots.data`), so the logs sit on the shared file system with the cache.

## How a batch is made

- **Arrays.** Each step of the workflows becomes one array job, with one task per job that isn't cached. A job shared by several workflows, such as one calibration's ingest, is one task.
- **Dependencies.** Each array runs `afterok` the arrays it reads from.
- **Tasks.** Each task runs `python -m ponzi_worker.node` against the shared cache, under the job's lock. It writes the same records as the local executor.
- **Later steps.** A step known only once others ran waits for the next batch, which the worker renders and submits when the one before is done. That covers the per-pair coherence jobs after discovery, and anything after `tile`.

## The profile

A profile is made, not written by hand, from two inputs:

- **A snapshot of the cluster**: read-only SLURM queries of the partitions, the nodes with their cpus, memory, GPUs and state, your accounts, the limits, and your recent jobs.
- **A site file**, written once for the cluster at `$PONZI_HOME/cluster/sites/<site>.yaml` (or any file given to `--site`). It holds what a snapshot cannot say: the roots, the release, which partition plays each role (`cpu`, `scratch`, `gpu`, `bulk`), nodes to avoid, and each stage's request.

Every job checks for the profile first. `ponzi-worker job` and `run` with `--executor slurm` and no `--profile` read `$PONZI_HOME/cluster/profiles/<site>.yaml`; with none, they take the snapshot on the login node, make the profile from it and the site file, and save both in the home's `cluster/` folder (`ponzi_spec.home.Layout.cluster`). `--site` names the site; with one site file in `$PONZI_HOME/cluster/sites/`, it is that one, and with none the job fails saying where to write it. `ponzi-worker profile` takes a new snapshot and makes it again, after a node goes down or new stages have run. The home is `roots.data` of the cluster's `ponzi.yaml`, typically the shared scratch root; with no `roots.data` it is `$PONZI_HOME`, else `~/.ponzi` in your cluster home folder. The `roots` of the site file are where the SLURM jobs work and do not choose this folder:

```
$PONZI_HOME/cluster/
  sites/<site>.yaml                      the site file, written for the cluster
  profiles/<site>.yaml                   the current profile
  profiles/<site>-<version>.yaml         every version made
  snapshots/<site>/<YYYY-MM-DDTHHMMSS>/  the last 10 snapshots
```

Remaking the profile of an unchanged cluster keeps its version, so a batch already rendered keeps its id and is not submitted twice. A changed cluster, such as a node going down, gives a new version named by the day (`2026.11.05`, then `2026.11.05.2`). `--profile FILE` uses a given profile instead.

By hand, `ROOTS=... RELEASES=... bash snapshot.sh <site>` (in ponzi-core's `packages/spec/src/ponzi_spec/cluster/`) takes the same snapshot on the login node, and `ponzi-worker profile --snapshot DIR --site <site> --out FILE` makes the profile from it anywhere; `python -m ponzi_spec.cluster.create` does the same without the worker.

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

A root missing from the file systems, or a release not installed, becomes a warning in the file. The version is the snapshot's date.

The tests use a made-up cluster: `test_profile_create.py` makes profiles from a small synthetic snapshot and site file, and `test_slurm.py` renders and runs batches from a made-up profile with a fake `sbatch`. Nothing of a real cluster is in any repository.

The stages that never ran on the cluster keep the site's requests until a snapshot holds their jobs. Measuring them is on the [roadmap](../contributing/roadmap.md#phase-8-the-slurm-executor).

## The port reference (phase 0)

[ponzi-core `packages/pipeline/reference/phase0`](https://github.com/conflict-ecology/ponzi-core/tree/main/packages/pipeline/reference/phase0) holds repeat_ccd's own ISCE3 functions on one burst, with every intermediate kept. The check, `ponzi-pipeline port-check`, compares the port with it stage by stage on the bytes. Its README gives the three jobs and their resources.
