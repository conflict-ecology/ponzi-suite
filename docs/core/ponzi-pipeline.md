# ponzi-pipeline

The inputs of a run: from a burst id to its coherence store and the covariates beside it. It finds and downloads the Sentinel-1 scenes, computes coherence with ISCE3, assembles the store, and onboards it with weather, built-up and the process mask.

| Part | What it does | Explained in |
| --- | --- | --- |
| `discover`, `pairs` | a burst's acquisitions from ASF, and the pyramid pairs between them | [Making coherence stores](../method/coherence.md#a-bursts-series) |
| `acquire`, `orbits`, `dem` | the SLCs, orbit files and DEM a burst needs | [Data sources and catalogs](../method/data-sources.md#fetched-by-the-worker-per-job) |
| `coherence`, `engine`, `assemble` | one pair's coherence with ISCE3, then the burst's store with the engine's checks | [Making coherence stores](../method/coherence.md#one-pair) |
| `onboard` | the store's sidecar (weather, built-up, land, pair differences, mask) and pixel sample, by an onboarding spec | [Data sources and catalogs](../method/data-sources.md#era5-land-weather) |
| `bursts`, `catalog` | the OPERA burst map, and the burst catalog the server reads | [Data sources and catalogs](../method/data-sources.md#the-burst-catalog) |

## The `ponzi-pipeline` command

```
ponzi-pipeline discover | pairs | acquire | dem | coherence | assemble   # the coherence chain, step by step
ponzi-pipeline onboard ...                                              # a store's sidecar and sample
ponzi-pipeline weather-prefetch ...                                     # the shared weather download
ponzi-pipeline burst-catalog [--source FILE]                            # the burst catalog in the home
```

`ponzi-pipeline` with no argument lists the commands. The coherence chain's options are in [Making coherence stores](../method/coherence.md#commands). Under a server, the worker runs the same code as its `discover`, `dem`, `coherence`, `assemble` and `onboard` stages ([Stages](../method/stages.md)).

Its [API reference](../reference/api/ponzi-pipeline.md) is generated from its docstrings.
