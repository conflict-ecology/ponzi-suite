# CR-032: the coherence chain in ponzi-pipeline (from repeat_ccd)

- **Requested by / date:** owner, 2026-10-23 (phase 5 of the overhaul plan; decisions D4 ISCE3 only, D5, D6 a clean slate, D8 the conda-forge stack, D9 a configurable burst grid, D10, D18 native grids)
- **Status:** implemented on the owner's instruction (2026-10-23), awaiting review; uncommitted (plan decision D10). Not yet run on real SLCs: that is the phase 0 reference on the HPC (D16)

## Why

A clean slate (D6) means PONZI makes its own coherence stores. The download and the ISCE3 processing come from repeat_ccd (author Corey Scher); what PONZI needs and repeat_ccd never did is the dense pyramid of pairs, one fixed grid per burst, and the coherence store (C1) with its engine report (C18).

## What changes

New in `ponzi-pipeline` (0.2.0):

| Module | Holds | From |
| --- | --- | --- |
| `config` | `CoherenceConfig`: backend, polarisation, platforms, revisit, baselines, pair tolerance, looks, window, the burst grid (`posting_m`, `buffer_m`; D9), the DEM; `config_hash` (BLAKE2b-16) | new |
| `bursts` | burst ids in the PONZI, OPERA and ASF spellings; `BurstMap` (the OPERA burst database: per burst its UTM zone and box); `burst_lattice` (the burst's fixed grid) | repeat_ccd `bursts.py` |
| `discover` | `search_asf`: the acquisitions of bursts over a span (ASF `SLC-BURST`, the parent SLC per hit) | repeat_ccd `bursts.search_bursts_asf` |
| `pairs` | the pyramid rule (every acquisition paired back by each baseline within the tolerance, one platform set and polarisation), the time axis, `add_bperp` | new; bperp from repeat_ccd |
| `orbits` | `.EOF` parsing, Lagrange interpolation, the perpendicular baseline, picking and downloading orbit files from ASF S1QC | repeat_ccd `baselines.py`, `asf.py` |
| `acquire` | SLC downloads through `asf_search` under an NFS-safe lock, the Earthdata session from the environment, orbit files | repeat_ccd `asf.py`, `auth.py` (ASF only) |
| `dem` | the ellipsoidal DEM over a burst's grid (`dem_stitcher`), cached | repeat_ccd `prepare_dem` |
| `coherence.estimator` | NaN-aware multilook and Gaussian window | repeat_ccd `_compute_coherence`, on the bytes |
| `coherence.isce3` | topo, coregistration, interferogram, geocoding onto the burst lattice, COG output | repeat_ccd `isce3_coh.py`, the per-burst route |
| `engine` | the engine's own checks (C18 engine rows) and its report, independent of `ponzi.contracts.validate` | new |
| `assemble` | pair rasters into `{burst}.coh.zarr` via `.partial`, the engine report, `_complete` | new |
| `work`, `cli` | the burst work folder; `ponzi-pipeline discover`, `pairs`, `acquire`, `dem`, `coherence`, `assemble` | new |

The one change to repeat_ccd's processing: every pair of a burst is geocoded onto the burst's fixed grid (its UTM zone from the burst map, edges on multiples of the posting), not onto each pair's own bounding box in the DEM's system. Not ported: Earth Engine (owner), the CDSE route (`search_bursts_cdse`, the CDSE downloads; a follow-up), the other backends (SNAP, HyP3, ISCE2, BUD, CSLC; D4), the SLURM orchestration (the worker's, phase 8).

`ponzi`: `ponzi.contracts.coherence.CoherenceWriter`, a coherence store written one acquisition at a time in the format of `write_coherence_store` (which is unchanged). `ponzi-models`: `panels.cells.bursts_for_cells` and `ponzi-models panel-cells --burst-map` (the bursts that cover a panel's cells).

The pixi environment `isce3` (its own solve group; the other environments' locks are unchanged): isce3 0.25, s1reader 0.2.5, COMPASS, dem_stitcher, GDAL 3.13, asf_search 14.

A finding, fixed: rasterio's COG driver opened for writing wrote NaN as 0 with GDAL 3.13 and rasterio 1.5.1 (the `isce3` environment), which would have turned missing coherence into coherence 0. `write_cog` writes a tiled GeoTIFF in memory and copies it with GDAL's COG driver; a regression test holds it.

## Do results change?

No result of `ponzi` changes. The stores are new (D6).

## Tests

`packages/pipeline/tests/test_coherence_chain.py` (no network, no ISCE3): the config; burst ids and a burst map; orbit interpolation against an analytic orbit (below a millimetre) and the baseline of a twin orbit; orbit picking and download through a faked session; the pyramid rule (gaps, other platforms and polarisations, the tolerance); discovery and acquisition through a faked `asf_search`; the estimator equal on the bytes to a verbatim copy of repeat_ccd's and recovering a known coherence; assembly into a store that passes `ponzi validate-store` with the engine report agreeing (an empty pair undeclared, the counts, the footprint), a raster off the grid refused; the stage commands; the COG regression. `test_isce3_backend.py` (`-e isce3`): every ISCE3 and s1reader API the port calls, with its arguments. `pixi run test-pipeline`: 76 passed and the ISCE3 module skipped; `pixi run -e isce3 test-pipeline`: 79 passed.

## Version

`ponzi-pipeline` 0.2.0. `ponzi`: MINOR (an addition to the contract module), part of 0.3.0. Standard: a standard names its coherence config.
