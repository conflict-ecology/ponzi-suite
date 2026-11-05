# Running on the cluster (SLURM)

The worker renders SLURM job scripts from a **cluster profile**: versioned data, `ponzi_worker/profiles/ceoas.yaml`. A profile holds the partitions, the Python of each environment of a ponzi-service release, the scratch redirects, and the resources of each stage. Nothing is submitted without approval.

```
ponzi-worker run WORKFLOW.yaml --executor slurm --each burst=t028_058198_iw3,t028_058199_iw3 --print-scripts
# (on the laptop, which has no SLURM, add --profile ceoas to render with the shipped profile)
ponzi-worker approve BATCH          # the arrays, tasks, resources, cpu-hours and walltime; then asks
ponzi-worker batch BATCH            # how far it got: job records in the cache, failures from sacct
ponzi-worker serve --worker-id login --executor slurm   # jobs from the server; each batch waits for approval
```

## How a batch is made

- **Arrays.** Each step of the workflows becomes one array job, with one task per job that isn't cached. A job shared by several workflows, such as one calibration's ingest, is one task.
- **Dependencies.** Each array runs `afterok` the arrays it reads from.
- **Tasks.** Each task runs `python -m ponzi_worker.node` against the shared cache, under the job's lock. It writes the same records as the local executor.
- **Later steps.** A step known only once others ran waits for the next batch, which needs its own approval. That covers the per-pair coherence jobs after discovery, and anything after `tile`.

## The profile

A profile is made, not written by hand, from two inputs:

- **A snapshot of the cluster**: read-only SLURM queries of the partitions, the nodes with their cpus, memory, GPUs and state, your accounts, the limits, and your recent jobs.
- **A site file**, shipped in the worker as `profiles/sites/<site>.yaml`. It holds what a snapshot cannot say: the roots, the release, which partition plays each role (`cpu`, `scratch`, `gpu`, `bulk`), nodes to avoid, and each stage's request.

The worker makes its profile when it starts. `serve` and `run` with `--executor slurm` and no `--profile` take the snapshot on the login node, make the profile of `--site` (default `ceoas`), and save both under `~/.config/ponzi-service/` (`$XDG_CONFIG_HOME/ponzi-service/` when that is set):

```
~/.config/ponzi-service/
  profiles/ceoas.yaml                    the current profile
  profiles/ceoas-<version>.yaml          every version made
  snapshots/ceoas/<YYYY-MM-DDTHHMMSS>/   the last 10 snapshots
```

A restart on an unchanged cluster keeps the current version, so batches waiting for approval keep their ids. A changed cluster, such as a node going down, gives a new version named by the day (`2026.11.05`, then `2026.11.05.2`). `--profile NAME|FILE` uses a given profile instead.

By hand, `bash snapshot.sh ceoas` (in ponzi-service's `packages/worker/reference/clusters/`) takes the same snapshot on the login node, and `ponzi-worker profile --snapshot DIR --site ceoas --out FILE` makes the profile from it anywhere.

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

The shipped `ceoas` profile, which the laptop and the tests render with, is made this way from the snapshot of 2026-10-27, and `test_profile_create.py` checks that it is exactly what the command makes. Its site file follows the job files of the system before the overhaul (ponzi-models `hpc/*.sbatch` and repeat_ccd's array scripts). `test_slurm.py` checks that the rendered scripts match those references: partition, account, excluded nodes (plus those down in the snapshot), GPUs, cpus, memory, walltime, throttle, roots, environment, exports and log folder.

The stages that never ran on the cluster keep the site's requests until a snapshot holds their jobs. Measuring them is on the [roadmap](../contributing/roadmap.md#phase-8-the-slurm-executor).

## The port reference (phase 0)

[ponzi-core `packages/pipeline/reference/phase0`](https://github.com/conflict-ecology/ponzi-core/tree/main/packages/pipeline/reference/phase0) holds repeat_ccd's own ISCE3 functions on one burst, with every intermediate kept. The check, `ponzi-pipeline port-check`, compares the port with it stage by stage on the bytes. Its README gives the three jobs and their resources.
