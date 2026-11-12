# CR-092: the store contracts' code is held to its own rules

- **Requested by / date:** owner, 2026-11-12 (after the audit of the contract pages against the code: "draft")
- **Status:** signed off (2026-11-12), implemented (unreleased)

## Why
An audit of the 22 contract pages against the code (2026-11-12) found the pages mostly right, and fixed what was not in the pages alone (the code wins). It also found five places where the code disagrees with itself or with the rules the contracts state for every store, which a page cannot fix:

1. **C3's declaration says int64, every writer writes int32.** The hashed declaration of the pixel sample gives `pix_y` and `pix_x` as `int64` (`ponzi.core.sample`, `CONTRACT`), while `extract_sample` and `ponzi-models export-pixels` write `int32`, and the validator accepts any integer type. C3's version is the hash of a layout no sample has.
2. **Some readers accept any zarr format.** The rule (CR-086) is that every writer writes zarr v3 and every reader refuses another format; `ponzi.contracts.base.open_group` does that. These open stores with `zarr.open_group(..., mode="r")` and no format, so a zarr v2 store is read as it is:
    - `ponzi.contracts.pvalues`: `create_pvalue_store` (its read of `score.zarr`, and its own new store, written in zarr's default format), `open_pvalue_store`;
    - `ponzi.contracts.events`: `open_events_store`;
    - `ponzi.calibration.store` (its reads of `score.zarr`, `staged.zarr` and an existing p-value store) and `ponzi.calibration.staged` (`staged.zarr`, `score.zarr`);
    - `ponzi_models.calibration.null_rows` (`score.zarr`).
3. **Three openers raise outside `ContractError`.** The rule is that an `open_*` that validates raises `ContractError` (`ponzi.contracts.base`, itself a `ValueError`). `ponzi.evaluation.labels.open_labels` raises plain `ValueError`; `open_pvalue_store` and `open_events_store` raise `IncompletePValueStore` and `IncompleteEventsStore`, which subclass `ValueError` only. A caller cannot catch every contract failure by one type.
4. **The engine and PONZI judge `identity` differently.** C18's `identity` check: PONZI (`ponzi.contracts.validate`) counts an empty `sensor` or `producer` as missing; the engine (`ponzi_pipeline.engine`) only checks that the keys exist. A store with `sensor: ""` gets `ok` from the engine and `warn` from PONZI, and the `engine_report` check then reports a disagreement that is the checks', not the store's.
5. **"Request config" in the onboarding spec's docstrings.** CR-070 renamed the request config to the onboarding spec; `ponzi_pipeline.onboard.onboarding_spec` still says "a request config" in its module docstring and in `load_onboarding_spec`'s.

## What changes
1. **C3 (ponzi).** The declaration gives `pix_y` and `pix_x` as `int32`, as written. C3's `CONTRACT_VERSION` changes, and its pin in `test_contract_versions.py`. The validator keeps accepting any integer type when it reads. A sample of the old version is refused, as any sample of another version is (CR-085), and is made again.
2. **Zarr v3 (ponzi, ponzi-models).** Every site in item 2 opens through `ponzi.contracts.base.open_group`, and `create_pvalue_store` writes with `zarr_format=3`, so a store of another format is refused with the same error as elsewhere. No store PONZI writes changes.
3. **One error type (ponzi).** `IncompletePValueStore` and `IncompleteEventsStore` subclass `ContractError`, and `open_labels` raises `ContractError` for a store that breaks C11. `ContractError` is a `ValueError`, so a caller catching `ValueError` keeps working.
4. **`identity` (ponzi-pipeline).** The engine counts an empty `sensor` or `producer` as missing, as PONZI does. C1's declaration is unchanged; the engine report's declaration is unchanged (the check's name, severity and rule are the same, read as PONZI reads them).
5. **Docstrings (ponzi-pipeline).** "request config" becomes "onboarding spec" where it names C17.

**The contract pages**, in ponzi-suite, in the same change (code first): C3 (`pix_y`, `pix_x` int32, no note on the declaration), C18 (one reading of `identity`), C11, C22 and C25 (their openers raise `ContractError`), and the Store formats index (every reader refuses another zarr format; every validating opener raises `ContractError`), taking back the exceptions the 2026-11-12 fixes wrote there.

## Do results change?
No. No number a run, a calibration or a detection computes changes. What changes is what is refused: a zarr v2 store where one was read before (PONZI writes none), and a pixel sample of C3's old version, which is made again.

## Tests
- ponzi: `test_contract_versions.py` pins C3's new version. A sample written by `extract_sample` and by `export-pixels` validates against the declaration's dtypes. A zarr v2 score, staged, p-value and events store is refused by each site of item 2. `open_pvalue_store`, `open_events_store` and `open_labels` raise `ContractError` (and so `ValueError`) on a broken store.
- ponzi-pipeline: a store with `sensor: ""` gets `identity` warn from the engine and from PONZI, and the `engine_report` check shows no disagreement for it (`test_engine_agreement.py`). The engine's thresholds stay equal to C1's.
- ponzi-models: `null-rows` refuses a zarr v2 `score.zarr`.

## Version
Library: `ponzi` major (C3's contract version changes, a store format by the version rules), `ponzi-pipeline` minor (a check reads one case as PONZI does; a docstring), `ponzi-models` minor (a refusal of what was always outside the rules). Standard: no change; no standard's key moves.
