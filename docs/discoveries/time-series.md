# The time series

Lessons about the (time, baseline) series a burst's coherence is arranged into, and about what happens to it when the satellites change. How PONZI pairs acquisitions is in [Coherence](../method/coherence.md#a-bursts-series).

## The constellation, as observed

These are facts about Sentinel-1, measured from the catalogues, that any series design has to meet (`meta/2026-09-28-cross-sensor-12day-coherence-stores`, `meta/2026-10-07-sensor-seam-two-lattice-series`, `meta/2026-09-25-coh-tbaseline-per-platform-stores`, `design.md`).

- **Phases.** S1C flies one day after S1A's phase, so an S1A to S1C pair spans 13 days on every Gaza and Lebanon track. S1D is about one day off the shared S1A/S1C phase, so 11 or 13 days against either. S1D against S1A gives 7, 19, 31 days: the 6-day interleave. Cross-sensor spans seen were 11, 13, 23, 25, 35, 37, 47 and 49 days.
- **Switches.** S1B's last acquisition was 2021-12-23. S1C started in April 2025 and S1D in April 2026 (Gaza: S1C from 2025-04-10 to 04-15 by path, S1D from 2026-04-19). S1A's last catalogued acquisitions were late June 2026, by track. On Tehran, S1A stopped and S1D started 7 days later on every track. S1C has a 31-day gap at a manoeuvre, which is not a multiple of 12 and splits its record in two.
- **Cadence.** Not one revisit interval over a whole window. None of 1,407 BRIGHT bursts had a 24-day mode over its whole window; cadence changes at sensor events such as the S1B failure (`meta/2026-09-01-bright-per-burst-cadence-probe`).
- **Radiometry.** The orbits of S1C and S1D match S1A's tube closely; their absolute calibration, noise floor and processor version were not shown to match. The records call an S1C- or S1D-only product "a separate product that shares a geometry, not a continuation of the S1A time series".

*In PONZI:* keep a per-track table of switch dates from the catalogue, and use the last acquisition actually on disk, not the last one catalogued: "S1A ends 2026-06-27" was quoted while the stores ended on 06-15 to 06-23 because 06-27 was never fetched.

## Anchor the series to one exact lattice

**Put acquisitions on one sensor's exact 12-day lattice with a tolerance of one day, and refuse any date that does not land on a slot. Never round a date into a slot.**

The first cross-sensor canary rounded dates to a 6-day grid. S1D to S1D pairs then landed in the same cells as the S1A to S1C bridge pairs: 188 collisions, and 9 of 15 bridge pairs lost. The fix anchors the lattice at the first acquisition of the backbone sensor on the track; a pair's cell is (slot of the later image, 12 x slots between them); dates more than a day off a slot are excluded and listed; a date that does not snap is an error at the writer. With it, all 20 Gaza stores were built, 15 with no collision and 5 with 7 or 8 resolved by the tie-break below (`meta/2026-09-28-...`, amendment A2).

**One function snaps, and it snaps where the value is used.** Pair lists store the raw interval; at least two older copies of the snapping arithmetic existed, and one consumer that did not snap made "a real 156-day gap" (`meta/2026-09-28-...`).

## At a switch, bridge the gap

**When one sensor hands over to another, admit the cross-sensor pairs that fill every baseline across the switch: 15 for five baselines (5 + 4 + 3 + 2 + 1). Admit them only around switches.**

- One bridge pair per switch left the cells after it empty; the amendment of 2026-09-29 admitted every cross-sensor pair with a snapped span of 12 to 60 days. The window is tested on the snapped span: 61 days snaps to 60 and is admitted (`meta/2026-09-28-...`, A1).
- Where the handover is not a multiple of 12 (Tehran: 7 days), one lattice excluded every S1D date and the series would have ended in June 2026. Bridge pairs were first refused (2026-10-07), then admitted two days later: the switch is one ordinary 12-day step on a global slot index, and the bridge pairs sit in cells 12 to 60 with real spans of 7, 19, 31, 43 and 55 days (`meta/2026-10-07-...`).
- **Store the truth beside the nominal slot.** The model asked for it: `span_days` and `is_bridge_pair` per (time, baseline), added without changing the existing arrays (`meta/2026-10-20-seam-bridge-span-days-flag`).

*In PONZI:* the forecast models should see the real span or mask bridge pairs, and the pyramid's [warm-up](detection.md#warm-up-and-the-clean-span) starts again after a switch: the first date of a new sensor has no pair, the second only the 12-day pair, and all five baselines exist only from the sixth date.

## Cells hold one pair

**Show that placing pairs into (time, baseline) cells is one-to-one, and keep a gate that refuses to write a store with a collision.**

S1C and S1D, one day apart, gave two later images x two earlier images = 4 distinct pairs in one cell. The gate stopped the write rather than overwrite silently, which was the right behaviour; letting the first pair win would have thrown away 3 of every 4 (`meta/2026-09-25-...`). On Colombia track 48 every one of the 53 stores in the AOI collided, and stores with collisions are refused as detector input (`colombia_eq_2026/2026-09-26-t48-zarr-detector-run`).

**When a real collision remains, choose the winner by a stated rule and count the losers:** closest raw span to the nominal one, then shortest perpendicular baseline, then date order. Put the rule in one function; the design document said one order and the writer did another, which would have picked a different winner in 4 of 9 cells (`meta/2026-09-28-...`, `meta/2026-10-02-incremental-store-append`).

**Sort tied candidates with a stable sort.** pandas' default sort is unstable, and pair sets built with a different numpy matched production on only 15 of 20 bursts (`meta/2026-10-02-...`).

**With a cap on pairs per date, adding a date can remove a pair.** Of 3,555 single insertions, 45 removed one, all in a switch window. So compare a new pair set with the one stored, never with one derived again (`meta/2026-10-02-...`).

## Choose the sensor policy once

**Decide up front how a store treats several sensors, because changing it later means rebuilding everything.**

In five days the design changed six times: an exact-timestamp axis (rejected), one store per platform (approved 09-25), a sensor axis (for Colombia, 09-26), one cross-sensor series (09-28), 15 pairs per switch (09-29), the exact lattice and S1A plus S1C only (09-30). One store per platform failed twice over: S1C and S1D each failed 60 of 72 Lebanon bursts, and on Colombia an S1D-only stack fell from 23 to 5 pairs, and its reference stack from 19 to 0 (`meta/2026-09-25-*`, `meta/2026-09-28-*`, `colombia_eq_2026/2026-09-26-...`).

## Baselines

- **Do not cap the perpendicular baseline for time-series pairs; store it for every pair.** A 150 m cap would have dropped about 20 % of S1A to S1C candidates, and 43 % of the fleet was multi-platform (`meta/2026-08-01-bright-coherence-fleet`, `meta/2026-09-28-...`).
- **Fix the requested baselines and check every slot is filled.** An axis built from the pairs that happen to exist hides the missing ones; two stores held one date and no 12 to 60 day pairs and still counted as delivered (`meta/2026-09-08-coherence-store-qaqc-done-contract`).
- **The first acquisition never appears** on an axis keyed by the later image of each pair; account for it by construction (`meta/2026-09-08-...`).
- **Pass the baseline set explicitly.** Omitting it fell back to another campaign's 30-slot default instead of the 5 slots requested (`meta/2026-09-04-majortom-v1-fullbatch-coherence-leg`).
- **Never write pair lists by hand;** use the selector. A hand specification ("all exact 60-day pairs") was an error (`colombia_eq_2026/2026-08-15-...`).
