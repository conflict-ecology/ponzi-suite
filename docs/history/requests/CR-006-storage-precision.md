# CR-006: storage precision of the run outputs (feature request, not decided)

- **Requested by / date:** owner, 2026-10-12
- **Status:** requested; to be decided before the v1 run profile

## Why
Earth observation products usually store packed integers with `scale_factor`, `add_offset` and `_FillValue` (Sentinel-2 and Landsat reflectance, MODIS indices). PONZI does this for the p-values only. The other stores are 32-bit floats.

## Candidates
| Output | Today | Candidate | Note |
| --- | --- | --- | --- |
| coherence store (the engine's, the largest) | float32 in 0 to 1 | uint8 (steps of 0.004) or uint16 | the estimate's noise is far larger; the engine's format, to agree with its owner; the largest saving |
| `difference`, `sensitivity`, `predicted_median` | float32 | int16, scale 0.0001 | no practical effect expected |
| `anomaly_score`, `ceiling_score` | float32 | int16, scale 0.001 | calibration ranks them against the null: rounding makes ties and moves p-values slightly |
| compact per-channel z (planned) | | int8, steps of 0.1 | already planned this way |

## Why not now
Rounding scores or coherence changes numbers. It belongs to a MAJOR version of the standard, with the panel nulls made under the same rounding; done now it would cut the link to the existing Gaza and Tehran runs and the registered calibrations.

## To do when taken up
Measure store sizes and the effect on p-values on one Tehran burst; write the precision of every variable into its contract; make packed storage the default of the v1 run profile.
