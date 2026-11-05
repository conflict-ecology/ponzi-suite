# Running on the cluster (SLURM)

The worker renders SLURM job scripts from a **cluster profile**: versioned data, made by ponzi-core's `ponzi_spec.cluster` (shipped: `ponzi_spec/cluster/profiles/ceoas.yaml`). A profile holds the partitions, the Python of each environment of a ponzi-service release, the scratch redirects, and the resources of each stage.

Work is asked for through the server, by a request or a watched area made with ponzi-client (or ponzi-visual). `ponzi-client serve` claims it; that loop is the only long-running process, on the login node or wherever the server can be reached. For each job it calls `ponzi-worker job`, a short command that renders the job's next batch and submits it, or checks the batch already running, and exits. The SLURM tasks invoke the core commands; when the last is done the client delivers the outputs (CR-062, CR-063).

```
ponzi-client serve --worker-id login -- --executor slurm --site ceoas   # the loop: claims jobs, calls ponzi-worker job
ponzi-worker run WORKFLOW.yaml --executor slurm --each burst=t028_058198_iw3,t028_058199_iw3   # one workflow, no server
ponzi-worker run WORKFLOW.yaml --executor slurm ... --dry-run --print-scripts   # render and show; submit nothing
# (on a machine without SLURM, add --profile ceoas to render with the shipped profile)
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
#SBATCH --output=%x_%j.out
export PONZI_KEY_FILE=~/ponzi-worker.key          # a worker key (Authentication)
ponzi-client serve --worker-id <name> -- --executor slurm --site <site>
```

Before relying on it, check on your cluster:

- **The network:** a compute node must reach the server's URL. Many clusters allow outbound connections from the login node only. Try it from a short interactive job, for example `curl -sI <server url>/v1/standards`.
- **Submitting from a job:** with `--executor slurm`, the loop's `ponzi-worker job` calls run `sbatch` and `sacct` from inside the loop's job. Try `sbatch --test-only <any script>` from an interactive job.
- **The time limit:** the partition's `MaxTime` and your QOS's `MaxWall` (`scontrol show partition`, `sacctmgr show qos`) bound how long the job lives. A snapshot of the cluster records both (`partitions.txt`, `qos.psv`).
- **The shared file system:** the worker's home (`roots.data` of the cluster's `ponzi.yaml`) must be on storage the compute nodes share, so the loop's job and the SLURM tasks see one cache.

Restarting is safe. When the loop's job ends (its time limit, a node failure, maintenance), the job it held returns to the server's queue once its lease expires; a restarted loop claims it again, finds every finished output in the cache, and does not submit a batch twice. To restart it automatically, use `scrontab` where the cluster enables it, or a cron entry on the login node that submits the job again when `squeue` no longer shows it.

One loop carries out one job at a time. More loops, each with its own `--worker-id`, carry out jobs side by side.

## How a batch is made

- **Arrays.** Each step of the workflows becomes one array job, with one task per job that isn't cached. A job shared by several workflows, such as one calibration's ingest, is one task.
- **Dependencies.** Each array runs `afterok` the arrays it reads from.
- **Tasks.** Each task runs `python -m ponzi_worker.node` against the shared cache, under the job's lock. It writes the same records as the local executor.
- **Later steps.** A step known only once others ran waits for the next batch, which the worker renders and submits when the one before is done. That covers the per-pair coherence jobs after discovery, and anything after `tile`.

## The profile

A profile is made, not written by hand, from two inputs:

- **A snapshot of the cluster**: read-only SLURM queries of the partitions, the nodes with their cpus, memory, GPUs and state, your accounts, the limits, and your recent jobs.
- **A site file**, shipped in ponzi-spec as `ponzi_spec/cluster/sites/<site>.yaml`, or any file given to `--site`. It holds what a snapshot cannot say: the roots, the release, which partition plays each role (`cpu`, `scratch`, `gpu`, `bulk`), nodes to avoid, and each stage's request.

The worker uses the site's current profile and makes one when there is none. `ponzi-worker job` and `run` with `--executor slurm` and no `--profile` read `{home}/cluster/profiles/<site>.yaml` (`--site`, default `ceoas`); with none, they take the snapshot on the login node, make the profile, and save both in the home's `cluster/` folder (`ponzi_spec.home.Layout.cluster`). `ponzi-worker profile --site ceoas` takes a new snapshot and makes it again, after a node goes down or new stages have run. The home is `roots.data` of the cluster's `ponzi.yaml`, typically the shared scratch root; with no `roots.data` it is `$PONZI_HOME`, else `~/.ponzi` in your cluster home folder. The `roots` of the site file are where the SLURM jobs work and do not choose this folder:

```
{home}/cluster/
  profiles/ceoas.yaml                    the current profile
  profiles/ceoas-<version>.yaml          every version made
  snapshots/ceoas/<YYYY-MM-DDTHHMMSS>/   the last 10 snapshots
```

Remaking the profile of an unchanged cluster keeps its version, so a batch already rendered keeps its id and is not submitted twice. A changed cluster, such as a node going down, gives a new version named by the day (`2026.11.05`, then `2026.11.05.2`). `--profile NAME|FILE` uses a given profile instead.

By hand, `bash snapshot.sh ceoas` (in ponzi-core's `packages/spec/src/ponzi_spec/cluster/`) takes the same snapshot on the login node, and `ponzi-worker profile --snapshot DIR --site ceoas --out FILE` makes the profile from it anywhere; `python -m ponzi_spec.cluster.create` does the same without the worker.

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

The shipped `ceoas` profile, which machines without SLURM and the tests render with, is made this way from the snapshot of 2026-10-27, and `test_profile_create.py` checks that it is exactly what the command makes. Its site file follows the job files of the system before the overhaul (ponzi-models `hpc/*.sbatch` and repeat_ccd's array scripts). `test_slurm.py` checks that the rendered scripts match those references: partition, account, excluded nodes (plus those down in the snapshot), GPUs, cpus, memory, walltime, throttle, roots, environment, exports and log folder.

The stages that never ran on the cluster keep the site's requests until a snapshot holds their jobs. Measuring them is on the [roadmap](../contributing/roadmap.md#phase-8-the-slurm-executor).

## The port reference (phase 0)

[ponzi-core `packages/pipeline/reference/phase0`](https://github.com/conflict-ecology/ponzi-core/tree/main/packages/pipeline/reference/phase0) holds repeat_ccd's own ISCE3 functions on one burst, with every intermediate kept. The check, `ponzi-pipeline port-check`, compares the port with it stage by stage on the bytes. Its README gives the three jobs and their resources.
