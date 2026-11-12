# Naming

Specs, models and standards have names a person can read: lowercase words joined by hyphens, from the general to the specific. A name says what the thing is. How it is versioned and where it came from are written in the file, never in the name: no version, date, sensor, seed or abbreviation code (`c30`, `pdcompact`, `f1p`, `mt0.4`). The one exception is a standard's sensor (below).

The rules are code, `ponzi_spec.naming` (ponzi-core CR-052, CR-070), and ponzi-core's tests hold every file of this repository to them (`test_suite_names.py`).

| What | Name | Example | Where it sits |
| --- | --- | --- | --- |
| panel spec | `<design>-<scope>[-<change>]` | `majortom-global` | `specs/panel_specs/majortom-global/`; built: `$PONZI_HOME/panels/majortom-global@<hash8>/` |
| training spec | `<family>-<inputs>` | `tide-weather` | `specs/training_specs/tide/tide-weather.yaml` |
| variant | `<training spec>-<change>...` | `tide-weather-fill-median` | `specs/training_specs/tide/candidates/tide-weather-fill-median.yaml` |
| test case's training spec | `<training spec>-<case>-<change>` | `tide-weather-gaza-finetune` | `specs/training_specs/tide/tide-weather-gaza-finetune.yaml` |
| fit at another seed | `<training spec>-seed<N>` | `tide-weather-fill-median-seed43` | `ponzi-models train --seed 43` |
| model | `<training spec>@<hash8>--<panel spec>@<hash8>` | `tide-weather@59bfd3dc--majortom-global@77941f85` | the artifact `export` writes, the registry entry |
| scoring spec | `<forecaster>-<scoring>[-<change>]` | `rolling-ols-pyramid` | `specs/scoring_specs/rolling-ols-pyramid.yaml` (CR-058) |
| coherence spec | `<backend>-<window>[-<change>]` | `isce3-gaussian` | `specs/coherence_specs/isce3-gaussian.yaml` |
| onboarding spec | `<steps>[-<change>]` | `all-steps`, `mask-only` | `specs/onboarding_specs/all-steps.yaml` |
| detection spec | `<method>[-<change>]` | `single-path`, `single-path-gaza-release` | `specs/detection_specs/single-path.yaml` |
| standard | `<sensor>-<scope>` | `s1-general`, `s1-gaza` | `standards/s1-general-2.0.0.yaml`; cited `s1-general@2.0.0` |

A word is letters and digits, and a name starts with a letter. The double hyphen of a model id separates the two spec versions it was made from, since each name may hold single hyphens. A registry reference ends in the artifact's digest and is read on its last `@sha256:`: `registry:tide-weather@59bfd3dc--majortom-global@77941f85@sha256:<digest>`.

A spec is named by its file: `tide-weather-fill-median.yaml` is `tide-weather-fill-median`, and a panel spec by its folder. No spec file says its name (a `training_id` in a training spec or an `id` in a `panel.yaml` is refused), and a name is unique within its kind (ponzi-core CR-081). A spec's version is its content hash, cited `name@<hash8>` (ponzi-core CR-083): a spec is edited in place under its name, and a new name is for another spec, the old one with its change added (`majortom-global-dense`). The name is a label, not part of the hash ([Standard versions and naming](versions.md#specs-a-name-and-a-hash)).

A standard's id is its sensor and its scope, both listed in `ponzi_spec.naming` (`SENSORS`, `SCOPES`, `TESTCASES`). The sensor is the one exception to "no sensor in a name": a standard runs one sensor's data, and its model card names the same sensor. `check-standard`, `register-standard` and the suite's tests refuse any other form. Its version is not in the id: it is cited as `<id>@<version>`.

## Spec folders

A spec is a file a person writes, validated by PONZI, that says how something is made; its content enters the identity of what it makes. There are six kinds (`ponzi_spec.specs.SPEC_KINDS`). ponzi-suite keeps them under git, and the PONZI home holds working copies, in folders of the same plural name:

| Spec | Says how this is made | Folder (suite and home) |
| --- | --- | --- |
| training spec | a trained model | `specs/training_specs/**/<name>.yaml` (`tide/`, `tide/candidates/`) |
| scoring spec | the runs of a model over a burst | `specs/scoring_specs/<name>.yaml` |
| panel spec | a built panel | `specs/panel_specs/<name>/` (`panel.yaml` and its two geojson) |
| detection spec | the events and cells from p-values | `specs/detection_specs/<name>.yaml` |
| coherence spec | a burst's coherence store | `specs/coherence_specs/<name>.yaml` |
| onboarding spec | a store's sidecar and pixel sample | `specs/onboarding_specs/<name>.yaml` |

A command takes a spec as `--<kind>-spec NAME|FILE` (`--training-spec`, `--scoring-spec`, `--panel-spec`, `--detection-spec`, `--coherence-spec`, `--onboarding-spec`). A path is taken as it is. A name is looked up in the home's folder first, then in the suite's (`$PONZI_SUITE`, else the `ponzi-suite` checkout beside ponzi-core), by `ponzi_spec.specs.find_spec`: the file `<name>.yaml` anywhere under the kind's folder (subfolders only arrange the files), or a panel spec's folder `<name>/`. The keys inside a spec's file are its content. The standard, the model, the calibration, the built panel, the workflow, the site file, the cluster profile and the server settings are not specs.

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

## Before

The former names of the specs are in ponzi-core [CR-052](../history/requests/CR-052-readable-names.md). CR-070 renamed the files a person writes to specs (fit spec to training spec, run config to scoring spec, panel definition to panel spec, detection recipe to detection spec, coherence and onboarding configs to coherence and onboarding specs) and dropped the panel's version: the panel `majortom-global@0.4.0` is the panel spec `majortom-global`, and the model `tide-weather--majortom-global-0.4.0` was registered again as `tide-weather--majortom-global`, and since CR-083 is `tide-weather@<hash8>--majortom-global@<hash8>`.
