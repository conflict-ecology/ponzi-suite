# Naming

Specs, models and standards have names a person can read: lowercase words joined by hyphens, from the general to the specific. A name says what the thing is. How it is versioned and where it came from are written in the file, never in the name: no version, date, sensor, seed or abbreviation code (`c30`, `pdcompact`, `f1p`, `mt0.4`). The one exception is a standard's sensor (below).

The rules are code, `ponzi_spec.naming` (ponzi-core CR-052, CR-070), and ponzi-core's tests hold every file of this repository to them (`test_suite_names.py`).

| What | Name | Example | Where it sits |
| --- | --- | --- | --- |
| panel spec | `<design>-<scope>[-<change>]` | `majortom-global` | `panel_specs/majortom-global/`; built: `$PONZI_HOME/panels/majortom-global/` |
| training spec | `<family>-<inputs>` | `tide-weather` | `training_specs/tide/weather.yaml` |
| variant | `<training spec>-<change>...` | `tide-weather-fill-median` | `training_specs/tide/candidates/fill-median.yaml` |
| test case's training spec | `<training spec>-<case>-<change>` | `tide-weather-gaza-finetune` | `testcases/gaza/training.yaml` |
| fit at another seed | `<training spec>-seed<N>` | `tide-weather-fill-median-seed43` | `ponzi-models train --seed 43` |
| model | `<training spec>--<panel spec>` | `tide-weather--majortom-global` | the artifact `export` writes, the registry entry |
| scoring spec | `<forecaster>-<scoring>[-<change>]` | `rolling-ols-pyramid` | `scoring_specs/rolling-ols-pyramid.yaml` (CR-058) |
| coherence spec | `<backend>-<window>[-<change>]` | `isce3-gaussian` | `coherence_specs/isce3-gaussian.yaml` |
| onboarding spec | `<steps>[-<change>]` | `all-steps`, `mask-only` | `onboarding_specs/all-steps.yaml` |
| detection spec | `<method>[-<change>]` | `single-path`, `single-path-loose` | `detection_specs/single-path.yaml` |
| standard | `<sensor>-<scope>` | `s1-general`, `s1-gaza` | `standards/s1-general-2.0.0.yaml`; cited `s1-general@2.0.0` |

A word is letters and digits, and a name starts with a letter. The double hyphen of a model id separates its two names, since each may hold single hyphens. A model id has no `@`, because a registry reference already uses it: `registry:tide-weather--majortom-global@sha256:<digest>`.

A spec has no version: it is known by its name and its content hash, and a changed spec is a new name, the old one with its change added (`majortom-global-dense`). The name is a label, not part of the hash ([Standard versions and naming](versions.md#specs-a-name-and-a-hash)).

A standard's id is its sensor and its scope, both listed in `ponzi_spec.naming` (`SENSORS`, `SCOPES`, `TESTCASES`). The sensor is the one exception to "no sensor in a name": a standard runs one sensor's data, and its model card names the same sensor. `check-standard`, `register-standard` and the suite's tests refuse any other form. Its version is not in the id: it is cited as `<id>@<version>`.

## Spec folders

A spec is a file a person writes, validated by PONZI, that says how something is made; its content enters the identity of what it makes. There are six kinds (`ponzi_spec.specs.SPEC_KINDS`). ponzi-suite keeps them under git, and the PONZI home holds working copies, in folders of the same plural name:

| Spec | Says how this is made | Folder (suite and home) |
| --- | --- | --- |
| training spec | a trained model | `training_specs/<family>/<inputs>.yaml`, `candidates/` |
| scoring spec | the runs of a model over a burst | `scoring_specs/<name>.yaml` |
| panel spec | a built panel | `panel_specs/<id>/` (`panel.yaml` and its two geojson) |
| detection spec | the events and cells from p-values | `detection_specs/<name>.yaml` |
| coherence spec | a burst's coherence store | `coherence_specs/<name>.yaml` |
| onboarding spec | a store's sidecar and pixel sample | `onboarding_specs/<name>.yaml` |

A command takes a spec as `--<kind>-spec NAME|FILE` (`--training-spec`, `--scoring-spec`, `--panel-spec`, `--detection-spec`, `--coherence-spec`, `--onboarding-spec`). A path is taken as it is. A name is looked up in the home's folder first, then in the suite's (`$PONZI_SUITE`, else the `ponzi-suite` checkout beside ponzi-core), by `ponzi_spec.specs.find_spec`; a training spec is also found by its `training_id`. The keys inside a spec's file are its content. The standard, the model, the calibration, the built panel, the workflow, the site file, the cluster profile and the server settings are not specs.

## Words in use

- **Designs** (panel specs): `majortom`, cells of the Major TOM grid.
- **Scopes** (panel specs): `global`.
- **Families** (training specs): `tide`, the default today; a new forecaster brings its own family word.
- **Inputs** (training specs): `weather`, the weather levels (soil moisture, snow depth, snow cover) and the compact set of their pair differences.
- **Scorings** (scoring specs): `pyramid`, the 15-pair pyramid over baselines of 12 to 60 days and a horizon of 5. A scoring spec's forecaster part is the forecaster it runs (`rolling-ols`, `tide-weather`).
- **Backends and windows** (coherence specs): `isce3-gaussian`, ISCE3 with 10 by 2 looks, the Gaussian window and a 40 m posting.
- **Steps** (onboarding specs): `all-steps` (built, weather, pairdiff, mask and sample); `<step>-only` for one step.
- **Methods** (detection specs): `single-path`, the flags of one calibration, dated by Et.
- **Sensors** (standards): `s1`, later `nisar`.
- **Scopes** (standards): `general`; `rehearsal`, for the lifecycle rehearsal and the demo; a test case's name (`gaza`).
- **Changes** (variants): `fill-<how>`, how a missing coherence is given to the model (`constant`, `median`, `previous`, `sentinel`, with `no-flags` when the obs flags are left out); `augmented`, the general training augmentation; `context-dropout`; `radar-moisture`, the Sentinel-1 moisture covariate; `finetune`.

Add a word here when a new one is needed, so the same thing is always called the same.

## Former names

Every training spec renamed by CR-052 keeps its old id as `formerly:`, so the fits, artifacts and registry entries made under it can still be found:

| Name | Formerly |
| --- | --- |
| `tide-weather` | `tide_c30_pdcompact` |
| `tide-weather-fill-constant` | `tide_c30_pdcompact_constant` |
| `tide-weather-fill-median` | `tide_c30_pdcompact_median` |
| `tide-weather-fill-previous` | `tide_c30_pdcompact_previous` |
| `tide-weather-fill-previous-augmented` | `tide_c30_pdcompact_previous_aug` |
| `tide-weather-fill-previous-augmented-radar-moisture` | `tide_c30_pdcompact_previous_aug_s1` |
| `tide-weather-fill-previous-context-dropout` | `tide_c30_pdcompact_previous_cd` |
| `tide-weather-fill-sentinel` | `tide_c30_pdcompact_sentinel_flag` |
| `tide-weather-fill-sentinel-no-flags` | `tide_c30_pdcompact_sentinel` |
| `tide-weather-gaza-finetune` | `tide_c30_gaza_f1p` |
| `rolling-ols-pyramid` (scoring spec) | `exp_b5h5_base` |

Models registered before keep their names (`tide_c30_pdcompact_mt0.4`, `tide_s1_mt04`); the headers of the specs refer to them as they were registered.

CR-070 renamed the files a person writes to specs (fit spec to training spec, run config to scoring spec, panel definition to panel spec, detection recipe to detection spec, coherence and onboarding configs to coherence and onboarding specs) and dropped the panel's version: the panel `majortom-global@0.4.0` is the panel spec `majortom-global`, and the model `tide-weather--majortom-global-0.4.0` is registered again as `tide-weather--majortom-global`.
