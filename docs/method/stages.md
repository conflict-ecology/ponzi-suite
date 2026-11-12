# Stages

A stage is one replaceable unit of work with a fixed interface (`ponzi_spec.stages.StageSpec`):

| Field | Meaning |
| --- | --- |
| `name` | the stage; it has no version ([Versions](../reference/versions.md#stages-the-majors-of-their-code)) |
| `inputs` | role → Collection, e.g. `{coherence: ponzi-coherence, sidecar: ponzi-sidecar}` |
| `outputs` | role → Collection |
| `identity_params` | a pydantic model, hashed into the content id |
| `request_params` | a pydantic model, recorded but never hashed |
| `resources` | cpus, memory, GPUs, walltime, environment (`default`, `ml`, `ml-gpu`, `isce3`) |
| `fan_out` | how the worker splits the stage into tasks: `per_pair`, `per_burst`, `per_path` |
| `code` | the distributions whose code computes it; their majors enter the content id ([Content ids](../using/content-ids.md)) |

An implementation is an object with a `spec` and a `run(inputs, params, request, workdir)` method, registered under the entry point group `ponzi.stages`. The worker finds every installed stage with `discover_stages()`, so a new or replacement stage is a package that registers a name, with no change to the worker.

## The stages of the S1 workflow

The stages ponzi-worker registers, each a thin adapter over the distribution named:

| Stage | From | To | Over |
| --- | --- | --- | --- |
| `discover` | a burst id and span (ASF search) | `ponzi-pairs`: the acquisitions and their pyramid pairs | ponzi-pipeline |
| `dem` | the burst's box | `ponzi-dem` | ponzi-pipeline |
| `coherence` | `ponzi-dem`, `ponzi-pairs` (one job per pair; it downloads the pair's SLCs and orbits) | `ponzi-coherence-pair` | ponzi-pipeline |
| `assemble` | `ponzi-pairs`, `ponzi-coherence-pair` | `ponzi-coherence`, with the engine report | ponzi-pipeline |
| `ingest-coherence` | a coherence store made elsewhere | `ponzi-coherence` | ponzi-worker |
| `onboard` | `ponzi-coherence` | `ponzi-sidecar` | ponzi-pipeline |
| `run` | `ponzi-coherence`, `ponzi-sidecar`; the model through the scoring spec | `ponzi-run` | ponzi |
| `ingest-calibration` | a calibration file | `ponzi-calibrations` | ponzi-worker |
| `pvalues` | `ponzi-run`, `ponzi-calibrations` | `ponzi-pvalues` | ponzi |
| `detect` | `ponzi-pvalues`, `ponzi-run` | `ponzi-events` | ponzi |
| `tile` | `ponzi-pvalues`, `ponzi-run` | `ponzi-events-cell`, one per Major TOM cell | ponzi |

`ponzi-pipeline`'s own commands split the chain further (`pairs` and `acquire` apart from `discover` and `coherence`, [Coherence](coherence.md)); `ponzi-worker stages` lists the stages installed.

A workflow is an ordered list of steps, each a stage with its inputs and params; `ponzi-models standard-workflow` builds the one a standard runs ([Making a standard](../models/standards.md#from-bundle-to-server)). To add a stage, see [A new stage](../contributing/new-stage.md).

The panel stages (`panel-cells`, `panel-masks`, `panel-assemble`) are described in [Panels](panels.md).
