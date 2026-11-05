# Naming

Forecasters, panels and models have names a person can read: lowercase words joined by hyphens, from the general to the specific. A name says what the thing is. How it is versioned and where it came from are written in the file, never in the name: no version, date, sensor, seed or abbreviation code (`c30`, `pdcompact`, `f1p`, `mt0.4`).

The rules are code, `ponzi_spec.naming` (ponzi-core CR-052), and ponzi-core's tests hold every file of this repository to them (`test_suite_names.py`).

| What | Name | Example | Where it sits |
| --- | --- | --- | --- |
| panel | `<design>-<scope>` | `majortom-global` | `panels/majortom-global/`; its version is in `panel.yaml` |
| panel, cited | `<id>@<version>` | `majortom-global@0.4.0` | standards, calibrations; built: `majortom-global-0.4.0` |
| forecaster | `<family>-<inputs>` | `tide-weather` | `forecasters/tide/weather.yaml` |
| variant | `<forecaster>-<change>...` | `tide-weather-fill-median` | `forecasters/tide/candidates/fill-median.yaml` |
| test case's forecaster | `<forecaster>-<case>-<change>` | `tide-weather-gaza-finetune` | `testcases/gaza/forecaster.yaml` |
| fit at another seed | `<forecaster>-seed<N>` | `tide-weather-fill-median-seed43` | `ponzi-models train --seed 43` |
| model | `<forecaster>--<panel>-<version>` | `tide-weather--majortom-global-0.4.0` | the artifact `export` writes, the registry entry |
| run config | `<forecaster>-<scoring>[-<change>]` | `rolling-ols-pyramid` | `run_configs/rolling-ols-pyramid.yaml` (CR-058) |

A word is letters and digits, and a name starts with a letter. The double hyphen of a model id separates its two names, since each may hold single hyphens. A model id has no `@`, because a registry reference already uses it: `registry:tide-weather--majortom-global-0.4.0@sha256:<digest>`.

## Words in use

- **Designs** (panels): `majortom`, cells of the Major TOM grid.
- **Scopes** (panels): `global`.
- **Families** (forecasters): `tide`, the default today; a new forecaster brings its own family word.
- **Inputs** (forecasters): `weather`, the weather levels (soil moisture, snow depth, snow cover) and the compact set of their pair differences.
- **Scorings** (run configs): `pyramid`, the 15-pair pyramid over baselines of 12 to 60 days and a horizon of 5. A run config's forecaster part is the forecaster it runs (`rolling-ols`, `tide-weather`); its name is a label and not part of its hash.
- **Changes** (variants): `fill-<how>`, how a missing coherence is given to the model (`constant`, `median`, `previous`, `sentinel`, with `no-flags` when the obs flags are left out); `augmented`, the general training augmentation; `context-dropout`; `radar-moisture`, the Sentinel-1 moisture covariate; `finetune`.

Add a word here when a new one is needed, so the same thing is always called the same.

## Former names

Every fit spec renamed by CR-052 keeps its old id as `formerly:`, so the fits, artifacts and registry entries made under it can still be found:

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
| `rolling-ols-pyramid` (run config) | `exp_b5h5_base` |

Models registered before keep their names (`tide_c30_pdcompact_mt0.4`, `tide_s1_mt04`); the headers of the specs refer to them as they were registered.
