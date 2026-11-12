# Running on the cluster

Lessons from running the engine's campaigns on SLURM. How the PONZI worker submits batches is in [Running on the cluster](../service/hpc.md). Node and partition names are left out: they are this cluster's, and they change.

## Job state

**Progress is a job's terminal state in `sacct`. A job leaving `squeue` means nothing, and an exit code of 0 with no outputs is a failure.**

Failed jobs leave the queue too (`meta/2026-06-22-cslc-coherence-zarr-shared-archive-hpc-verify`). Use an array-aware `sacct -j ID -X` and count element states; record the job ids of each unit, not counts by state (`meta/2026-09-01-bright-per-burst-cadence-probe`, `meta/2026-09-04-majortom-v1-fullbatch-coherence-leg`).

## A sentinel is trusted only with sacct

**A completion file is trusted only if the job traps its signals, and only when `sacct` agrees it is finished.**

A preemption hit 11 drivers. One wrote `.done` with exit code 0 while SLURM marked it PREEMPTED and requeued it; the controller moved on and 5 stores were packed with 23 to 109 of their 110 to 115 dates. The fix traps TERM, INT and HUP and writes `.interrupted`, which is not terminal, and treats `.done` or `.failed` as in flight while `sacct` shows the job active. Why the exit code was 0 was never found (`meta/2026-10-21-preempted-driver-done-sentinel`).

## Dependencies

**Chain stages with `afterany` and have each job check its upstream's terminal state in `sacct` before working. Do not rely on `afterok`.**

A finalize step on `afterok` of a rerun fired before the array it belonged to had drained, and ran on missing shards (`aleppo/2026-06-10-aleppo-densest-bucket-methods-transfer-emit`). Both the coherence dispatcher and a copy of it used `afterok`; the gap spread by copying and was fixed in both at once (`syria/2026-07-25-icorr-syria-emit-campaign`). Finalize counts the actual shard markers and refuses to mark a partial store complete. Monitors fail loudly on PENDING with `DependencyNeverSatisfied`, and expect them to die when a session ends (`colombia_eq_2026/2026-08-15-colombia-eq-2026-s1-snapshot-campaign`).

## Generated commands

**Quote every token of a generated `sbatch` command except a closed list of intended shell expressions, and test it by running real bash.**

A JSON argument with spaces was joined unquoted; bash split it and every merge job failed after 33 s for two days, while all 2,335 shard tasks in the same window succeeded, so the fault showed only at the merge. Quoting everything would have broken `$SLURM_ARRAY_TASK_ID` and `$(( ... ))`, so the fix allows exactly those two shapes. A sibling bug parsed `"44G"` as an integer. The fix covered all 15 call sites (`meta/2026-08-04-coh-merge-quoting-fix-and-single-burst-verify`).

**Read the generated script** (a dry run, then grep `#SBATCH`) instead of assuming options reach it: a stale default node-exclusion list in code ignored the standing list in config (`meta/2026-08-01-bright-coherence-fleet`).

## The controller

**Run a campaign as a stateless controller that is called again, not as a long job that polls.**

- A `while true` controller in a 1-CPU job took about 4.5 hours a pass over 72 bursts under scratch contention; its 10-hour limit killed all four controllers mid-pass with their state in memory. Raising the limit to a week was called a symptom patch (`meta/2026-09-28-coherence-campaign-controller-redesign`).
- A submit-and-poll process that outlives its own limit cancels the array still draining (`meta/2026-08-01-bright-coherence-fleet`, `meta/2026-06-22-...`). The submitter hands off the job id; it does not poll and exit.
- **State comes from the stores' markers, not a ledger rewritten whole.** A pass that had started 4.5 hours earlier wrote back its stale view and reverted a burst that had just completed (`meta/2026-09-28-coherence-campaign-controller-redesign`).
- **Failed states are rechecked like blocked ones.** Five of 20 Gaza bursts sat failed for hours after the fix was live, because only blocked states were retried (`meta/2026-09-28-...`).
- **A controller that is running does not pick up a fix** until relaunched at the new commit; plan for the old behaviour in the meantime (`meta/2026-10-21-shared-scene-download-wait`).
- **Scope each leg's roster and progress.** One 1,431-burst roster starved later bursts by iteration order; a second leg documented as "a separate, later invocation" never ran, leaving 354 bursts without coherence until someone asked (`meta/2026-09-04-...`).

## Bound catalogue queries

**Catalogue queries at dispatch are bounded in time and never block the fleet.**

A controller spent 50 minutes in serial per-burst catalogue queries with the cluster idle; a healthy query took 25 s, 22 hours for 3,208 bursts. CDSE paging had no cap, and `asf_search` posted an error report on every error. The fix: 60 s per burst, a `timed_out` status that is asked again next pass, a 50-page cap, error reports off. Every pass still queries every burst; a service should cache completed answers (`meta/2026-10-20-dispatch-query-budget`).

## Ceilings and packing

**Bound the jobs in flight in the one function that submits, counting array elements, and allow no ad hoc loops around `sbatch`.**

- 750 shard tasks at once wedged 8 nodes; 36 array elements on one node wedged its epilog at teardown; on Syria, 46 % of 1,900 shards started within a minute, up to 62 a node, and 238 timed out from contention, not compute (`meta/2026-09-08-fleet-inflight-bound-node-packing`).
- **Count only RUNNING jobs against the ceiling and bound PENDING separately.** Counting pending jobs left about 70 running against a ceiling of 192 and starved submits for up to 70 minutes (`meta/2026-10-20-fleet-ceiling-running-only`).
- **A rule that is too blunt stalls production.** A per-node limit refused a submit with 97 of 200 in flight because one node held other work; it cost 40 minutes of a 7.5-hour budget. The relaxed rule only allows more, and falls back to the old rule if `sinfo` fails (`meta/2026-09-08-...`, amendment of 2026-09-09).
- **Do the fleet arithmetic before launch:** units in flight x tasks per unit within the ceiling (200 x 12 = 2,400 against 2,000 was cut to 166 x 12) (`netherlands_s1a/2026-11-04-netherlands-s1a-coherence-stores`).
- **Heavy-I/O tasks ask for at least 4 CPUs and 16 GB** so SLURM cannot stack them on one node; about 40 small-file readers suit the scratch filesystem, about 120 saturate it (`meta/2026-09-08-...`, `meta/2026-09-28-cross-sensor-12day-coherence-stores`).
- **`--ntasks-per-node` does not limit how array elements share a node.** It was a misdiagnosis, made jobs unschedulable with `--ntasks=1`, and was reverted. Serial programs run with `--ntasks=1`, since the partition's default above 1 caused a shared-write race (`meta/2026-06-25-frozen-coherence-axis-multiconflict-archive`, `meta/2026-06-09-cslc-zarr-writer-hpc-verify-densest-burst`).
- **Check a job can be placed** with `sbatch --test-only`, list more than one partition so a reservation on one does not strand a job, and keep bad nodes as runtime data with an expiry: all 34 quarantined nodes had lapsed a month later (`meta/2026-06-25-...`, `netherlands_s1a/2026-11-04-...`).

## Shared files on NFS

**A lock on a shared file has a heartbeat and is released only by its owner; a second worker waits rather than duplicating the work.**

Sibling bursts share a scene. The lock's age was its creation time and a waiter removed any lock older than 30 minutes; a 4 to 8 GB download under a busy fleet outlasted that, a second copy was extracted into the same SAFE, the loser saw 5 of 6 images, and 12 of 74 tasks failed in the first hour. The fix: a 60 s heartbeat, stale after 30 minutes without one, an ownership check by inode, and waiters that poll for up to 6 hours. Decide failures and requeues from the files once siblings in flight have settled (`meta/2026-10-21-shared-scene-download-wait`).

Copy HDF5 inputs made of many small chunks to node-local disk before reading; NFS stalled on them (`meta/2026-06-24-cslc-coherence-parallel-emit-byte-identity-verify`).

## Sizing

**Size from measurements of the actual units, store the predicted and measured peak per unit, and test an extrapolation on the densest case before trusting it.**

- A prediction of 1.5 to 2.5 GB per pair led to a 24 GB request; the measured peak was 11.1 GB (`meta/2026-06-22-...`). Two dense tiles of 103 ran out at the default request (`aleppo/2026-06-10-...`).
- A linear memory formula from one measured burst predicted 53 GB where the old formula said 472 GB; the larger bursts waited for one real measurement (`meta/2026-08-01-bright-coherence-fleet`).
- Ask first well below the old peak and treat running out of memory as the finding: 64 GB rather than 200 (`meta/2026-08-01-streaming-coh-merge`).
- Derive concurrency from free resources: 8 bursts in flight reserved at most 58 % of the 4.9 TB free (`meta/2026-09-04-...`).
- **A default that resolves to nothing can switch an optimisation off.** A skip-what-is-done check was guarded on an argument the chain never passed; the log said "0 already done" for 244 tasks and 85 CPU-hours went to re-geocoding when 2 tasks were needed. Resolve defaults once and print the skip count (`meta/2026-10-02-incremental-store-append`).

Historical costs, for orders of magnitude: 0.61 CPU-hours per burst-date on Iran (209,407 CPU-hours for 3,192 bursts); 54 CPU-hours a burst at about 107 dates on Tehran; merges of 46 to 51 GB (`netherlands_s1a/2026-11-04-...`, `meta/2026-09-28-cross-sensor-...`).

## Deploying code

**Code reaches the cluster only through git: pin the commit, check `HEAD` and a clean tree, reinstall so new entry points register.**

- The worktree a campaign was briefed on was 5 commits behind and lacked the writer it was meant to run (`meta/2026-07-05-coh-tbaseline-chunk-fix-and-t021-single-burst-reemit`). Nine jobs were lost to a stale commit; a branch missing the main fixes was caught with `git merge-base --is-ancestor` (`colombia_eq_2026/2026-09-26-t48-zarr-detector-run`).
- An editable install pointed at a stale worktree without the needed commands, so everything ran as `PYTHONPATH=... python -m` (`meta/2026-09-08-coherence-store-qaqc-done-contract`). Installed packages at pinned versions remove this class of error.
- Never run long work as an untracked background process on a login node; one died at item 270 of 285 without writing its record (`aleppo/2026-06-12-aleppo-param-l0-gee-publish`).
