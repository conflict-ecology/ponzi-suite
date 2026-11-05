# Making a standard

A standard is a versioned bundle: a model, its run config hash, its calibrations, a detection recipe, the onboarding and the coherence config. Watched areas and run requests name it as `<id>@<version>`.

## On the CPU, on local disk (the rehearsal)

```
cd ponzi-core
pixi run -e ml ponzi-models rehearse --out /tmp/rehearsal               # a tiny TiDE fit, about 10 s
pixi run ponzi-models rehearse --out /tmp/rehearsal-r --model rolling    # no torch
```

The rehearsal runs the functions of the real lifecycle on the synthetic world (`ponzi_models.synthetic`):

| Step | Function | At scale (HPC) |
| --- | --- | --- |
| Bursts and panel | `synthetic.build_panel` | `ponzi-models panel-cells`, `panel-build` on ISCE3 stores |
| Prepare, train, export | `training.prepare`, `train.train_fit(device="cpu")`, `export.export_fit` | `prepare`, `train` on `ceoas-gpu`, `export` |
| Register | `register_model.register` | `register-model` |
| Null | `null_runs.run_burst` on the test bursts, both layers | `null-runs` (an array job) |
| Calibrate | `null_rows.collect`, `build.build`, `register_calibration.register` | `null-rows`, `calibrate`, `register-calibration` |
| Bundle | `Standard(...).check(registry)` | `check-standard` |

Its registry (`<out>/registry`) and its standard (`<out>/standards/`) behave like real ones, and the worker runs them.

## From bundle to server

```
pixi run ponzi-models standard-workflow STANDARD.yaml --registry REGISTRY --out s1-general.yaml \
    --source pipeline --set burst_map=... --set slc_dir=... --set orbit_dir=... --set dem_dir=... \
    --set start_date=2025-01-01
```

This writes the standard as the server runs it. The steps are:

1. The coherence chain, either way:
    - `--source pipeline`: `discover`, `dem`, `coherence` (one job per pair), `assemble`;
    - `--source stores`: `ingest-coherence` of stores made elsewhere.
2. `onboard`.
3. `run`, a staged run with the Et summary.
4. `ingest-calibration`.
5. `pvalues`.
6. `detect`.
7. `tile`.

Copy the file into the server's `standards` folder and restart the server. `ponzi-client standards` then lists it.

The open work for the first real standard is on the [roadmap](../contributing/roadmap.md#phase-8b-the-first-standard).
