# Coherence computation

Lessons about how coherence is estimated and checked. How PONZI computes it now is in [Coherence](../method/coherence.md).

## The estimator is a method choice, not plumbing

**Multilook the complex interferogram, then apply a NaN-aware window whose weights are renormalised over the valid samples. Never use a uniform boxcar with NaN set to 0.**

The engine's first estimator was an 8x8 (or 8x16) `uniform_filter` over values with NaN replaced by 0. It pulled coherence down wherever a window touched no-data. It was named the dominant cause of the gap between the engine's two chains: after the fix, damaged buildings in the same run went from 3,146 to 14,049. The replacement multilooked 6 range x 3 azimuth looks, then applied a NaN-aware Gaussian (sigma 1, truncated at 2, a 5x5 window), VV (`meta/2026-07-31-corrected-kernel-cslc-coherence-emit`).

When the estimator was still an open question (`meta/2026-06-22-cslc-coherence-zarr-shared-archive-hpc-verify`), the two candidates were a boxcar in map geometry and a radar-geometry chain (10 x 2 looks, a NaN-aware 5x5 Gaussian, then geocoding). The record states plainly that choosing between them changes the values.

*In PONZI:* the ISCE3 chain uses the radar-geometry estimator (10 x 2 multilook, NaN-aware Gaussian, sigma 1, truncated at 2). Its values will not match any product of the engine, and nobody should expect them to.

## Each parameter has one source

**An estimator parameter is defined in one place. Every reader, including derived products, takes it from the store it reads, never from a CLI or code default.**

- One script defaulted `--looks-rg` to 16 (a COMPASS default); the packer and the function signature used 8; the production store had been built with 8. The parallel run had to pin every parameter on the command line to stay identical, and the record says a mismatch would have been caught only late (`meta/2026-06-24-cslc-coherence-parallel-emit-byte-identity-verify`).
- A derived product (intensity correlation) was nearly built with the CLI default of 8 looks over a store built with 16. "A hardcoded default would silently corrupt the estimator", so it was made to read `estimator_params` from the source store (`syria/2026-07-25-icorr-syria-emit-campaign`).
- Before replacing a store, its attributes (`estimator_params`, `coherence_estimator`, `writer_command`) were read back and the recompute used exactly those (`meta/2026-07-05-coh-tbaseline-chunk-fix-and-t021-single-burst-reemit`).

*In PONZI:* the coherence spec is that one place, and its hash names the computation. Code defaults exist only for running without a spec.

## The DEM covers every footprint

**The DEM must cover the union of the geocoded burst footprints, not the AOI, with the sea filled at height 0. Check it before any compute and stop on a gap.**

The 2026-05-21 Aleppo "flat-earth" incident came from a DEM that covered the AOI but not the whole burst. NaN over the sea breaks `geo2rdr` or drops tiles, and Gaza is all coast. The fix was a coverage assertion as step 0 that exits on under-coverage, and LZW compression rather than DEFLATE for the DEM tiles (`meta/2026-06-09-cslc-zarr-writer-hpc-verify-densest-burst`, `meta/2026-06-22-...`).

*In PONZI:* the `dem` stage.

## Compare chains at the decision level

**Two coherence chains that agree field for field can still disagree on detections. Check a new chain against the decisions it feeds, not only against the coherence.**

The corrected CSLC chain and the production ISCE3 chain correlated at r = 0.967 on matched coherence fields. On 464,006 common buildings the detections had a Jaccard index of 0.32, recall 0.66 and precision 0.38: the CSLC chain flagged about 1.71 times more. The suspected cause, multilooking in map rather than radar geometry, was never resolved (`meta/2026-07-31-corrected-kernel-cslc-coherence-emit`).

## Say what "identical" means

**Set the standard of identity by the kind of operation, and write it down before the comparison.**

| Operation | Standard |
| --- | --- |
| Copy, re-layout, change of container | Exact bytes of the decompressed values |
| Recomputation of the same estimator | Within 2 ULP: `scipy` filters gave up to 2 ULP differences between runs and nodes |
| A new chain with no reference | Schema, finite values in [0, 1], plausible scene (see below) and catalogue cross-checks |

A run aimed at bit-for-bit identity between serial and parallel coherence found the 2-ULP non-determinism and had to restate its goal. A later campaign declared anything beyond 2 ULP "a STOP, not a tunable tolerance" (`meta/2026-06-24-...`, `meta/2026-07-05-coh-tbaseline-full-productionization-campaign`, `meta/2026-10-02-incremental-store-append`). Compare values through an integer view of the floats, so NaN payloads count too; compare compressed bytes only with deterministic compression ([Stores](stores.md#deterministic-bytes)).

## One burst, looked at, before the fleet

**Before scaling a new estimator or chain, run one burst and look at it.**

The checks the engine used: every value in [0, 1]; towns high and water and vegetation low; no image all 0 or all 1; no NaN bleeding in from the burst edges; min, max, median and per cent valid reported; the temporal median of the 12-day coherence exported as a GeoTIFF and reviewed in a GIS. The fleet run waited until this burst passed (`meta/2026-07-31-...`).

## Costs (historical)

Serial coherence took about 13 s per pair (1,564 pairs in 5 h 46 min, overrunning a 6-hour limit); sharded across an array it took about 19 minutes (`meta/2026-06-24-...`). Another chain measured 8.2 s per pair (`meta/2026-08-01-bright-coherence-fleet`). These were CSLC-based chains; measure the ISCE3 chain afresh.
