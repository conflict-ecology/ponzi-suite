# A new model

From a fit spec to a model watched areas run, with the command `ponzi-models` (`ponzi-models --help` lists the stages).

1. **Change request**, with the evidence the model is meant to improve on.
2. **Fit spec** in ponzi-suite `forecasters/<family>/` (a variant in `candidates/`), named by the [naming convention](../reference/naming.md): window (context, horizon, baselines, quantile levels), covariate channels, sizes, optimiser, stopping, treatment of missing values, augmentation. Unknown keys are refused.
3. **Panel**: a set of pixels of many bursts, defined by mask layers on full coherence stores. Training, calibration and production read the panel through the same opener, so a training window is byte for byte the window inference builds.
4. **Prepare, train, export** (`ponzi-models prepare`, `train`, `export`): the prepared files are identified by a digest of what they depend on; training keeps the epoch with the lowest validation loss; export writes the TorchScript artifact and its `meta.json`.
5. **Register** (`ponzi-models register-model`) the model, its id `<forecaster>--<panel>-<version>` (the name `export` gives the artifact) as a `ponzi-models` Item (with the `mlm` extension): the artifact by its digest and the run config it runs with. Configs refer to the model as `registry:<model id>@sha256:<digest>` (`ModelEntry.ref`), never by path; the run resolves it through the registry and checks the digest.
6. **Null and calibrate** (`ponzi-models null-runs`, `null-rows`, `calibrate`, `register-calibration`): run the registered model over the panel's test bursts; build the calibrations (plain and ceiling) from those runs. For staged runs (CR-021), `null-runs --staged` and `calibrate-staged` build the staged (format 3) pair instead. A calibration is bound to one run config hash and one major version of `ponzi`.
7. **Benchmark** against the current standard. A model joins a standard only after the benchmark.
8. **Standard** (`data/standards/<id>-<version>.yaml`, checked with `ponzi-models check-standard`): a new standard version names the model, its run config, its calibrations, the detection recipe and the workflow.
