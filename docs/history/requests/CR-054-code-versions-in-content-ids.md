# CR-054: the code's major versions in content ids, and every distribution versioned by its tags

- **Requested by / date:** owner, 2026-11-05 (approved the first change request of the versioning gaps).
- **Status:** implemented on the owner's instruction (2026-11-05)

## Why

Checking the change workflows of 15 October against the code found that a results-changing release reran nothing. A content id was the stage, its hand-kept version `"1"`, its inputs and its parameters, so the worker's cache reused runs and coherence stores made by an older major. Only `pvalues` noticed, and only once the calibration was rebuilt. Three of the four ponzi-core distributions also had fixed version numbers that were never raised.

## What changes

- **`ponzi_spec.identity`:**
  - `library_major(version)` (the CR-020 rule: the first number from 1 on, `0.y` below 1, None when unknown).
  - `code_majors(distributions)`: the installed majors.
  - `content_id(..., code=)`: the majors enter the payload under `code`, which is left out when empty.
  - `ponzi.calibration.library_major` now uses it.
- **`StageSpec.code`:** the distributions whose code computes a stage, hashed through `code_majors`. ponzi-worker's stages declare them:

| Stage | Code |
| --- | --- |
| `run`, `pvalues`, `detect`, `tile` | `ponzi` |
| `discover`, `dem`, `coherence`, `onboard` | `ponzi-pipeline` |
| `assemble` | `ponzi`, `ponzi-pipeline` |
| `ingest-coherence`, `ingest-calibration` | none |

  ISCE3 is not named: it is installed only in the `isce3` environment, while ids are also computed in the default one, and its build is pinned in the lock.
- **Versions from git tags, per distribution (hatch-vcs):**
  - `ponzi` takes `vX.Y.Z`, now matched as `v[0-9]*` only.
  - `ponzi-spec` takes `spec-vX.Y.Z`, `ponzi-pipeline` takes `pipeline-vX.Y.Z`, and `ponzi-models` takes `models-vX.Y.Z`.
  - Each `__version__` reads the installed metadata.
  - Tagged at `main`: `spec-v0.4.0`, `pipeline-v0.2.0`, `models-v0.3.0`; `v0.2.4` was moved onto `main`.
  - CI fetches the full history for the spec job and the docs build.

## Do results change?

No scores or codes. Every content id of a computing stage changes once, so a worker's cache computes everything again once. Ingest ids are unchanged.

## Tests

- ponzi-spec `test_identity.py`: majors, patch and minor releases keep an id, a major changes it, a stage without code keeps the id of before.
- ponzi-worker `test_plan.py`: every computing stage names its code, and the ingest stages name none.
- The spec, calibration and service suites.

## Version

- `ponzi-spec`: minor (new functions and a new optional field).
- `ponzi`: patch.
- ponzi-worker: the content ids of its stages change.
