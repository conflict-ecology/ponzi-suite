# Stages

A stage is one replaceable unit of work with a fixed interface (`ponzi_spec.stages.StageSpec`):

| Field | Meaning |
| --- | --- |
| `name`, `version` | the stage and its identity version |
| `inputs` | role → Collection, e.g. `{coherence: ponzi-coherence, sidecar: ponzi-sidecar}` |
| `outputs` | role → Collection |
| `identity_params` | a pydantic model, hashed into the content id |
| `request_params` | a pydantic model, recorded but never hashed |
| `resources` | cpus, memory, GPUs, walltime, environment (`default`, `ml`, `ml-gpu`, `isce3`) |
| `fan_out` | how the worker splits the stage into tasks: `per_pair`, `per_burst`, `per_path` |

An implementation is an object with a `spec` and a `run(inputs, params, request, workdir)` method, registered under the entry point group `ponzi.stages`. The worker finds every installed stage with `discover_stages()`, so a new or replacement stage is a package that registers a name, with no change to the worker.

## The stages of the S1 workflow

| Stage | From | To | Distribution |
| --- | --- | --- | --- |
| `discover` | burst ids, span | `s1-slc` | ponzi-pipeline |
| `pairs` | `s1-slc` | `ponzi-pairs` | ponzi-pipeline |
| `acquire` | `s1-slc`, `s1-orbit` | local files in the worker cache | ponzi-pipeline |
| `dem` | burst footprint | `ponzi-dem` | ponzi-pipeline |
| `coherence` | SLCs, orbits, DEM, a pair | `ponzi-coherence-pair` | ponzi-pipeline |
| `assemble` | pair coherence of a burst | `ponzi-coherence` | ponzi-pipeline |
| `validate` | `ponzi-coherence` | a report | ponzi |
| `onboard` | `ponzi-coherence` | `ponzi-sidecar`, `ponzi-sample` | ponzi-pipeline |
| `run` | coherence, sidecar, model | `ponzi-run` | ponzi |
| `pvalues` | `ponzi-run`, calibration | `ponzi-pvalues` | ponzi |
| `detect` | `ponzi-pvalues`, `ponzi-run` | `ponzi-events` | ponzi |
| `tile` | `ponzi-events` | `ponzi-events-cell`, one per Major TOM cell | ponzi |

A workflow is an ordered list of stage references, named by a standard. To add a stage, see [A new stage](../contributing/new-stage.md).

The panel stages (`panel-cells`, `panel-masks`, `panel-assemble`) are described in [Panels](panels.md).
