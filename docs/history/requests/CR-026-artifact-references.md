# CR-026: forecaster weights named by registry id and digest

- **Requested by / date:** owner, 2026-10-23 (phase 2 of the overhaul plan, section 4b)
- **Status:** implemented on the owner's instruction (2026-10-23), awaiting review; uncommitted (plan decision D10)
- **Superseded in part:** `ponzi.models` is `ponzi_models` (CR-028), and the default registry is the home's (CR-086).

## Why

A TiDE run config names its weights by a folder path, and the path is part of `config_hash`. The same weights in another place give another hash, so ponzi-models' null runs start in a working folder where the old relative path is a symlink to the registry. A config should say which weights, not where they lie.

## What changes

`forecaster.params.artifact` of `tide` also accepts a registry reference, `registry:<model id>@sha256:<artifact digest>`, the digest being the model card's `artifact_digest` (sha256 over the artifact folder, `ponzi.models.digest_dir`).

- `ponzi.core.forecast.artifacts`: `parse_ref`, `ArtifactRef`, a pluggable resolver (`set_resolver`, `use_resolver`) and `resolve_artifact` (a path is used as it is; a reference goes through the resolver; the folder must hold `meta.json`). Core does not know the registry.
- `TideParams` checks a reference's form only, so a config with a reference loads and hashes without a registry; the forecaster resolves it when it loads the module.
- `ponzi.models`: `ModelEntry.ref` (the reference of a model) and `Registry.resolver(verify=True)`, which refuses a digest that is not the card's and, once per model and process, files that do not match it.
- `ponzi` (the command): every run-side command runs with the default registry's resolver, opened on the first reference (`PONZI_MODEL_REGISTRY`, else `$PONZI_DATA_ROOT/registry`).

A path keeps working and keeps its hash. The plan expected a new hash rule ("config hash v2"); none is needed: a config with a reference simply hashes the reference.

## Do results change?

No. Every existing config is unchanged; a reference to the same weights gives the bytes of the path (tested).

## Tests

`test_artifact_ref.py` (parsing, the resolver hook, a config hashing without the registry, the registry's resolver, a tampered artifact refused) and, in the `ml` tier, `test_tide_templated.py::test_a_registry_reference_runs_the_same_weights` (equal bytes by reference and by path).

## Version

`ponzi`: MINOR, opt-in (released as `0.2.z+1` under CR-020's reading). Standard: not affected.
