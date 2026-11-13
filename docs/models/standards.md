# Building a standard

A standard is a bundle: a model, its scoring spec hash, its calibrations, and the panel, detection, onboarding and coherence specs it names, in one file `standards/<id>.yaml`. Its version is its content hash, and watched areas and run requests name it as `<id>@<hash8>`, or by its id when the server holds one version (CR-089). How it is versioned, written (`new-standard`, `register-standard`) and tracked by the server is in [Standard versions](versions.md).

## On the CPU, on local disk (the rehearsal)

```
cd ponzi-core
# a tiny fit of the default, TiDE, about 10 s
pixi run -e ml ponzi-models rehearse --out /tmp/rehearsal
# no torch
pixi run ponzi-models rehearse --out /tmp/rehearsal-r --model rolling
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

- **The id:** `<sensor>-<scope>`, its sensor the model card's ([Naming rules](naming.md)).
- **The specs:** each it names, as `name` or `name@<hash>` (`new-standard` writes the latter), is found: the home, then the suite, then the registry's archive for a version (ponzi-core CR-083).
- **The registry:** the model, its artifact by reference when it has one, its scoring spec, and the calibrations, each made for that scoring spec on the standard's panel spec. A trained model was trained on that panel spec (the same hash).
- **The panel:** with the built panel in the home, no training or validation cell of the model is a test cell of the panel, the calibrations' null.
- **`requires`:** the installed distributions meet it. A worker also refuses a job of a standard whose `requires` its own versions do not meet.
- **The version before it:** the latest registered version, else `--previous FILE`; what the change means (`run`, `products` or `other`) is reported, never refused ([What a change means](versions.md#what-a-change-means)).
- **Drafts:** a draft (`status: draft`) is checked for its form and its specs only, and `standard-workflow` refuses it. The general standard, ponzi-suite `standards/s1-general.yaml`, is a draft.

Its registry (`<out>/registry`) and its standard `s1-rehearsal` (`<out>/standards/s1-rehearsal.yaml`, registered with `--allow-uncommitted`, since its specs are written into `<out>` and are in no ponzi-suite commit) behave like real ones, and the worker runs them. `<out>` is the rehearsal's home for its specs: a command run with `PONZI_HOME=<out>` finds them (CR-088).

## From bundle to server

```
pixi run ponzi-models standard-workflow STANDARD.yaml --registry REGISTRY \
    --source pipeline --set burst_map=... --set slc_dir=... \
    --set orbit_dir=... --set dem_dir=... --set start_date=2025-01-01
```

The standard must be registered first: its workflow is recorded beside it in the registry, once per source, and every later build must match ([One key, one workflow](versions.md#one-key-one-workflow)). This writes the standard as the server runs it, by default to `$PONZI_HOME/standards/<id>@<hash8>.yaml` where the server of that home reads it (`--out` names any file; for another home, set `PONZI_HOME`; CR-080, CR-088), with the `specs:` block of every spec it names and of the bundle. `burst_map`, `slc_dir`, `orbit_dir`, `dem_dir`, `ghsl_dir` and `era5_dir` can be left out: a worker fills those it is not given from its PONZI home (`$PONZI_HOME/catalog/` and `downloads/`, on the cold tier when one is set, CR-099). The steps are:

1. The coherence chain, either way:
    - `--source pipeline`: `discover`, `dem`, `coherence` (one job per pair), `assemble`;
    - `--source stores`: `ingest-coherence` of stores made elsewhere.
2. `onboard`, with the onboarding spec's fields.
3. `run`, a staged run with the Et summary.
4. `ingest-calibration`.
5. `pvalues`.
6. `detect`, with the detection spec's fields.
7. `tile`, the same.

The file's `final` is `[cells]`: a job delivers the `tile` step's `ponzi-events-cell` Items only, and `detect`'s per-burst events stay in the worker's cache (CR-100).

Unless it was written there, copy the file into the server's `$PONZI_HOME/standards/` and restart the server; `ponzi-client standards` then lists it ([how the server reads it](versions.md#two-files-for-one-version)).

The open work for the first real standard is on the [roadmap](../contributing/roadmap.md#phase-8b-the-first-standard).
