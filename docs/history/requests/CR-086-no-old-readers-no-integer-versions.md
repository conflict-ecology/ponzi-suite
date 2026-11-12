# CR-086: no reader of the old repositories' formats, no integer format version

- **Requested by / date:** owner, 2026-11-12 ("remove Old-format readers still in code", then "remove those integer versions replace with new convention"; then, the same day, the TiDE parity tests and the readers kept for them)
- **Status:** signed off (2026-11-12), implemented (unreleased)

## Why
CR-082 removed the guards that explained old formats. Readers of formats made by the retired repositories PONZI was derived from (repeat_ccd's engine, the old ponzi and ponzi-models repositories) were still in the code. Nothing of theirs is carried over (decision D6 of the overhaul plan), so the readers are dead weight. CR-085 made every store's and record file's version the hash of its declaration, but three integer format numbers were missed: the calibration file's (2 and 3), the burst catalog's (1) and the prepared training folder's (2). ponzi-server's `boundaries.sqlite3` had a fourth (2).

Readers of this suite's own earlier formats are not in scope (ponzi-service's areas of before CR-067, ponzi-visual's renamed skins, artifacts of before CR-016).

## What changes

### The readers removed
- `ponzi.contracts.pred`: the reader of a `pred_quantiles.zarr` (`LEGACY_ARRAY`, `_legacy_report`, `is_legacy_store`, `_legacy_meta`, `PredMeta.legacy`, `PredDataset.legacy`). The `stored` forecaster reads a C5 store only. `PredMeta.stamp` is required.
- C1, `ponzi.contracts.coherence` and `ponzi.contracts.validate`: `writer_command` and `schema` as the producer (`_legacy_producer`). A store without `producer` reads it as the empty string. The "legacy store" wording of the `identity` warning goes; a missing attr still warns.
- `validate-store`: `baseline_days` from the `baseline` array's attrs, and the decoding of a CF-encoded integer `time` axis. C1's `time` is datetime64; any other dtype now fails `time_axis` (`ponzi.contracts.time_axis.decode_time`).
- `make_coherence_fixture(legacy_attrs=)` is `identity_attrs=` (false leaves out `sensor`, `producer` and `contract_version`), without the old `schema` attr.
- C11, `ponzi.evaluation.labels`: the conversion of a `window` array into bag ids (`bags_from_window`, the attr `bag_from_legacy_window`). A store without `bag` is read as before: the caller's anchor window applies to every pixel.
- C6 and C7: the ceiling layers are no longer optional (`OPTIONAL_ARRAYS`, the `optional` check). `c` and `ceiling_score` are required, as every writer writes them.
- The run stamp: `ceiling_floor` is required, in (0, 1). The runner always set it. The stamp's hash changes.
- The environment names `PONZI_DATA_ROOT` and `PONZI_MODEL_REGISTRY`, which came from the old repositories: no longer aliases of `roots.data` and `roots.registry` (`ENV_ALIASES`), and no longer the registry's default (`ponzi_spec.specs.registry_root`, `default_registry_root`). The registry is `--registry`, else the PONZI home's. The commands' help says so.
- ponzi-suite: `tide-weather-gaza-finetune` names `${PONZI_ROOTS__DATA}` where it named `${PONZI_DATA_ROOT}`. Its hash changes from `8c62637900183b8f1029de4927ceb403` to `f2695f019d04c5989d2a2f2c0fc957e5`. Nothing pins it: no test, standard or registry entry holds it.

### The readers kept, then removed
The first pass kept what the TiDE parity oracle needed: `test_tide.py` read a reference coherence store and a reference artifact of the old repositories through `PONZI_REF_BURSTS` and `PONZI_REF_ARTIFACT`. The owner then dropped the parity tests (2026-11-12), and with them these readers.

The tests removed:
- `test_tide.py::test_block_parity_with_the_reference_quantile_store`, and the block it compared with, `packages/core/tests/data/tide_t017_block_golden.npz` (cut from the old repositories' `pred_quantiles.zarr`; nothing else reads it). `test_tide_registered_and_params` stays.
- `test_tide_mask.py`, whole. Its two tests needed a reference artifact without covariates (`PONZI_REF_ARTIFACT_NOCOV`). What they held (only the mask's pixels are forecast, an empty mask forecasts nothing, pooled workers give the serial forecast) `test_tide_templated.py` holds on its own tiny model.
- `test_model_inputs.py::test_legacy_meta_maps_to_the_explicit_spec`. The file's other tests read a meta written here, with its `fcov_spec` from `build_fcov_spec`, and no longer the reference artifact's.
- ponzi-pipeline `test_onboard.py`: `test_the_sample_carries_a_legacy_stores_string_pair_tables`, `test_an_unwritable_pair_table_is_left_out_with_a_note`, and `make_legacy_store` in `conftest.py`.

What is removed with them:
- Zarr v2. `ponzi.contracts.open_group` opens zarr v3 only and refuses another format with `ContractError`. With it go `_ARRAY_DIMENSIONS` in `dim_names` (C1) and in the sample's, the v2 `.zmetadata` in the `consolidated` checks of `validate-store` and of the sample, and the v2 chunk layout (`coh/t.y.x.b`) in `chunk_completeness`. The label reader (C11) opens zarr v3 only too.
- `ponzi.contracts.coherence._attr_baseline_days`: `baseline_days` from the `baseline` array's attrs. A store without the group attr is refused, as `validate-store` already did.
- `ponzi.core.forecast.model_inputs.ensure_fcov_spec`, which mapped a meta without `fcov_spec` (the `tide_v1` artifact) onto the explicit spec. `load_artifact` refuses a meta without `fcov_spec`. Every export writes it.
- ponzi-pipeline `ponzi_pipeline.onboard.onboard.writable_time_tables` and `_writable_pair_table`, which cast a v2 store's object string tables for the sample. `extract_burst_sample` and ponzi-models `export-pixels` no longer call it.

Every writer writes zarr v3 (`zarr_format=3`, or zarr 3's default), with fixed-width strings, so none of this read what this suite writes. No store contract's declaration changes, so no hash changes.

Kept, as rules of the current format rather than readers of an old one: the track from a `burst_id` when a store has no `relative_orbit` (C1), the burst id from a store's name (`_coh.zarr` among the suffixes) when it has no `burst_id` attr, TiDE's `batching: legacy` (a batching a run can choose, CR-011), and the `generation` check of C18's catalogue (removing it is a change of C1's declaration and is left for its own request).

### The integer versions replaced
As CR-085: each layout is declared as data in its module (`CONTRACT`), its version is `ponzi_spec.contract_hash` of that, 32 hex digits written as a string, a reader refuses another version as before, and a test pins the hash.

| File | Constant | Was | Hash | Pinned in |
| --- | --- | --- | --- | --- |
| calibration file | `ponzi.calibration.product.FORMAT` | 2, and 3 when staged | `e0c035b61197db944591fc65bbaf90a2` | ponzi-core `packages/core/tests/test_contract_versions.py` |
| burst catalog `bursts.sqlite3` | `ponzi_spec.catalog.FORMAT` | 1 | `6d512f410f445d81ab7ce591554fa611` | ponzi-core `packages/spec/tests/test_home_catalog.py` |
| prepared training folder | `ponzi_models.training.prepare.FORMAT` | 2 | `e79056c21230a551452c2bdf28b5770e` | ponzi-core `packages/models/tests/test_training_data.py` |
| `boundaries.sqlite3` | `ponzi_server.boundaries.FORMAT` | 2 | `72c08ac7afb8fd293e1aaf24fcc3a341` | ponzi-service `packages/server/tests/test_server_boundaries.py` |
| C7/C8 run stamp | `ponzi.contracts.stamp.STAMP_CONTRACT_VERSION` | `a69e8ed6ee00afcbe4eb62ccdb1080b9` | `861401d948da3382058e27c37b565fcb` | ponzi-core `packages/core/tests/test_contract_versions.py` |

- The calibration file has one declaration for both layouts. A staged file is told by its meta `stages`, not by its number.
- The prepared folder's `FORMAT` is part of `features_identity`, so it is also in the folder's tag: a folder of before is another folder.
- ponzi-server reads the catalog's format from `ponzi_spec.catalog` instead of its own `"1"`.
- Left as a person sets them, by decision: `API_VERSION`, the PONZI STAC extension's version, the standard's version.

## Do results change?
No number changes. A calibration file of before is refused and made again. A burst catalog, a boundaries file and a prepared folder of before are built again. A zarr v2 store and an artifact without `fcov_spec` are refused; this suite writes neither. A run's stores written by this suite still open: the runner always wrote `ceiling_floor` and the ceiling layers, and no reader checks the stamp's `contract_version`. Nothing published is pinned to any of them.

## Tests
- Removed: `test_legacy_quantile_store_replays` (it existed only for the `pred_quantiles.zarr` reader; its refusal of another context depth moves into `test_stored_forecaster_reproduces_the_run`) and `test_legacy_window_store_converts_to_bag_ids`.
- Changed: the fixtures without identity attrs (`test_coherence_store.py`, `test_validate_store.py`), the stamps built by hand (`ceiling_floor`), the registry's default (`test_registry_store.py`, `test_registry_refs.py`), the config (`test_the_old_names_are_not_read`), the format checks of the calibration and catalog tests.
- New: the four pins above, a catalog of format 1 is built again, a boundaries file of format 2 is refused.
- Removed with the parity tests: the four tests named above, `test_tide_mask.py` and `make_legacy_store`.
- New: `open_group` refuses a zarr v2 group (`test_contracts_base.py`).
- Golden data: none converted or made again. The files under `packages/core/tests/data` are numpy arrays and JSON, not stores of the old repositories, and their numbers are unchanged; `tide_t017_block_golden.npz` is removed with the test that read it.

## Version
Library: `ponzi-spec`, `ponzi` and `ponzi-models` major (store and file formats, the stamp, the environment names); `ponzi-pipeline` major (`writable_time_tables` removed). ponzi-server major (the boundaries' format); ponzi-worker none (a test). Standard: none registered; s1-general stays a draft.
