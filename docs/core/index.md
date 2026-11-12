# ponzi-core

ponzi-core is the repository of everything that computes. It holds four Python distributions, each a layer on the one below it:

| Distribution | Command | What it does |
| --- | --- | --- |
| [ponzi-spec](ponzi-spec.md) | | the shared schemas every other part installs: content ids, the STAC profile, manifests, stages, the PONZI home, specs and naming, the REST API models |
| [ponzi](ponzi.md) | `ponzi` | the method: the forecast run, calibration to p-values, detection of events, and the store formats |
| [ponzi-pipeline](ponzi-pipeline.md) | `ponzi-pipeline` | the inputs of a run: Sentinel-1 search and download, ISCE3 coherence, the coherence store and its covariates |
| [ponzi-models](../models/index.md) | `ponzi-models` | what a watched area runs: panels, training, calibration, the registry and standards |

```
ponzi-spec  ◄──  ponzi  ◄──  ponzi-pipeline  ◄──  ponzi-models
```

- **One way only.** Each distribution imports only those to its left: `ponzi` never imports `ponzi_pipeline` or `ponzi_models`, and `ponzi_pipeline` never imports `ponzi_models` (held by ponzi-core's layering tests).
- **Light where it can be.** `ponzi-spec` needs only pydantic and PyYAML, so the server and the clients install it without the scientific stack. torch is an extra (`ponzi[tide]`, `ponzi-models[train]`), and ISCE3 comes only in the `isce3` environment ([Install](../getting-started/install.md)).
- **No data.** The code holds no specs, standards or results: the files PONZI runs from are in ponzi-suite, and everything computed goes in the [PONZI home](../service/configuration.md).
- **Versions.** Each distribution is released by its own git tags (`spec-v…`, `v…`, `pipeline-v…`, `models-v…`), and a new major of `ponzi` or `ponzi-pipeline` gives everything its code computes new content ids ([Versions](../reference/versions.md)).

Each distribution's section starts with what it holds and its commands, then the pages on its parts, then its API reference, generated from the code.

How the four work together, from the scenes to the events, is in [How PONZI works](../method/workflows.md); the service that runs them is [ponzi-service](../service/index.md).
