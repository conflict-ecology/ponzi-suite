# PONZI

PONZI (Pyramid Of Normalised Z-score Indicators) detects surface disturbance from Sentinel-1 SAR coherence time series. For every burst it forecasts the coherence each new acquisition should have, scores how far the observed coherence falls below the forecast, turns the scores into calibrated p-values, and dates the changes as surface disturbance events.

The system is four repositories:

| Repository | Distributions | Role |
| --- | --- | --- |
| [ponzi-core](https://github.com/conflict-ecology/ponzi-core) | `ponzi-spec`, `ponzi`, `ponzi-pipeline`, `ponzi-models` | everything that computes: shared schemas, the algorithm, data acquisition and coherence processing, training and calibration |
| [ponzi-service](https://github.com/conflict-ecology/ponzi-service) | `ponzi-server`, `ponzi-worker`, `ponzi-client` | the REST service, the job runner and the clients |
| [ponzi-visual](https://github.com/conflict-ecology/ponzi-visual) | `ponzi-visual` | the map front end |
| [ponzi-suite](https://github.com/conflict-ecology/ponzi-suite) | this site | documentation for people and agents, and the files PONZI runs from: panels, forecasters, run configs, standards, test cases |

!!! note "Status"
    The system is being rebuilt as packages (the overhaul). Available now, in ponzi-core: `ponzi-spec` 0.4.0 (the shared schemas, the API models, the PONZI home, composable yaml, naming), the `ponzi` library (its version comes from ponzi-core's git tags, the latest `v0.2.4`), `ponzi-pipeline` 0.2.0 (the coherence chain and the onboarding of a store) and `ponzi-models` 0.3.0 (panels, training, calibration, the registry, standards). In ponzi-service, `ponzi-server`, `ponzi-worker` and `ponzi-client` are at 0.1.0, not yet released. What is left is on the [roadmap](contributing/roadmap.md).

Start with [how PONZI works](method/workflows.md) and the [system overview](getting-started/overview.md). Agents start at [For agents](contributing/agents/index.md).

## The site

| Section | For |
| --- | --- |
| [Getting started](getting-started/index.md) | what PONZI is made of, installing it, a first run on one machine, logins, paths |
| [Using PONZI](using/index.md) | watching areas, the map, the clients, and reading the outputs |
| [The service](service/index.md) | the server, the worker, running on a cluster, configuration, the REST API, troubleshooting |
| [The method](method/index.md) | how the detection works: coherence, panels, grids, stages, and the data it is built from |
| [Models and standards](models/index.md) | making, versioning and naming standards and models |
| [Reference](reference/index.md) | the schemas and APIs generated from the code, the store contracts, terminology, citations |
| [Contributing](contributing/index.md) | the roadmap, the change process, new stages, and the rules for agents |
| [History](history/index.md) | the overhaul and the system before it |
