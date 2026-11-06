# C17: Request config (onboarding spec)

`ponzi_pipeline.onboard.onboarding_spec`. HOW a coherence store is onboarded (where and when are the caller's): which steps run, the edge margin, the ERA5 route and variables, the pair-difference baselines. The values used are stamped into `onboard_meta.json` beside the sidecar (C2).

## Producer and consumers

Written by hand: an onboarding spec of ponzi-suite `onboarding_specs/` (its fields at the top level), or any yaml file with an `onboarding:` section (every other top-level section is then ignored). The file is composed first ([Composition](../../service/configuration.md#composition)). Read by `load_onboarding_spec(path)` for `ponzi-pipeline onboard --onboarding-spec NAME|FILE` (none: the defaults) and `ponzi-pipeline weather-prefetch --onboarding-spec NAME|FILE` (which needs `weather_area`); names are found by `ponzi_spec.specs.find_spec`. The worker stage `onboard` takes an `OnboardingSpec` as its identity params.

## Model

`OnboardingSpec`, pydantic, `extra="forbid"`, frozen: a field left out is the default, an unknown key is an error. Its hash is `spec_hash` (`ponzi_spec.identity.spec_hash`).

```yaml
steps: [built, weather, pairdiff, mask, sample]
edge_margin: 20
weather_source: edh              # edh, cdsgrid, edh_cdsgrid
weather_variables: [...]         # default: ponzi_pipeline.onboard.weather.DEFAULT_VARIABLES
pairdiff_baselines: [12, 24, 36, 48, 60]
weather_area: [lon_min, lat_min, lon_max, lat_max]   # optional
```

| Field | Meaning |
|---|---|
| `steps` | the per-burst preparation to run, any subset of `ONBOARDING_STEPS`; they run in that order whatever order they are given in, and `onboard_store` refuses an unknown name |
| `edge_margin` | pixels eroded from the valid footprint for the process mask and the pixel sample; preprocessing, so NOT a scoring spec field (C4) |
| `weather_source` | the ERA5 route: `edh`, `cdsgrid`, or `edh_cdsgrid` (edh where the EDH store reaches, cdsgrid after it) |
| `weather_variables` | the variables of the C2 sidecar |
| `pairdiff_baselines` | the baselines the `pairdiff` step differences every ERA5 level over (`DEFAULT_PAIRDIFF_BASELINES`) |
| `weather_area` | one CDS grid request per month over this WGS84 box (snapped outward to whole ERA5-Land cells), shared by every burst inside it, which it must contain plus one cell; `cdsgrid` and `edh_cdsgrid` only (refused with `edh`). Default None: each burst requests its own patch, and the field is left out of the dump, so the stamp and the hash do not change |

## Functions

`load_onboarding_spec(path=None) -> OnboardingSpec` (None: the defaults; a missing file is `FileNotFoundError`), `OnboardingSpec`, `ONBOARDING_STEPS`, `DEFAULT_PAIRDIFF_BASELINES`.
