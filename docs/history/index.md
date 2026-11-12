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

## Decision log

The library's earlier decisions are in the monorepo's `docs/decisions.md` and in the change requests below (CR-000 onward).

## Change requests

Nothing in ponzi-core changes without a written request the owner signs off. The requests are kept here (`docs/history/requests/`, since CR-071; the form is [TEMPLATE.md](requests/TEMPLATE.md)). Several also change ponzi-service, ponzi-visual or this suite. A request that no longer applies, because a later one replaced or removed what it did, says so on a `Stale` line under its status; one that applies only in part says what no longer holds on a `Superseded in part` line. The table shows both.

<!-- ponzi:requests -->
