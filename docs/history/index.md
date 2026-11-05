# History

## The overhaul (from October 2026)

PONZI is being rebuilt from a set of repositories and scripts into four repositories of installable packages. The plan, with its decisions and phases, is the [overhaul plan](overhaul-plan.md); the state before it is the [baseline record](current-system.md).

What moves where:

| From | To |
| --- | --- |
| ponzi-models (training, calibration, registry) | `ponzi-models` in ponzi-core |
| repeat_ccd: Sentinel-1 search and download, burst map, baselines, DEM, ISCE3 coherence | `ponzi-pipeline` in ponzi-core |
| `ponzi.onboarding` | `ponzi-pipeline` |
| ponzi-apps: AOIs, campaigns, pages, HPC jobs | ponzi-server, standards, ponzi-visual, the worker's cluster profile |
| ponzi-paper: panel builders, labels, the config generator | `ponzi-models` |
| SLURM job files of ponzi-models and repeat_ccd | the worker's cluster profile |

Not carried over: Earth Engine (repeat_ccd's GEE ingest and CCD), repeat_ccd's other coherence backends (SNAP, HyP3, ISCE2, BUD, CSLC), and every store, model and calibration made before the overhaul. The new system starts on a clean slate and its first standard is trained and calibrated on ISCE3 coherence.

## Coherence methods

Why coherence is estimated in radar geometry, and how the backends repeat_ccd explored compared, will be written up from repeat_ccd's notes when `ponzi-pipeline` is built (phase 5).

## Decision log

The library's earlier decisions are in the monorepo's `docs/decisions.md` and in ponzi-core's change requests (`docs/requests/CR-000` onward); they move here as the overhaul proceeds.

## Change requests

Nothing in ponzi-core changes without a written request the owner signs off. The requests are kept in ponzi-core (`docs/requests/`) and rendered here at build time. Several also change ponzi-service, ponzi-visual or this suite.

<!-- ponzi:requests -->
