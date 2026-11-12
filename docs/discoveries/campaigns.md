# Campaigns

Lessons about planning, running and closing a campaign: which bursts, in what order, when it is finished, and what was decided along the way.

## Done is defined by the request

**A burst is done when its store meets the request (window, baselines, platforms, area), not when a valid store exists.**

On 2026-09-05 all 372 Major TOM stores were "verified on disk". Checked against the delivery request, 123 failed: 120 covered a shorter window than asked, 3 lacked requested baselines, and 38 more had no store at all. BRIGHT passed 16 of 29. Every gate (the writer's validator, the verify step, the done marker, the closeout) checked only that a store existed and was well formed, and no store recorded the window or the request it was built for. The fix was a request file per (campaign, burst), checks A to J against it, and a closeout that succeeds only when every row is done or is a real gap with catalogue evidence (`meta/2026-09-08-coherence-store-qaqc-done-contract`).

- **Measure completeness against the catalogue's expected acquisitions,** not a tolerance in days: tolerances of 30 and 23 days could not tell a missing date from a normal lead-in, and some stores ended a year early.
- **Make the hand-off from acquisitions to pairs a blocking comparison with the catalogue.** For one volcano, 54 of 121 expected slots were empty although both satellites acquired on those dates; the pair builder read what was on disk, and the planned comparison had never been written.
- **"Catalogued" is not "acquired"** ([Sensors and acquisitions](acquisition.md)).
- **Chain to the final product and declare done only there.** A finished upstream stage is not a delivery ([Running on the cluster](cluster.md#the-controller)).
- **A failed check is "not evaluated", not "passed".** A gap class that counts as done hides processing faults; when the definition of done changes, mark records with a version so the old ones are checked again (`meta/2026-10-01-scene-level-availability-request-manifest`).
- **Trace every step a definition change reaches.** A new definition of missing dates sent a router round a no-op acquire forever, and a step that ran in the same pass archived a good marker before a check refused the store (`meta/2026-10-01-...`).

## Rosters

**Never trust a hand-written roster. Reconcile every row against the archive, the catalogue and the burst footprints before dispatch, and derive the action from what exists.**

- Major TOM: 15 of 200 cells (28 of 412 rows) carried bursts of unrelated campaigns, 2 bursts were listed twice across cells, and 26 bursts were on a track that does not cover their cell (`meta/2026-09-02-majortom-v1-fullbatch-dispatch`, `meta/2026-09-08-...`).
- BRIGHT backfill: 5 of 6 extension rows had wrong bounds (four exactly 12 days off), and a row marked "new" already had a store. The windows were derived again from the stores' own time axes (`meta/2026-09-02-bright-minimal-coverage-backfill`).
- A roster of 1,429 held 17 corrupt and 22 degenerate bursts (`meta/2026-08-01-bright-coherence-fleet`).
- Colombia's three event rosters had 82 bursts each but differed by 7 each way; the union was 89 (`colombia_eq_2026/2026-09-26-t48-zarr-detector-run`).
- Coverage values were recomputed for known cells and had to match the stored ones to 0.001; a cell needing more than one orbit was redrawn (`meta/2026-09-30-majortom-arid-burst-db-probe`).

**The burst set is an explicit input,** filtered before any expensive step. One driver listed every scene in a shared folder (1,879 scenes, three tracks) and would have run tracks nobody approved (`syria/2026-07-25-idleb-ab-cslc-coherence-campaign`). Another resolved all of a scene's ~27 bursts and enumerated up to 20,000 tasks a cell; every job of the test batch failed or timed out (`meta/2026-09-01-majortom-fullbatch-hardening`).

**Count the inventory again before sizing.** Lebanon was recorded at 281 S1A of 502 scenes, then counted at 1,027 of 1,285 ten days later with no new files: a counting error that broke the plan (`meta/2026-07-05-coh-tbaseline-full-productionization-campaign`). Check that cached inputs still exist; Lebanon's 17.7 TB of intermediates had been deleted to free space (`syria/2026-07-25-*`).

**Decide inclusion rules early.** A rule of "more than 1 % of the burst inside the area" kept 52 of 200 Netherlands bursts that are more than half open water (`netherlands_s1a/2026-11-04-netherlands-s1a-coherence-stores`).

## Canary first

**Profile the densest unit, then run one canary chosen at the hardest known case with its acceptance numbers written in advance, then one region, then the fleet.**

"Never dispatch-then-discover at cluster latency" recurs in nearly every record. Pick the densest unit from manifest counts (16 Lebanon bursts tied at 182 dates); pick the canary where the last failure happened (the burst where the collision first appeared; the densest burst with a switch; one Netherlands burst inland and one with half its DEM filled). Run a verification against its own roster and progress, on a burst with no complete store, or it is skipped and proves nothing (`aleppo/2026-06-10-...`, `meta/2026-09-28-cross-sensor-12day-coherence-stores`, `netherlands_s1a/2026-11-04-...`, `meta/2026-08-04-coh-merge-quoting-fix-and-single-burst-verify`). Re-prove identity on existing data after a code change before fanning out; passing the schema check is not identity (`meta/2026-07-06-ponzi-cslc-allplatform-campaign`).

## Tests and changes

- **Use the real failing records as test fixtures.** 33 tests on real catalogue records, including the three that broke simpler rules; regression tests on the real dates of the collision burst (`meta/2026-10-01-...`, `meta/2026-09-28-...`).
- **Compare failure sets, not a green run.** With 78 failures already present, a change passed when the failing ids were identical before and after; a large deletion compared both failure sets and the dry-run plans, and tagged the fork point first (`meta/2026-08-31-majortom-v1-test-batch`, `meta/2026-09-17-slim-branch-lineage-retirement`). Show a failure is old with an A/B run before calling it unrelated (`meta/2026-09-25-coh-tbaseline-per-platform-stores`).
- **A fast path is checked against the slow reference on the densest tile of each new region;** identity does not carry over between regions (`aleppo/2026-06-10-...`). Diagnostic and production code share one core (`aleppo/2026-06-18-p116-layer2-cross-geometry-staging`).
- **When one copy of a defect is found, fix every copy** in the same change (`syria/2026-07-25-icorr-syria-emit-campaign`, `meta/2026-08-04-...`).
- **When removing code, find every caller** in the same change (`meta/2026-06-09-cslc-zarr-writer-coherence-carveout`).
- **Check the real command line before writing a dispatch command;** one drafted command used options that did not exist (`meta/2026-06-09-cslc-zarr-writer-hpc-verify-densest-burst`).

## Deleting

**Delete an input only after every product it feeds is complete and checked, and move to a backup before clearing.**

Deleting intermediates when they were packed left 17 bursts without coherence, because the coherence step still needed them (`meta/2026-08-31-...`). A scene covers about 27 bursts across three subswaths, so it can go only when all of its bursts in the area are complete; deletion runs in two phases with a manifest of what goes and why, and a reviewed dry run (`meta/2026-06-25-frozen-coherence-axis-multiconflict-archive`). Deleting a product because it can be rebuilt is an exception to state and have signed off (`meta/2026-09-02-bright-lane-b-coherence-reemit`).

## Records and decisions

- **One record per campaign.** Scope changes produced chains of superseded, reactivated and deferred records that contradicted each other (`meta/2026-07-05-*`).
- **Choose the design once, before the fleet.** The sensor policy changed six times in five days ([The time series](time-series.md#choose-the-sensor-policy-once)).
- **Write a ruling into the canonical docs the same day.** The engine retired a method by a spoken ruling while its docs still called it frozen and active (`meta/2026-09-17-...`).
- **Record what authorised each run.** Runs went ahead on a blanket instruction, or under another record's approval for a tool that record had called unchanged (`meta/2026-08-01-bright-coherence-fleet`, `meta/2026-08-04-...`). An approval to run does not cover a methodological gate (`colombia_eq_2026/2026-09-26-...`). An approval check that never read the approval field passed everything until it was noticed (`meta/2026-07-06-...`).
- **Do not cite numbers you cannot trace.** A "43-minute pack" was looked for in the day's `sacct` history, not found, and not used (`meta/2026-09-25-*`).
- **Match the review to the risk.** Full review of a scoping document with no compute was named an anti-pattern (`meta/2026-06-06-active-monitoring-architecture-gaza-lebanon`).
- **Keep incident history in records, not in code comments.** 40 % of seven core modules was comments, much of it incident narration (`meta/2026-09-17-...`).
