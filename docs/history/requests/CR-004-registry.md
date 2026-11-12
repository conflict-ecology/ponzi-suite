# CR-004: `ponzi.models`, the registry contract

- **Requested by / date:** owner, 2026-10-12
- **Status:** signed off 2026-10-12; contract implemented; which existing models are registered is decided with the owner
- **Superseded in part:** the registry lives in `ponzi_models.registry` (CR-028), `run_config.yaml` is `scoring_spec.yaml` (CR-070), and the root no longer comes from `PONZI_MODEL_REGISTRY` or `PONZI_DATA_ROOT` (CR-086).

## Why
Models, nulls and lookups are in five places (the monorepo clone's `data/models/fm`, `gaza/tide_onset/hpc_panel`, `$DR/gaza/panel` on the HPC, the release lookup inside the code repository). Conflict work and the paper need one place and one way to read them.

## What changes
`ponzi.models.Registry`: `{registry}/{model_id}/` with `model.json`, `run_config.yaml`, `artifact/`, `calibrations/{id}/calibration.npz`. Root from `PONZI_MODEL_REGISTRY` or `$PONZI_DATA_ROOT/registry`.

## Not in this request
Run configs still name their artifact by path, and the config hash includes that path; referring to a model by id (and hashing the artifact's digest instead) changes config hashes and is its own request.

## Do results change?
No.

## Tests
Unit tests on a temporary folder.
