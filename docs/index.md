# PONZI

PONZI (Pyramid Of Normalised Z-score Indicators) detects surface disturbance from Sentinel-1 SAR coherence time series. For every burst it forecasts the coherence each new acquisition should have, scores how far the observed coherence falls below the forecast, turns the scores into calibrated p-values, and dates the changes as surface disturbance events.

The system is four repositories:

| Repository | Distributions | Role |
| --- | --- | --- |
| [ponzi-core](https://github.com/conflict-ecology/ponzi-core) | `ponzi-spec`, `ponzi`, `ponzi-pipeline`, `ponzi-models` | everything that computes: shared schemas, the algorithm, data acquisition and coherence processing, training and calibration |
| [ponzi-service](https://github.com/conflict-ecology/ponzi-service) | `ponzi-server`, `ponzi-worker`, `ponzi-client` | the REST service, the job runner and the clients |
| [ponzi-visual](https://github.com/conflict-ecology/ponzi-visual) | `ponzi-visual` | the map front end |
| [ponzi-suite](https://github.com/conflict-ecology/ponzi-suite) | this site | documentation for people and agents, and the files PONZI runs from: panels, forecasters, run configs, test cases |

!!! note "Status"
    The system is being rebuilt as packages (the overhaul). Available now: `ponzi-spec` 0.1.0, the `ponzi` library (with STAC Items for its stores and models named by registry reference) `ponzi-pipeline` 0.2.0 (the coherence chain and the onboarding of a store) and `ponzi-models` 0.1.0 (panels, training, calibration, the registry, standards). Pages for the parts still to come say which phase brings them.

Start with [how PONZI works](concepts/workflows.md) and the [system overview](concepts/overview.md). Agents start at [For agents](agents/index.md).
