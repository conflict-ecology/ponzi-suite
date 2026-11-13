# Making coherence stores

PONZI makes its own coherence stores with `ponzi-pipeline`, an ISCE3 chain run burst by burst.

## A burst's series

- **Acquisitions**: the burst's, from ASF's burst search, of the configured platforms and polarisation, one per date.
- **Pairs** (the pyramid): for every acquisition, the pair reaching back by each of `baseline_days` (12 to 60 days), the earlier image within `pair_tolerance_days` of the date it should be. A missing acquisition leaves the pairs that need it empty.
- **Grid**: one fixed grid per burst, its UTM zone and box from the OPERA burst map, pixel edges on multiples of `grid.posting_m` (40 m by default). Every pair is geocoded onto it.

## One pair

1. The reference (the earlier image) burst's radar geometry over the DEM (Rdr2Geo), computed once and reused by every pair it is the earlier image of.
2. The secondary coregistered onto the reference radar grid (Geo2Rdr offsets, ResampSlc with the TOPS azimuth carrier).
3. The interferogram and both powers at full resolution.
4. Coherence: NaN-aware 10 x 2 multilook, then a NaN-aware Gaussian window (sigma 1, truncated at 2), `|<ifg>| / sqrt(<p1><p2>)`.
5. Geocoded onto the burst grid, written as a Cloud Optimized GeoTIFF.

## The store

`ponzi-pipeline assemble` writes the burst's coherence store (contract C1) one acquisition at a time as `.partial`, runs the coherence engine's own checks (C18), writes the engine report, renames the store and writes `_complete`. `ponzi validate-store` then checks it independently and compares with the engine's report.

## Commands

```
ponzi-pipeline discover  --burst ID --start DATE --end DATE [--work DIR]
ponzi-pipeline pairs     --burst ID [--work DIR]
ponzi-pipeline acquire   --burst ID [--work DIR] --burst-map FILE
ponzi-pipeline dem       --burst ID [--work DIR] --burst-map FILE
# in the isce3 environment
ponzi-pipeline coherence --burst ID [--work DIR] --burst-map FILE --index N
ponzi-pipeline assemble  --burst ID [--work DIR] --burst-map FILE [--out DIR]
```

`--work` defaults to `$PONZI_HOME/work/` (one folder per burst), `assemble --out` to the burst's own work folder (the SAR layer `<burst>.sar.zarr`, `<burst>.coh.zarr` before CR-102; CR-088), and the SLCs, orbits and DEM tiles go to `$PONZI_HOME/downloads/` (on the cold tier when one is set, and looked up in every tier first, CR-099) unless `--slc-dir`, `--orbit-dir` or `--dem-dir` say else (CR-079, CR-080). ISCE3's scratch goes to `$PONZI_HOME/tmp/` (CR-088).

All take `--coherence-spec NAME|FILE`, the coherence spec (looks, window, grid, DEM, platforms, baselines; `specs/coherence_specs/`, [Naming rules](../models/naming.md#spec-folders)), whose hash names the computation; without it, the code's defaults.
