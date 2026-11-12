# Discoveries

What the coherence engine taught us before the overhaul. Between June and November 2026 the coherence engine (the predecessor of `ponzi-pipeline`) was run on campaigns over Gaza, Lebanon, Aleppo and the rest of Syria, Iran, Colombia, the Netherlands, the BRIGHT conflict set and the Major TOM panel. Each campaign and each fix was written up as a design record. These pages distill those records into lessons for the system being built now.

The records themselves are not in this repository. They are the `coherence-engine-design-records` archive (61 records, 2026-06-06 to 2026-11-04); each lesson names the record it comes from by its folder, for example `meta/2026-10-02-incremental-store-append`.

## How to read these pages

- Each lesson is one sentence in bold, then what happened, then what it means for PONZI now.
- **Historical** marks a lesson or a number that belongs to a chain PONZI no longer has: OPERA CSLC (COMPASS), the boxcar estimator, Earth Engine, the per-record approval gate. Their numbers are orders of magnitude at most for the ISCE3 chain.
- Many records are designs that were approved and run later. Where a number comes from a later run quoted in a record, or was predicted but never measured, the lesson says so.
- The records reached some decisions the overhaul reverses. In particular, the engine retired the TiDE and rolling methods on 2026-09-17 in favour of a snapshot detector; PONZI runs forecast models (TiDE, rolling OLS) over the coherence series. The lessons about scoring here are the ones that hold either way.

## Pages

| Page | What it covers |
| --- | --- |
| [Coherence computation](coherence.md) | The estimator, the DEM, and what agreement between two coherence chains does and does not prove |
| [Sensors and acquisitions](acquisition.md) | ASF and CDSE catalogues, burst identity, orbits, S1A/B/C/D holdings |
| [The time series](time-series.md) | The 12-day lattice, sensor switches, bridge pairs and cell collisions |
| [Stores](stores.md) | Writing, chunking, completion, provenance, appending and rebuilding |
| [Running on the cluster](cluster.md) | Job tracking, dependencies, ceilings, locks, preemption, sizing |
| [Campaigns](campaigns.md) | Rosters, canaries, definitions of done, deletion, records and decisions |
| [Detection and scoring](detection.md) | Thresholds, warm-up, fit diagnostics, comparing a new chain with an old product |

## The ten that matter most

1. **Done means the request is met, not that a store exists.** 123 of 372 "verified" Major TOM stores failed their delivery request ([Campaigns](campaigns.md#done-is-defined-by-the-request)).
2. **An empty catalogue answer is not a missing acquisition.** ASF's burst catalogue missed scenes that existed at ASF and CDSE; the engine closed them as availability gaps and never fetched them ([Sensors and acquisitions](acquisition.md#a-missing-burst-product-is-not-a-missing-acquisition)).
3. **Sensor switches break a single-sensor series.** S1C and S1D fly a day off S1A's phase; rounding dates into slots put four pairs into one cell ([The time series](time-series.md)).
4. **Progress is a terminal `sacct` state, never a drained queue or a sentinel on its own.** A preempted job wrote `.done` and five stores were packed incomplete ([Running on the cluster](cluster.md#a-sentinel-is-trusted-only-with-sacct)).
5. **The estimator decides the values.** A boxcar with NaN set to 0 was the main cause of a 4.5x difference in damaged buildings between two chains ([Coherence computation](coherence.md)).
6. **Fields that agree do not mean decisions that agree.** r = 0.967 between two coherence fields gave a Jaccard of 0.32 on the detections ([Coherence computation](coherence.md#compare-chains-at-the-decision-level)).
7. **One writer per store, and a streaming writer.** Peak memory fell from 178.5 GiB to 19.2 GiB on the same burst ([Stores](stores.md#write-in-a-stream)).
8. **Chunk for the reader.** A "never split time" rule was the opposite of what the model needed ([Stores](stores.md#chunk-for-the-reader)).
9. **Profile the densest unit, then a canary, then the fleet.** Every campaign that skipped a step found out at cluster latency ([Campaigns](campaigns.md#canary-first)).
10. **Never trust a hand-written roster.** Rosters were wrong in 15 of 200 cells, and in 5 of 6 extension rows ([Campaigns](campaigns.md#rosters)).
