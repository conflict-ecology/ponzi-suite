# Detection and scoring

Lessons about turning coherence into detections. The engine's detectors (a rolling Gaussian, a parametric fit with seven terms, later a snapshot detector) are not PONZI's: PONZI forecasts the series and scores the residuals. These lessons are the ones that hold for any detector. Note that the engine retired its time-series detectors on 2026-09-17; the overhaul goes the other way.

## Keep the threshold out of the stored score

**Store the threshold-free score and apply the operating point downstream, so a new calibration never needs a recompute.**

Aleppo had no calibration anchors at all and inherited its thresholds (z = -2 and -4) from a Lebanon pilot, with transfer to Aleppo marked unknown. Storing the aggregate score let an Aleppo operating point be applied later without re-running; the downstream products read the stored event band and never re-thresholded (`aleppo/2026-06-10-aleppo-densest-bucket-methods-transfer-emit`, `aleppo/2026-06-14-aleppo-p116-likely-damage-full-footprint`).

**When an operating point is borrowed, say so on every output.** Each image carried its threshold and `z_thresh_calibration = inherited_uncalibrated_lebanon_matched_fp_pilot` (`aleppo/2026-06-12-aleppo-param-l0-gee-publish`).

**Set run parameters once,** in the run's stored metadata; later steps read them back and treat a flag passed again only as a check that fails on mismatch (`aleppo/2026-06-10-...`).

**Thresholds that differ by region are required inputs, never defaults** (`aleppo/2026-06-18-p116-layer2-cross-geometry-staging`). Do not pick a valid-pixel threshold before seeing the distribution; report it first (`meta/2026-09-08-coherence-store-qaqc-done-contract`).

## Warm-up and the clean span

**A model's warm-up drawn from inside the event contaminates its early scores. State the span that can be scored cleanly.**

With 30 acquisitions of warm-up, Aleppo's first score was 2016-09-08, its warm-up 2015-08 to 2016-08: inside the battle. Scores for 2016 and 2017 were called war-contaminated; the clean span starts after 2017 (`aleppo/2026-06-10-...`). The same holds after every [sensor switch](time-series.md#at-a-switch-bridge-the-gap), when the baselines fill again one by one.

**Check whether empty outputs are structural before calling them a bug.** 38 empty dates on Aleppo were the expected floor: 36 of warm-up at the start, 2 cut off at the end. The dates with any score became the explicit list of what to publish, and publishing stopped if the count differed (`aleppo/2026-06-12-...`).

## Store how well the model fitted

**Store the model's fitted parameters and a precisely defined measure of fit with the product.**

The released product kept no fit coefficients, so a later analysis had to re-fit about 3,200 pixels. The fit error the scientist meant (the weighted gap between observed and modelled coherence, median 0.118 on one bucket) was not the residual spread the code had called RMSE (0.085); the definition was written down and the proposed bands were fit RMSE, R², seasonal amplitude and the coefficients (`meta/2026-06-16-production-fit-rmse-sme-definition`, `aleppo/2026-06-18-...`). New output bands are added with a check that the decision bands are byte-identical to the run before (`meta/2026-06-16-...`).

## Compare a new chain with the old product by its decisions

- **Field agreement is not decision agreement:** r = 0.967 gave a Jaccard of 0.32 ([Coherence](coherence.md#compare-chains-at-the-decision-level)).
- **Write the acceptance checks against the old product in advance.** For Colombia: coverage at named points (both were empty in the old product, cause unknown); bursts missing because never built kept apart from bursts the detector dropped; the rule for merging overlapping bursts (select the lowest distance, not the maximum score); and transects across burst seams, where the old mosaic showed a step in z (`colombia_eq_2026/2026-09-26-t48-zarr-detector-run`).

## Limits to state

- **Dense urban areas at 40 m:** a single building's signal is below the noise; only aggregates over many buildings are clean. Do not make per-building claims (`aleppo/2026-06-10-...`).
- **Ascending and descending geometries differ** in layover; report the layover fraction when comparing them (`aleppo/2026-06-18-...`, a plan, not a result).
- **Across a sensor switch,** radiometric equivalence of S1C and S1D with S1A is not shown ([The time series](time-series.md#the-constellation-as-observed)).
- **In aggregated products,** outside coverage is NULL, never 0, and cumulative counts reconcile with the per-period sums (`aleppo/2026-06-14-...`).

## Monitoring

**Scheduled monitoring needs a frozen model and an append proven identical to a rebuild.** When it was scoped, three versions of the event definition coexisted and the store could only be rebuilt; the trigger was to be a schedule at the satellite's revisit, not a polling loop (`meta/2026-06-06-active-monitoring-architecture-gaza-lebanon`).
