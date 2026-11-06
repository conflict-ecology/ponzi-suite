# C17: Request config

> Note (2026-11-04): this repository reads only the `onboarding` section, `ponzi_pipeline.onboard.onboarding_spec`. The `selection` section, its constants and key vocabulary, the campaign files (`configs/request/`) and the request it was frozen into (C14) are not in this repository.

Status: implemented and reshaped 2026-09-09; here the onboarding section, `ponzi_pipeline.onboard.onboarding_spec`.

## Purpose

The request config says HOW a store is onboarded (where and when are given by the caller). Here that is the generic per-burst onboarding of a coherence store: which steps run, the edge margin, the ERA5 route and variables, the pair-difference baselines.

## Producer and consumers

Written by hand, any yaml file with an `onboarding:` section; the file is composed first (`extends`, `ponzi_spec.compose.load_yaml`), and every other top-level section (such as `schema_version` or `selection`) is ignored. Read by `load_onboarding_spec(path)` for `ponzi-pipeline onboard --onboarding-spec SPEC` (none: the defaults) and `ponzi-pipeline weather-prefetch --onboarding-spec SPEC` (which needs `weather_area`). The worker's `onboard` stage (ponzi-service, `ponzi_worker.stages.run`) takes an `OnboardingSpec` as its identity parameters. The values used are stamped into `onboard_meta.json` beside the sidecar (C2).

## Model

`OnboardingSpec`, pydantic, `extra="forbid"`, frozen: a field left out is the default, an unknown key is an error. A file without an `onboarding:` mapping is refused.

```yaml
onboarding:
  steps: [built, weather, pairdiff, mask, sample]
  edge_margin: 20
  weather_source: edh              # edh, cdsgrid, edh_cdsgrid
  weather_variables: [...]         # ponzi_pipeline.onboard.weather.DEFAULT_VARIABLES
  pairdiff_baselines: [12, 24, 36, 48, 60]
  weather_area: [lon_min, lat_min, lon_max, lat_max]   # optional, CR-023
```

| Field | Meaning |
|---|---|
| `steps` | the per-burst preparation to run, any subset of `ONBOARDING_STEPS`; they run in that order whatever order they are given in, and `onboard_store` refuses an unknown name |
| `edge_margin` | pixels eroded from the valid footprint for the process mask and the pixel sample; preprocessing, not scoring, so it is NOT a scoring spec field |
| `weather_source` | the ERA5 route: `edh`, `cdsgrid`, or `edh_cdsgrid` (edh where the EDH store reaches, cdsgrid after it) |
| `weather_variables` | the variables of the C2 sidecar |
| `pairdiff_baselines` | the baselines the `pairdiff` step differences every ERA5 level over, `DEFAULT_PAIRDIFF_BASELINES` |
| `weather_area` | CR-023: one CDS grid request per month over this WGS84 box, shared by every burst inside it, which it must contain plus one cell; `cdsgrid` and `edh_cdsgrid` only (refused with `edh`); default None, each burst requests its own patch, and the field is then left out of the dump so the stamp is unchanged |

## Functions

`load_onboarding_spec(path=None) -> OnboardingSpec` (None: the defaults; a missing file is `FileNotFoundError`), `OnboardingSpec`, `ONBOARDING_STEPS`, `DEFAULT_PAIRDIFF_BASELINES`.
