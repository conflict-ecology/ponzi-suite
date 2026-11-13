# PONZI

PONZI (Pyramid Of Normalised Z-score Indicators) detects surface disturbance from Sentinel-1 SAR coherence time series. For every burst it forecasts the coherence each new acquisition should have, scores how far the observed coherence falls below the forecast, turns the scores into calibrated p-values, and dates the changes as surface disturbance events.

The system is four repositories:

| Repository | Distributions | Role |
| --- | --- | --- |
| [ponzi-core](https://github.com/conflict-ecology/ponzi-core) | `ponzi-spec`, `ponzi`, `ponzi-pipeline`, `ponzi-models` | everything that computes: shared schemas, the algorithm, data acquisition and coherence processing, training and calibration |
| [ponzi-service](https://github.com/conflict-ecology/ponzi-service) | `ponzi-server`, `ponzi-worker`, `ponzi-client` | the REST service, the job runner and the clients |
| [ponzi-visual](https://github.com/conflict-ecology/ponzi-visual) | `ponzi-visual` | the map front end |
| [ponzi-suite](https://github.com/conflict-ecology/ponzi-suite) | this site | documentation for people and agents, and the files PONZI runs from: training, scoring, panel, detection, coherence and onboarding specs, standards, test cases |

!!! note "Status"
    The system is being rebuilt as packages (the overhaul). Available now, in ponzi-core (`ponzi` tagged 0.1.2, the other three 0.0.1): `ponzi-spec` (the shared schemas, the API models, the PONZI home, composable yaml, naming), the `ponzi` library, `ponzi-pipeline` (the coherence chain and the onboarding of a store) and `ponzi-models` (panels, training, calibration, the registry, standards). In ponzi-service, `ponzi-server`, `ponzi-worker` and `ponzi-client`, whose own tags are not cut yet. Every version comes from git tags ([Versions](reference/versions.md)). What is left is on the [roadmap](contributing/roadmap.md).

Start with [how PONZI works](method/workflows.md) and the [system overview](getting-started/overview.md). Agents start at [For agents](contributing/agents/index.md).

## The site

| Section | For |
| --- | --- |
| [Getting started](getting-started/index.md) | what PONZI is made of, installing it, a first run on one machine, logins and keys, folders |
| [Concepts](method/index.md) | how the detection works, stages, content ids and reuse, provenance, watched areas (under construction), data sources, specs and the home |
| [ponzi-core](core/index.md) | ponzi-spec (the shared schemas, the STAC catalog profile); ponzi (grids, the store formats); ponzi-pipeline (making coherence stores); [ponzi-models](models/index.md) (training panels, models, standards) |
| [ponzi-service](service/index.md) | running the server, the clients (both under construction), workflows and the cache, running on SLURM, troubleshooting |
| [ponzi-visual](using/map.md) | using the map (under construction) |
| [Reference](reference/index.md) | versions, the glossary, citations |
| [Contributing](contributing/index.md) | the roadmap, the change process, adding a stage, and the guides for agents |
| [Discoveries](discoveries/index.md) | what the coherence engine's campaigns taught, for the system being built |
| [History](history/index.md) | the overhaul and the system before it |
