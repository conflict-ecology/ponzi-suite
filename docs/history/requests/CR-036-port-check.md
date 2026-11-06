# CR-036: the port reference kit and the port check (decision D16)

- **Requested by / date:** owner, 2026-10-23 (D16 approved: the phase 0 HPC job)
- **Status:** implemented on the owner's instruction (2026-10-23), awaiting review; uncommitted (plan decision D10). Not yet run: the owner submits it from the HPC login node

## Why

Phase 5 checked the ISCE3 port on the laptop: the estimator matches repeat_ccd's on the bytes, and the ISCE3 calls are checked. Nobody has compared the full chain with repeat_ccd's on real SLCs.

`rccd-process-isce3` cannot serve as that reference as it stands. It deletes its per-burst outputs once it has merged them into a pair COG. It also geocodes each pair onto the pair's own bounding box in the DEM's system, while the port uses the burst's fixed grid (CR-032).

## What changes

| Where | Change |
| --- | --- |
| `packages/pipeline/reference/phase0/` (not in the wheel) | `pairs.csv` (one burst, one reference, five pyramid pairs); `port_reference.py` (repeat_ccd's own functions on that burst, every intermediate kept, `reference.json` with the sha256 of each file, the orbit files and the versions); `setup.sbatch`, `pairs.sbatch` and `check.sbatch` (partition and account `ceoas`, repeat_ccd's resources); `README.md` |
| `ponzi_pipeline.coherence.isce3` | `GeoGrid`, an output grid as ISCE3's geocoder takes it. `geocode` and `write_cog` take a `GeoGrid` or a `Lattice` (unchanged for a lattice) |
| `ponzi_pipeline.coherence.port_check` | `check(reference, work)`: the port on the reference's SLCs, orbit files and DEM, compared stage by stage (topo, coregistration, interferogram and powers, geocoding onto the reference's grid) on the bytes; `compare` |
| `ponzi-pipeline port-check` | the command; exits 1 when a stage differs |

The comparison uses the reference's own DEM and grid. The port's own DEM and grid are its deliberate changes, and the synthetic tests cover them.

## Do results change?

No. `geocode` and `write_cog` on a lattice are unchanged, and the COG regression test passes.

## Tests

`packages/pipeline/tests/test_port_check.py`:
- the comparison;
- `GeoGrid`, from a lattice and from a geographic GeoTIFF;
- the check against a synthetic reference with stand-ins for the ISCE3 functions, both equal and with the topo or the interferogram off;
- the kit (one burst, one reference, baselines 12 to 60 days that agree with the granule dates; the job files).

Every repeat_ccd function the driver calls binds to its arguments in the `isce3` environment (isce3 0.25.22, s1reader 0.2.5).

`pixi run test-pipeline`: 82 passed, 1 skipped.

## Version

`ponzi-pipeline` 0.2.0 (not yet released).
