# CR-029: ponzi-pipeline, starting with the onboarding

- **Requested by / date:** owner, 2026-10-23 (phase 4 of the overhaul plan; plan decision D7)
- **Status:** implemented on the owner's instruction (2026-10-23), awaiting review; uncommitted (plan decision D10)

## Why

`ponzi-pipeline` is the distribution that turns a burst and a date range into the inputs of a run. Its first part is what the library already does before a run, the onboarding of one coherence store; the acquisition and the ISCE3 coherence join it in phase 5. The store's validation stays with the consumer: C18 makes the coherence engine and PONZI two independent implementations of the same checks, and the engine is about to live in `ponzi-pipeline`.

## What changes

| Before | After |
| --- | --- |
| `ponzi.onboarding.config`, `onboard`, `built`, `weather` | `ponzi_pipeline.onboard.config`, `onboard`, `built`, `weather` (new distribution `ponzi-pipeline` 0.1.0, `packages/pipeline/`), unchanged apart from the imports |
| `ponzi.onboarding.validate` | `ponzi.contracts.validate` |
| `ponzi.onboarding.archive` (`decode_time`) | `ponzi.contracts.time_axis` |
| `ponzi onboard`, `ponzi weather-prefetch` | `ponzi-pipeline onboard`, `ponzi-pipeline weather-prefetch` (same arguments) |
| `ponzi validate-store` | unchanged |
| the extra `onboarding` of `ponzi` | the dependencies of `ponzi-pipeline` |
| `tests/onboarding/` | `packages/pipeline/tests/`; the store checks and `validate-store` in `packages/core/tests/validate/` with the store fixtures they need |

The provenance strings the onboarding writes (`ponzi_pipeline.onboard` in the stamp and the sidecar attrs, kept from the monorepo by CR-008) now name the module that writes them. `ponzi-models` depends on `ponzi-pipeline` (the standards validate the onboarding config, the pixel export reads `writable_time_tables`); `ponzi` does not import it. `pixi run test-pipeline` runs its tests, also in CI.

## Do results change?

No. The same code writes the same sidecars, stamps and samples (the onboarding tests pass unchanged apart from their imports).

## Tests

Before: 575 passed, 14 skipped in `pixi run test`. After: 514 passed, 14 skipped in `pixi run test` and 61 passed in `pixi run test-pipeline` (575 together); the `ml` tier, ponzi-spec and ponzi-models unchanged (38, 38, 91 + 18 skipped, 109 in `ml`).

## Version

`ponzi`: MAJOR in the contract sense (a subpackage, two commands and an extra removed), part of `0.3.0` with CR-028. `ponzi-pipeline` 0.1.0, new. Standard: not affected.
