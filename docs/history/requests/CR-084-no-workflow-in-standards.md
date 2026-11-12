# CR-084: a standard does not list its stages

- **Requested by / date:** owner, 2026-11-12 ("what is the version in the workflow section? I thought that was done away", then "yes" to removing it)
- **Status:** signed off (2026-11-12), implemented (unreleased)

## Why
A standard's `workflow:` listed stages with versions (`{name: discover, version: "2"}`, ..., `{name: tile, version: "2"}`), read after CR-083 as a version the hash had replaced. It is not a spec version: a stage's version is its identity version, set in the code (`StageSpec.version`) and hashed into every content id the stage makes. The standard's copy of it did nothing:

- `standard-workflow` builds the server's workflow from its own steps and never read it; the worker's steps carry no version.
- Nothing held it to the stages' versions in the code: a stage raised to `3` would leave every standard saying `2`, and nothing would fail.
- It did not name the steps that run: `discover` and `dem` are not run from coherence stores (`--source stores`), and `ingest-coherence` and `ingest-calibration` were missing.
- Its only effects were on the standard's own versioning: it was in `RUN_IDENTITY` (an edit to it was a new major) and in the bundle hash.

What a stage computes already reaches the runs by the content ids (its identity version and its code's majors, CR-054), and the code a standard runs is pinned by `requires`.

## What changes
- `Standard.workflow` is removed; a standard that gives it is refused as any unknown field is.
- `RUN_IDENTITY` loses `workflow`: `sensor`, `coherence`, `onboarding`, `panel`, `model`, `scoring_spec_hash`.
- `ponzi_models.standards.versions.WORKFLOW` is removed. `new-standard` takes `requires` from every stage of `STAGE_CODE`, as before.
- `check-standard` no longer prints the number of stages.
- ponzi-suite: `standards/s1-general-2.0.0.yaml` loses `workflow:`; the standards docs follow.

The server's file (`standard-workflow`) keeps its `workflow:` block (`{workflow: <id>, version: <version>, steps: [...]}`): that is the worker's workflow, built from the standard, and is unchanged.

## Do results change?
No. No content id changes. A standard's bundle hash changes (the field is gone); s1-general is a draft and no standard is registered.

## Tests
`test_standards.py`: its standards lose `workflow`, and one that gives it is refused.

## Version
Library: `ponzi-models` major (a standard file of before is refused). Standard: none registered; s1-general stays 2.0.0, a draft.
