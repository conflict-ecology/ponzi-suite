# C4: Scoring spec

`ponzi.core.scoring_spec` (package `packages/core`). The algorithm specification and nothing else: burst-independent, sensor-independent, mode-independent. Its hash identifies a computation: two stores with the same `ponzi_scoring_spec_hash` were produced by the same algorithm.

## Producer and consumers

Producer: the user. Scoring specs live in ponzi-suite `specs/scoring_specs/` (and the PONZI home's working copies, looked in first: [Naming rules](../../models/naming.md#spec-folders)); a model's scoring spec is also kept as `scoring_spec.yaml` beside the model in the registry, verbatim, or composed when it uses `extends` (`ponzi_models.registry.store.copy_scoring_spec`).

Consumers: `ponzi run` (`--scoring-spec NAME|NAME@HASH|FILE`, found by `ponzi_spec.specs.find_spec`, a `NAME@HASH` version also in the registry's archive; `RunRequest.scoring_spec`, C4a); the worker stage `run` (`RunParams.scoring_spec`, a composed mapping: one that still names a base with `extends` is refused; written to `_config/{scoring_spec_name}.yaml` in its work folder and handed to `RunRequest`); ponzi-models (`calibration.null_runs`, which checks the loaded hash against the model card's `scoring_spec_hash`; the registry; the standards workflow; `rehearsal`).

A file may build on others with `extends:` ([Composition](../../service/configuration.md#composition)); what is validated and hashed is the composed spec. A base's `name` is not inherited.

## Schema

`ScoringSpec`, a plain pydantic model (not a settings model), `extra="forbid"` at every level.

| Block | Field | Type | Constraint | Default | Meaning |
|---|---|---|---|---|---|
| top | `name` | str or null | | file stem | Label only; NOT part of the hash |
| `context` | `C` | int | > 0 | required | Context length in acquisitions |
| `context` | `min_support` | int | 1..C | required | Minimum non-NaN context observations for a pixel-channel to be fitted |
| `forecaster` | `name` | str | non-empty | required | registered: `rolling_ols`, `tide`, `external`, `stored` |
| `forecaster` | `params` | dict | validated by the forecaster's own pydantic model | `{}` | e.g. `{harmonic_order: 0, pooled: false}` for `rolling_ols` |
| `scoring` | `target` | str | non-empty | `coh` | The input's `pair` variable the run forecasts and scores (CR-102): a coherence in [0, 1] whose estimator gives the noise floor (`noise_floor: derived` and the ceiling read the target's `estimator_params`, else the store's). Left out of the hash when it is `coh`, so a spec written before keeps its hash |
| `scoring` | `baseline_days` | list[int] | non-empty, positive, strictly increasing | required | The pyramid's baselines, matched by value against the store |
| `scoring` | `H` | int | > 0 | required | Horizon length |
| `scoring` | `alpha` | float | > 0 | required | z-level for the sensitivity channel `s` |
| `aggregate` | `min_channels` | int | >= 0 | 0 | Pixel unscored when fewer valid `(b, h)` channels |
| `aggregate` | `struct_weight` | bool | | true | `w = 1 / (1 + n_prim + n_sec)` when true, uniform otherwise |
| `state_machine` | `alpha` | float or null | > 0 | null | Change threshold on `anomaly_score`; null resolves to `scoring.alpha` |
| `state_machine` | `delta` | float | any value; a large positive value disables the difference test | required | `is_change = score > alpha AND difference < delta` |
| `state_machine` | `recovery_steps` | int | > 0 | 1 | Quiet steps to return to NORMAL |
| `state_machine` | `noise_floor` | float or `derived` | in (0, 1) | `derived` | Detectability floor on `predicted_median`; `derived` is the zero coherence level of the input store's own estimator (`ponzi.contracts.coherence.noise_floor`, C1), resolved by the runner and recorded in the stamp |
| `state_machine` | `nms_window` | int | >= 0 | 0 | NMS window in steps; 0 resolves to `H` |

Defaults are load-bearing: the hash covers resolved values, so a yaml that omits `struct_weight` hashes identically to one that writes `struct_weight: true`. The model validator resolves `state_machine.alpha` null and `nms_window` 0, so any constructed spec carries the effective values; `noise_floor: derived` stays `derived` in the spec (and its hash) and is resolved per input store by the runner.

`forecaster.params` passes through `_validate_forecaster_params(name, params)`: a name in the forecaster registry (`ponzi.core.forecast.registry`) gets its params model's resolved defaults (so they are hashed), a rejected value is a `ValueError`, an unregistered name keeps `params` as given. A `tide` spec names its weights by `params.artifact`, a path or a registry reference `registry:<model id>@sha256:<digest>` (`ponzi.core.forecast.artifacts`), so the hash says which weights, not where they lie; loading it needs an artifact resolver (`use_resolver`, or the `ponzi.artifact_resolvers` entry point).

`spec_hash` is `ponzi_spec.identity.spec_hash` of `model_dump(mode="json")` without `name`: BLAKE2b (16 bytes, hex) of the canonical JSON (sorted keys, compact separators). Exposed as the function `spec_hash(cfg)` and the property `ScoringSpec.spec_hash`; stamped as `ponzi_scoring_spec_hash` into every output store (C7) and as `scoring_spec.hash` into `run_meta.json` (C9). The hash is the spec's version, cited `name@<hash8>` (ponzi-core CR-083); the spec has no `schema_version`.

Example, the reference `rolling-ols-pyramid` (ponzi-suite `specs/scoring_specs/rolling-ols-pyramid.yaml`):

```yaml
context: {C: 30, min_support: 6}
forecaster: {name: rolling_ols, params: {harmonic_order: 0, pooled: false}}
scoring: {baseline_days: [12, 24, 36, 48, 60], H: 5, alpha: 3.0}
aggregate: {min_channels: 5, struct_weight: true}
state_machine: {alpha: null, delta: -0.1, recovery_steps: 1,
                noise_floor: 0.03, nms_window: 0}
```

A copy is `packages/core/tests/data/rolling-ols-pyramid.yaml`; its hash `a8e69b6b8b407d33ba8e4b800ede8d3a` is a golden value in `packages/core/tests/test_scoring_spec.py`.

## Invariants

- No paths, dates, mode, dataset names, sink choices, thread counts or replay thresholds; those are run arguments (C4a) or replay arguments (C4b). The one location a spec may hold is a forecaster's `params.artifact`, and it should be a registry reference: a plain path is accepted but puts the location in the hash.
- The edge margin is not a field (`context.edge_margin` is refused like any unknown key): the process mask is made at onboarding and travels with the input (C2, C3), so two runs that differ only in their margin share a hash.
- Derived-from-data values (`revisit_days`, `T`, the overlap mask) are never fields; `extends` is reserved.
- Adding a forecaster never changes this schema.

## Functions

`ponzi.core.scoring_spec`: `ScoringSpec`, `ScoringContext`, `ScoringForecaster`, `ScoringPyramid`, `ScoringAggregate`, `ScoringStateMachine`, `load_scoring_spec(path)` (composes, applies the file-stem default for `name`, constructs), `composed_scoring_spec(path)` (the flat composed mapping), `spec_hash(cfg) -> str`, `dump_scoring_spec(cfg, path)` (the resolved, flat values including `name`, sorted keys).
