# Stores

Lessons about writing, naming, checking and changing coherence stores. The current format is the [coherence store contract](../reference/contracts/coherence_store.md).

## Agree the layout with the reader

**Write the layout the reader needs, agreed before shipping, and have the validator enforce it.**

- A store shipped in a retired pair-indexed `(sample, y, x)` layout that the model could not read. Moving to `(time, y, x, baseline)` is a scatter into a grid, not a relabelling: every input pair must be accounted for (packed + unresolved + collided = all pairs) (`meta/2026-07-05-coh-tbaseline-chunk-fix-and-t021-single-burst-reemit`).
- A missing temporal baseline turned into 0 and collapsed the baseline axis; the fix falls back to the difference of the dates (`meta/2026-07-05-...`).
- When no reference store exists, write the reader's contract out field by field and check each (dimensions, dtype, shapes, dense baseline axis, chunk shape, NaN fill and pair conservation) (`meta/2026-07-05-...`).

## Chunk for the reader

**Choose the chunk shape from how the store is read, and derive the expected shape in the validator from the store's own dimensions.**

A rule written before the reader was known said "never split the time axis" (`{time: -1, y: 512, x: 512, baseline: -1}`, chunks of 0.8 to 2.3 GB). The model reads one `(y, x, baseline)` slice per time step, so the rule was reversed to `(1, H, W, n_baseline)`, about 39 MB a chunk (`meta/2026-07-05-...`). Check the chunk tuple, not only the shape, before running code that assumes it (`aleppo/2026-06-10-aleppo-densest-bucket-methods-transfer-emit`).

## Write in a stream

**Write a store in two passes, first the metadata, then one chunk-aligned buffer at a time. Never hold the whole array.**

On one burst (121 dates, 1543 x 3304, 30 baselines, 3,119 pairs) the old writer peaked at 178.5 GiB, holding two full-size buffers; the streaming writer peaked at 19.2 GiB in about the same time (`meta/2026-08-01-streaming-coh-merge`). Assemble each chunk in memory and write it once: writing cell by cell into compressed chunks recompresses them O(n²) times (`meta/2026-06-25-frozen-coherence-axis-multiconflict-archive`). Verification streams too; an earlier check ran out of memory loading a whole array (`aleppo/2026-06-10-...`).

## One writer per store

**Spread the computation over tasks that each write their own shard, and let one writer merge them. Never let two tasks write one Zarr store.**

With chunks spanning the whole pair or time axis, two tasks writing different samples would read, modify and write the same chunk. The merge sorts and deduplicates by pair, so the result does not depend on how the work was split; it was tested with 1, 2, 3, 5 and 11 shards, shuffled, and with duplicates across shards (`meta/2026-06-24-cslc-coherence-parallel-emit-byte-identity-verify`).

**Serial and parallel paths share the function that decides which pairs exist.** The parallel path read pairs by globbing a directory (782 resolvable) while the serial one used the pair list (1,564): identity was impossible before a pixel was computed. A dry run that compared the resolved count with the reference caught it (`meta/2026-06-24-...`).

## Completion

**`.partial`, then fsync, then an atomic rename, then `_complete`, written only after the checks pass. Readers refuse anything without it.**

Every record relied on this; a controller that finds `_complete` skips the burst with no work at all (`meta/2026-08-01-bright-coherence-fleet`). Three ways it went wrong:

- **The marker said nothing about what was asked.** After six bursts' inputs were extended, the controller trusted their markers and would have skipped them, leaving stale stores; there was no rebuild flag. The fix stamps the request, the time bounds, the baselines and the platforms into the store and its marker, and adds an explicit rebuild (`meta/2026-09-02-bright-lane-b-coherence-reemit`, `meta/2026-09-08-coherence-store-qaqc-done-contract`).
- **Different store types used different markers.** Gating on `_complete` silently excluded every store of a type that had none (`meta/2026-09-02-bright-minimal-coverage-backfill`).
- **A marker is only as good as the job that wrote it** ([preemption](cluster.md#a-sentinel-is-trusted-only-with-sacct)).

## Provenance in the store

- **Record the estimator, its parameters and the full command** in the store's attributes, and rebuild from those, not from memory (`meta/2026-07-05-...`).
- **Check provenance is parsed, not just present.** A writer that fails to parse its parameters stores `{"_raw_unparsed": ...}`; done means the parsed fields are all there (`meta/2026-08-04-coh-merge-quoting-fix-and-single-burst-verify`).
- **Downstream code takes its input paths from store attributes,** never from region-specific file names; a Lebanon file name was nearly read for Aleppo (`aleppo/2026-06-18-p116-layer2-cross-geometry-staging`).
- **Per cell: platform, the earlier image's platform and date, and the perpendicular baseline,** so the true span can be recovered (`meta/2026-09-28-cross-sensor-12day-coherence-stores`).
- **Keep a pair ledger with each store,** checked against the marker's digest, so what a store holds is known without recomputing. The one the engine had was overwritten in place on every rerun (`meta/2026-10-02-incremental-store-append`).
- **Consolidate the metadata as the last write.** None of 941 stores had `.zmetadata` although it had been asked for, and the catalogue missed every store under the new folder layout (`meta/2026-09-08-...`).

## Names and addresses

- **Name the location by the computation, derived, never typed in.** A folder named from the estimator's parameters (`gauss_w5x5_s1.0_ml6x3_vv`) kept a new estimator from overwriting the old stores (`meta/2026-07-31-corrected-kernel-cslc-coherence-emit`). PONZI's spec hashes do this.
- **Keep names people change out of identity.** Stores tagged with a conflict id that was later renamed left a shared archive in a mixed state (`syria/2026-07-25-idleb-ab-cslc-coherence-campaign`).
- **Refuse to guess when two stores match.** Two complete stores with different estimators for one burst broke a check script; the resolver now raises on ambiguity (`meta/2026-09-25-coh-tbaseline-per-platform-stores`).
- **One physical burst, one store** covering the union of the windows that ask for it; requests are separate files that point at it. Eight Major TOM rows found their burst's store built for another campaign's window (`meta/2026-09-08-...`).
- **Index a shared archive by burst,** with region and time as catalogue columns rather than folders (`meta/2026-06-22-cslc-coherence-zarr-shared-archive-hpc-verify`).

## Changing a store

- **Schema changes are additive.** New variables are flagged by an attribute and validators check them only where it is set, so older stores still validate (`meta/2026-10-20-seam-bridge-span-days-flag`); a new layout goes to a new address beside the old store (`colombia_eq_2026/2026-09-26-t48-zarr-detector-run`).
- **Before changing a store's shape, audit every reader against the code.** The validator assumed a regular time axis, three sizing scripts predicted the shape from a regular grid, and a "pluggable" detector took exactly one store (`meta/2026-09-25-coh-tbaseline-exact-acquisition-identity`).
- **A rebuild never shrinks coverage.** Refuse a replacement whose time axis is not a superset of the old one; the guard must not depend on the old marker, since a forced rebuild removed the marker first and skipped the guard (`meta/2026-09-08-...`, `meta/2026-10-02-...`).
- **Extending refuses overlaps and survives a crash:** reject dates already present, back up, rename in two steps, recover a stray backup on the next call (`meta/2026-09-02-bright-minimal-coverage-backfill`).

## Append or rebuild

**Rebuilding a whole store to add a date is the dominant cost of keeping a series current.** Filling 2 dates on one burst re-geocoded all 244 acquisitions, recomputed all 17 blocks (860 pairs where about 19 were new) and rewrote a 5 GB store; a whole-store fingerprint over every granule name invalidated every block. The proposed design reuses blocks keyed by their pair set and their inputs' versions, keeps a pair ledger, and publishes by a hard-linked copy swapped in with one rename, keeping the previous generation for rollback. It estimated about 8 minutes instead of 27, but was never run (`meta/2026-10-02-...`). Monitoring on a schedule needs an append that is proven identical to a rebuild (`meta/2026-06-06-active-monitoring-architecture-gaza-lebanon`).

## Deterministic bytes

**Multi-threaded blosc compression is not deterministic. Pin it to one thread before writing if compressed bytes are to be compared.** With the pin, 120 of 120 chunk hashes matched; without it they did not, even with the old writer unchanged (`meta/2026-08-01-streaming-coh-merge`). Otherwise compare decompressed values ([Coherence](coherence.md#say-what-identical-means)).

## Sizes (historical)

A coherence store was 1.1 to 1.3 GB per burst at about 120 dates (2.75 GB on average across Major TOM; 3.0 GB per 110 slots and 7.8 GB per 267 slots on Iran); one S1A scene 7.4 GB. A memory request of "50G" in notes was later taken for a store size; size from measurements (`meta/2026-06-25-...`, `meta/2026-09-08-...`, `netherlands_s1a/2026-11-04-netherlands-s1a-coherence-stores`, `meta/2026-10-02-...`).
