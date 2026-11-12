# Sensors and acquisitions

Lessons about finding and fetching Sentinel-1 data. What PONZI fetches now is in [Data sources and catalogs](../method/data-sources.md).

## A missing burst product is not a missing acquisition

**The expected acquisitions of a burst are the burst products plus the full scenes that contain the burst. An empty burst search proves nothing.**

- ASF's burst catalogue had no VV burst for 17 Gaza (burst, date) slots although the full dual-polarisation scenes existed at both ASF and CDSE. All 20 affected rows were closed as `PASS_AVAILABILITY_GAP`, a "done" class, so nothing ever fetched them. Under the new definition 16 of the 20 became processing gaps. Over 20 bursts there were 67 scene-only (burst, date) keys (`meta/2026-10-01-scene-level-availability-request-manifest`).
- ASF's burst extraction returned VH only for some (burst, date) pairs whose scenes held VV too; confirmed on 5 bursts. Downloading the full scene and extracting the bursts locally worked (`meta/2026-09-25-coh-tbaseline-per-platform-stores`, `caveats.md`).
- On Major TOM, of 4,747 uncovered dates, 4,380 were catalogued acquisitions the engine had failed to process; only 367 were real gaps (`meta/2026-09-08-coherence-store-qaqc-done-contract`).

*In PONZI:* `discover` builds the expected set from both, and a gap counts as an availability gap only with catalogue evidence.

## Membership by burst id, not by footprint

**Decide whether a scene contains a burst from an authoritative list of burst ids (CDSE's `Bursts` endpoint or the SAFE annotation), not from geometry.**

A "burst centre inside the scene polygon" test on 175 scenes gave 350 false positives among 5,089 predicted pairs, every one the neighbouring burst just outside the scene; a threshold would have had to sit in an overlap band of 0.601 to 0.677 fitted on one region. CDSE's `Bursts` matched the SAFE annotation on 40 of 40 scenes across S1A, S1B, S1C and S1D, at about 1.3 s a query (`meta/2026-10-01-...`).

Related: select bursts by their full burst id, not by path or track. Selection by track staged the wrong set once (`aleppo/2026-06-18-p116-layer2-cross-geometry-staging`), and a helper that derived the track from a granule name had an off-by-one error (`syria/2026-07-25-idleb-ab-cslc-coherence-campaign`). Take ids verbatim from the list.

## Acquisition identity

**Identify an acquisition by platform and sensing time from the scene name, and compare by that, never by product id or a catalogue row's own timestamp.**

- 3 of 263 CDSE `Bursts` rows for one burst were exactly one or two hours early. CDSE listed one acquisition twice under two product ids. Counted as products ASF and CDSE differed (681 against 686); counted as acquisitions they nearly matched (680 against 684, 680 common) (`meta/2026-10-01-...`).
- Re-assembled burst SAFEs get a new product id each time, so a "has this been done" check that compared product ids redid work (`meta/2026-10-02-incremental-store-append`).
- Match a burst to a scene by "the burst start lies inside the scene's sensing window, plus 2 s", not by a fixed tolerance: slices are 27 to 36 s long and a burst can start 32 s into a scene, beyond the 30 s tolerance then in use (`meta/2026-10-01-...`).

## Holdings differ by provider and platform

**ASF and CDSE do not hold the same scenes. Make the provider policy per platform and explicit, and record what is dropped instead of counting it as a failure.**

- Gaza had 4 S1C acquisitions held only by CDSE, in the commissioning window 2025-03-29 to 04-03 (`meta/2026-10-01-...`).
- On Iran, two S1D scenes were CDSE-only. They produced 33 ASF "not found" failures of about 5 minutes each, then CDSE downloads of 8.65 GB a scene at 3 to 10 MB/s under a 4-slot cap; the non-zero failure count stalled the unit. The ruling: "If S1D is missing fallback to S1C for now and take notes of it in the logs. Don't wait for CDSE" (`meta/2026-10-21-s1d-asf-only-no-cdse-wait`).
- For event response the opposite held: the co-event scene for Cali existed only on CDSE, and the standing rule was to download from CDSE first (`colombia_eq_2026/2026-08-15-colombia-eq-2026-s1-snapshot-campaign`).
- CDSE authentication failed from some cluster nodes and not others (`meta/2026-07-06-ponzi-cslc-allplatform-campaign`). Downloads run only where it works.

**Use one catalogue function for the expected set and for the download.** When the request and the gap-fill used different searches they disagreed, and every later exclusion had to be added on both sides (`meta/2026-10-01-...`, `meta/2026-10-21-s1d-...`).

## Failed queries are "not evaluated"

**A catalogue query that fails or times out leaves the burst unevaluated, never "no scenes".** The fixed manifest keeps a null expected set and the error, and the closeout reports NOT_VERIFIED so the next pass asks again. A cap on CDSE paging raises rather than returning a truncated list (`meta/2026-10-01-...`, `meta/2026-10-20-dispatch-query-budget`). Query costs and budgets are in [Running on the cluster](cluster.md#bound-catalogue-queries).

## The newer sensors

- **Orbits.** A worker that assumed orbit files were present failed on S1C and S1D; the driver had to fetch the restituted orbits for the ascending-node window first. Recent acquisitions may have only restituted orbits (precise orbits arrive about 20 days later): keep them and record the orbit class per acquisition (`meta/2026-07-06-...`, `meta/2026-06-25-frozen-coherence-axis-multiconflict-archive`).
- **Mass failures are bugs until shown otherwise.** 1,974 failures on Colombia track 48 were a bug in the orbit file's time margin, not missing data (`colombia_eq_2026/2026-08-15-...`).
- **Keep the platform list current everywhere.** `--platform S1C` did not parse because the token map knew only S1A and S1B, two tests asserted that S1C is rejected, and the controller did not pass `--platform` on (`meta/2026-09-25-coh-tbaseline-per-platform-stores`).
- **A sensor policy is a coverage cap.** The old burst database predated S1C and S1D, so an S1A-only policy was used; it left out 54 % of Caracas's scenes (S1C and S1D) and about 44 % of Lebanon's at the time. It was reversed on 2026-07-06 (`meta/2026-06-25-...`, `meta/2026-07-06-...`).
- **Request only what the series uses.** A controller for S1B dispatched Lebanon bursts that have no S1B data after 2021 (`meta/2026-09-28-cross-sensor-12day-coherence-stores`).
- **Long histories cross a burst-id change** at IPF 3.40; check it for any window that reaches back (`syria/2026-07-25-idleb-...`).

## Download by burst

**Downloading bursts rather than scenes cut the volume about 24 times** (298 MB for a 2-burst VV SAFE against 7.2 GB a scene), with requests of 14 to 38 s and no rate limiting at 8 concurrent requests, and worked back to the 2015 archive. Burst products are ASF-only, with no CDSE fallback (`meta/2026-09-01-burst-acquire-lane`). Given the gaps above, PONZI needs the scene path as a fallback.
