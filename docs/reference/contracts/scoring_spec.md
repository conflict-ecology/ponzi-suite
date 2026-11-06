# C4: Scoring spec

Status: implemented 2026-09-07, `ponzi.core.scoring_spec` (package `packages/core`).

## Purpose

The algorithm specification and nothing else: burst-independent, sensor-independent, mode-independent. Its hash identifies a computation; two stores with the same `scoring_spec_hash` were produced by the same algorithm.

## Producer and consumers

Producer: the user. Scoring specs live in the sibling repo `ponzi-suite`, under `scoring_specs/` (CR-048), not in ponzi-core; a model's scoring spec is also kept as `scoring_spec.yaml` beside the model in the registry, verbatim, or as its composed document when it uses `extends` (`copy_scoring_spec`) (`ponzi_models.registry`, default `{home}/registry` in the PONZI home, `ponzi_spec.home`). Consumers: `ponzi run` (`--scoring-spec NAME|FILE`, `RunRequest.scoring_spec`, found by `ponzi_spec.specs.find_spec`: the PONZI home's `scoring_specs/`, then the suite's; loads it, stamps it); the ponzi-worker `run` stage (`ponzi_worker.stages.run`, which takes the spec as a mapping in `RunParams.scoring_spec`, composed (a mapping that still names a base with `extends` is refused), writes it to `_config/{scoring_spec_name}.yaml` in its work folder and hands that file to `ponzi run`'s `RunRequest`); ponzi-models (`calibration.null_runs`, which checks the loaded hash against the model card's `scoring_spec_hash`; `registry.register_model`; `rehearsal`).

Composition (CR-043, `ponzi_spec.compose.load_yaml`): a file may build on others with `extends:`, a path or a list of paths relative to the file that writes it. The bases are merged in order, then the file's own keys over them; mappings merge key by key at every depth, anything else (a list, a value, null) replaces. `extends:` may also open any mapping inside a document. Cycles and non-mapping bases are refused. What is validated and hashed is the composed config, so a composed file and the flat file it resolves to have the same hash. A base's `name` is not inherited.

## Schema

`ponzi.core.scoring_spec.ScoringSpec`, a plain pydantic model (not a settings model), `extra="forbid"` at every level.

| Block | Field | Type | Constraint | Default | Meaning |
|---|---|---|---|---|---|
| top | `schema_version` | int | = 1 | 1 | Part of the hash |
| top | `name` | str or null | | file stem | Label only; NOT part of the hash |
| `context` | `C` | int | > 0 | required | Context length in acquisitions |
| `context` | `min_support` | int | 1..C | required | Minimum non-NaN context observations for a pixel-channel to be fitted |
| `forecaster` | `name` | str | non-empty | required | registered: `rolling_ols`, `tide`, `external`, `stored` |
| `forecaster` | `params` | dict | validated by the forecaster's own pydantic model | `{}` | e.g. `{harmonic_order: 0, pooled: false}` for `rolling_ols` |
| `scoring` | `baseline_days` | list[int] | non-empty, positive, strictly increasing | required | The pyramid's baselines, matched by value against the store |
| `scoring` | `H` | int | > 0 | required | Horizon length |
| `scoring` | `alpha` | float | > 0 | required | z-level for the sensitivity channel `s` |
| `aggregate` | `min_channels` | int | >= 0 | 0 | Pixel unscored when fewer valid `(b, h)` channels |
| `aggregate` | `struct_weight` | bool | | true | `w = 1 / (1 + n_prim + n_sec)` when true, uniform otherwise |
| `state_machine` | `alpha` | float or null | > 0 | null | Change threshold on `anomaly_score`; null resolves to `scoring.alpha` |
| `state_machine` | `delta` | float | any value; a large positive value disables the difference test | required | `is_change = score > alpha AND difference < delta` |
| `state_machine` | `recovery_steps` | int | > 0 | 1 | Quiet steps to return to NORMAL |
| `state_machine` | `noise_floor` | float or `derived` | in (0, 1) | `derived` | Detectability floor on `predicted_median`; `derived` is the zero coherence level of the input store's own estimator (`ponzi.contracts.coherence.noise_floor`), resolved by the runner and recorded in the stamp |
| `state_machine` | `nms_window` | int | >= 0 | 0 | NMS window in steps; 0 resolves to `H` |

Defaults are load-bearing: the hash covers resolved values, so a yaml that omits `struct_weight` hashes identically to one that writes `struct_weight: true`.

`context.edge_margin` was removed on 2026-09-09 and is now rejected like any other unknown key. The boundary margin is preprocessing, not algorithm: the process mask is produced at onboarding and travels with the input (a sidecar `process_mask` layer, or the pixel sample's own margin), so two runs that differ only in their margin are the same computation on different pixels and share a `scoring_spec_hash`. Every scoring spec hash changed with the removal, so outputs stamped with an older hash are stale and are re-run.

Resolution: the `ScoringSpec` model validator resolves `state_machine.alpha` null and `nms_window` 0 above, so any constructed config carries the effective values; `noise_floor: derived` stays `derived` in the config (and its hash) and is resolved per input store by the runner. `load_scoring_spec(path) -> ScoringSpec` composes the yaml (`extends:`), applies the file-stem default for `name`, and constructs it. `forecaster.params` passes through `ponzi.core.scoring_spec._validate_forecaster_params(name, params)`: a name in the forecaster registry (`ponzi.core.forecast.registry`) gets its params model's resolved defaults (so they are hashed), a rejected value is a `ValueError`, an unregistered name keeps `params` as given. A `tide` config names its weights by `params.artifact`, a path or a registry reference `registry:<model id>@sha256:<digest>` (CR-026, `ponzi.core.forecast.artifacts`), so the hash says which weights, not where they lie; loading it needs an artifact resolver (`use_resolver`, or the `ponzi.artifact_resolvers` entry point).

`spec_hash`: BLAKE2b, 16-byte digest, hex, of the canonical JSON of `model_dump(mode="json", exclude={"name"})` with sorted keys and compact separators: `ponzi_spec.identity.spec_hash`, the function of every spec's hash (CR-070). Exposed as the function `spec_hash(cfg)` and the property `ScoringSpec.spec_hash` (named `config_hash` before CR-070, the same value). Stamped as `ponzi_scoring_spec_hash` (`ponzi_config_hash` before CR-070) into every output store and as `scoring_spec.hash` into `run_meta.json`.

Example (the reference `rolling-ols-pyramid`, `ponzi-suite/scoring_specs/rolling-ols-pyramid.yaml`, formerly `exp_b5h5_base`):

```yaml
schema_version: 1
context: {C: 30, min_support: 6}
forecaster: {name: rolling_ols, params: {harmonic_order: 0, pooled: false}}
scoring: {baseline_days: [12, 24, 36, 48, 60], H: 5, alpha: 3.0}
aggregate: {min_channels: 5, struct_weight: true}
state_machine: {alpha: null, delta: -0.1, recovery_steps: 1, noise_floor: 0.03, nms_window: 0}
```

## Invariants

- No paths, dates, mode, dataset names, sink choices, thread counts or thresholds-to-replay in this file; those are run arguments (C4a) or replay arguments. The one location a config may hold is a forecaster's `params.artifact`, and it should be a registry reference: a plain path is accepted but puts the location in the hash.
- `extends` is reserved: no config field has that name.
- Derived-from-data values (`revisit_days`, `T`, overlap mask) are never fields.
- Adding a forecaster never changes this schema.

## Functions

`ponzi.core.scoring_spec`: `SCHEMA_VERSION`, `ScoringSpec`, `ScoringContext`, `ScoringForecaster`, `ScoringPyramid`, `ScoringAggregate`, `ScoringStateMachine`, `load_scoring_spec(path)`, `composed_scoring_spec(path)`, `spec_hash(cfg) -> str`, `dump_scoring_spec(cfg, path)` (writes the resolved, flat values including `name`, sorted keys). `ponzi_spec.compose`: `load_yaml`, `merge`, `ComposeError`. A copy of the example above is `packages/core/tests/data/rolling-ols-pyramid.yaml`; its hash (`acfd26a53eefa49557b0da18cdc46fed`) is asserted as a golden value in `packages/core/tests/test_scoring_spec.py`.
