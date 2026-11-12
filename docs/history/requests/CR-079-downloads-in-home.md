# CR-079: every download kept once in the PONZI home

- **Requested by / date:** owner, 2026-11-12 ("the downloads should also be cached in PONZI_HOME")
- **Status:** signed off (2026-11-12), implemented (unreleased)

## Why
A worker already filled the SLC, orbit and DEM folders from its home's `downloads/` (CR-045). The onboarding's downloads were not there: with no folder given, the GHSL tiles and the CDS weather of a sidecar went inside that sidecar's cache entry, so they were downloaded again for every burst and kept inside the cache. The `ponzi-pipeline` commands put every download (SLCs, orbits, DEM, GHSL, weather) in their own work or output folder.

## What changes
- `ponzi_spec.home.Layout` gains `ghsl` (`downloads/ghsl/`) and `era5` (`downloads/era5/`), made with the rest.
- ponzi-worker: `home_variables` adds `ghsl_dir` and `era5_dir`, filled from the home when a job does not set them, like `slc_dir`.
- `ponzi-models standard-workflow`: the `onboard` step has the request `{ghsl_cache: ${ghsl_dir}, era5_cache: ${era5_dir}}`. A server's standard file is made again to take it.
- `ponzi-pipeline`: `acquire --slc-dir/--orbit-dir`, `dem --dem-dir`, `onboard --ghsl-cache/--era5-cache` and `weather-prefetch --cache` default to the home's `downloads/` folders instead of the work or output folder; `weather-prefetch --cache` is no longer required.
- The files are safe to share: a GHSL tile is named by its tile and product, a burst's weather month by the burst, the month and a digest of the request, a shared area's month by its key; each is written to a temporary name and renamed, the shared-area months under a lock.
- The pipeline tests each get their own PONZI home, as the worker's, server's and client's do, so no fake tile reaches a real home.

## Do results change?
No. The download folders are request parameters, never hashed: every content id is the same, and the bytes downloaded are the same wherever they are kept. Sidecars made before keep their downloads inside their entries.

## Tests
`test_home_catalog.py`: the layout's `downloads/ghsl` and `downloads/era5`. `test_commands.py`: `onboard` passes the home's folders unless given others. ponzi-worker `test_home.py`: the home's variables; `test_standard.py`: the `onboard` step's request, and a rehearsed standard run by a worker with a home; `test_watched.py`: the area's standard with the two variables.

## Deployment
A standard file made after this names `${ghsl_dir}` and `${era5_dir}`: a worker of before (without them in its home's variables) refuses its jobs as a missing variable, so the workers are updated before the server's standard files are made again.

## Version
Library: `ponzi-spec` minor, `ponzi-pipeline` minor (the defaults of the commands change), `ponzi-models` minor; ponzi-worker minor. Standard: no change.
