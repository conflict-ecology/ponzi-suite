# Making a standard

A standard is a versioned bundle: a model, its scoring spec hash, its calibrations, and the panel, detection, onboarding and coherence specs it names. Watched areas and run requests name it as `<id>@<version>`. How versions are numbered, written (`new-standard`, `bump-standard`, `register-standard`), checked and tracked by the server is in [Standard versions and naming](versions.md).

## On the CPU, on local disk (the rehearsal)

```
cd ponzi-core
pixi run -e ml ponzi-models rehearse --out /tmp/rehearsal               # a tiny fit of the default, TiDE, about 10 s
pixi run ponzi-models rehearse --out /tmp/rehearsal-r --model rolling    # no torch
```

The rehearsal runs the functions of the real lifecycle on the synthetic world (`ponzi_models.synthetic`):

| Step | Function | At scale (HPC) |
| --- | --- | --- |
| Bursts and panel | `synthetic.build_panel` | `ponzi-models panel-cells`, `panel-build --panel-spec` on ISCE3 stores |
| Prepare, train, export | `training.prepare`, `train.train_fit(device="cpu")`, `export.export_fit` | `prepare`, `train` on the cluster's GPU partition (the site file's `gpu` role), `export` |
| Register | `register_model.register` | `register-model` |
| Null | `null_runs.run_burst` on the test bursts, both layers | `null-runs` (an array job) |
| Calibrate | `null_rows.collect`, `build.build`, `register_calibration.register` | `null-rows`, `calibrate` (for staged runs, `calibrate-staged` on `null-runs --staged`), `register-calibration` |
| Bundle | `versions.new`, `versions.register` (the standard `s1-rehearsal`) | `new-standard`, `check-standard`, `register-standard` |

The checks of a standard (ponzi-core CR-055):

- **The id:** `<sensor>-<scope>`, its sensor the model card's ([Naming](naming.md)).
- **The specs:** each name it gives is found (the home, then the suite) and has the hash its name was first used with in the registry (`specs.json`). Spec fields given inline are refused.
- **The registry:** the model, its artifact by reference when it has one, its scoring spec, and the calibrations, each made for that scoring spec on the standard's panel spec. A trained model was trained on that panel spec (the same hash).
- **The panel:** with the built panel in the home, no training or validation cell of the model is a test cell of the panel, the calibrations' null.
- **`requires`:** the installed distributions meet it. A worker also refuses a job of a standard whose `requires` its own versions do not meet.
- **The version before it:** the latest registered version, else the previous one beside the file. Within a major, nothing that changes the runs may change (workflow, coherence and onboarding specs, panel spec, model, scoring spec). Within a minor, only the description, `requires` and the status.
- **Drafts:** a draft (`status: draft`) is checked for its form and its specs only, and `standard-workflow` refuses it. The general standard, ponzi-suite `standards/s1-general-2.0.0.yaml`, is a draft.

Its registry (`<out>/registry`) and its standard `s1-rehearsal@1.0.0` (`<out>/standards/`, registered with `--allow-uncommitted`, since its specs are written into `<out>` and are in no ponzi-suite commit) behave like real ones, and the worker runs them. `<out>` is the rehearsal's home for its specs: a command given `--home <out>` finds them.

## From bundle to server

```
pixi run ponzi-models standard-workflow STANDARD.yaml --registry REGISTRY --out s1-general-2.0.0.yaml \
    --source pipeline --set burst_map=... --set slc_dir=... --set orbit_dir=... --set dem_dir=... \
    --set start_date=2025-01-01
```

This writes the standard as the server runs it, with the `specs:` block of every spec it names and of the bundle. `burst_map`, `slc_dir`, `orbit_dir` and `dem_dir` can be left out: a worker fills those it is not given from its PONZI home (`$PONZI_HOME/catalog/` and `$PONZI_HOME/downloads/`). The steps are:

1. The coherence chain, either way:
    - `--source pipeline`: `discover`, `dem`, `coherence` (one job per pair), `assemble`;
    - `--source stores`: `ingest-coherence` of stores made elsewhere.
2. `onboard`, with the onboarding spec's fields.
3. `run`, a staged run with the Et summary.
4. `ingest-calibration`.
5. `pvalues`.
6. `detect`, with the detection spec's fields.
7. `tile`, the same.

Copy the file into the server's `standards` folder (`$PONZI_HOME/standards` by default) and restart the server. `ponzi-client standards` then lists it.

The open work for the first real standard is on the [roadmap](../contributing/roadmap.md#phase-8b-the-first-standard).
