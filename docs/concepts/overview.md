# System overview

## The data chain

```
Sentinel-1 SLCs (ASF, CDSE)
  → pair coherence per burst (ISCE3)            ponzi-pipeline
  → coherence store per burst (Zarr)            ponzi-pipeline
  → covariates sidecar (weather, built-up)      ponzi-pipeline
  → forecast run: scores and changes            ponzi
  → p-values under a calibration                ponzi
  → dated events under a detection recipe       ponzi
```

Models and calibrations are made by `ponzi-models` from panels: sets of pixels of many bursts, run through the same chain.

## The components

```
                ponzi-server  ◄──── REST ────  ponzi-client  ◄── ponzi-visual, agents
                     ▲
                     │ REST (the worker always asks; the server never calls out)
                ponzi-worker  ── runs ──►  ponzi, ponzi-pipeline, ponzi-models
                     │
                     └── locally, or through SLURM, or in a container
```

- **ponzi-server** holds requests, watched areas, jobs and the final outputs, and serves the catalog. It never imports the computing distributions.
- **ponzi-worker** claims jobs from the server, runs the stages directly or through SLURM, keeps intermediate outputs in its own cache, and uploads only the final outputs.
- **ponzi-client** (Python, and the `ponzi-client` command) is the only way to use the system from code. The front end has its own TypeScript client, generated from the server's committed OpenAPI document.
- **ponzi-visual** shows bursts, watched areas and events on a map, and adds bursts to the watched areas.

## What holds it together

- Every artifact that crosses a component boundary is a STAC Item in a known Collection: the [STAC profile](stac-profile.md).
- Every Item has a [content id](content-ids.md) computed before the work runs, so repeated requests reuse what exists.
- Every final output has a [manifest](manifests.md) that traces it back to the satellite scenes.
- Every unit of work is a [stage](stages.md) with declared inputs, params and outputs, so it can be replaced.
