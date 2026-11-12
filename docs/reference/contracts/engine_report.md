# C18: Engine report and check catalogue

`ponzi.contracts.validate` (PONZI's side) and `ponzi_pipeline.engine` (the engine's side). Two things the coherence engine and PONZI agree on without sharing code:

1. **The check catalogue**: every check a delivered store is judged by, with its rule, threshold, severity, and who runs it. The thresholds are written down here and as constants of `ponzi/contracts/coherence.py`, beside C1's declaration, which `ponzi.contracts.validate` imports (`GAP_FACTOR`, `MIN_VALID_FRACTION`, `RANGE_SAMPLE_STEPS`, `LOW_VALIDITY_FLOOR`, `SNAP_TOLERANCE_DAYS`, `FINITE_FLOOR`; the catalogue itself is `CATALOGUE`); the engine repeats four of them in `ponzi_pipeline/engine.py`, under its own names (`GAP_FACTOR`, `MIN_VALID`, `FINITE_FLOOR`, `SNAP_DAYS`), and a test holds those four equal to C1's (`test_engine_agreement.py`). The engine samples the range on 2 time steps written as a literal, not `RANGE_SAMPLE_STEPS`, and has no `LOW_VALIDITY_FLOOR`, since it does not run `cell_quality`. The thresholds are part of C1's declaration, so a change to them changes C1's `contract_version` (ponzi-core CR-085).
2. **The engine report**: a JSON file the engine writes beside every store it publishes, in the vocabulary of the catalogue, so PONZI can read it however the store was produced and flag any disagreement per check.

The two sides are independent implementations of this page and C1: the engine's checks read the store with zarr and numpy only and import none of `ponzi.contracts.validate`'s checks: from PONZI it imports only the report's declaration and version (`ENGINE_REPORT_SCHEMA`, `ENGINE_REPORT_SCHEMA_VERSION`) and C1's `CONTRACT_VERSION`. Drift is caught, not prevented: the diff shows in the `engine_report` check of `ponzi validate-store` (C15).

## Producer and consumers

Written by the coherence engine (`ponzi_pipeline.engine.checks` and `report`, called by `ponzi_pipeline.assemble.assemble`) after its own checks and before the `_complete` sentinel. Read by `ponzi.contracts.validate` (`read_engine_report`, `check_engine_report`: the `engine_report` check of `validate_store`) and by people. The worker stage `ingest-coherence` refuses a store without the file beside it and copies both into the cache; the file is the `engine_report` asset of a `ponzi-coherence` Item.

## The file

`{burst}.coh.zarr.validation.json`, a sibling of the store like `_complete` (`engine_report_path`):

```json
{
  "schema": "ponzi.engine_report",
  "schema_version": "d3584839241858096bc1b2ee105ca69a",
  "contract_version": "d30f943e410871ccabe4ee78e978dbf4",
  "burst_id": "t021_043813_iw2",
  "store": "t021_043813_iw2.coh.zarr",
  "producer": "ponzi-pipeline 0.4.2",
  "validator": "ponzi-pipeline 0.4.2 engine checks",
  "validated_at": "2026-09-10T14:03:11Z",
  "request": null,
  "verdict": "pass",
  "reason": "",
  "checks": [
    {"name": "structure", "severity": "ok", "detail": "...", "value": null, "items": []}
  ]
}
```

| Field | Meaning |
|---|---|
| `schema`, `schema_version` | `ponzi.engine_report`, the hash of the report's declaration (`ENGINE_REPORT_SCHEMA_VERSION`, `ponzi.contracts.validate`; the engine imports it). PONZI warns on another schema or another version |
| `contract_version` | the C1 version the checks were written against (C1's hash; the engine imports it). A mismatch with PONZI's is a warning that names both, never a failure |
| `burst_id`, `store` | the burst and the store's directory name |
| `producer`, `validator` | the writer and the validator, name and version |
| `validated_at` | UTC timestamp. Allowed here: the report is the engine's record; PONZI's own report stays reproducible |
| `request` | the engine always writes `null`; PONZI does not read it |
| `verdict` | `pass`, `fail`, or `published_with_fail` with a non-empty `reason`. The engine writes `fail` with the failed check names as `reason` when any check fails, else `pass`. A store with verdict `fail` must not carry `_complete`. PONZI warns on `published_with_fail` (naming the reason) and on any other value than the three |
| `checks[]` | `name` from the catalogue (names outside it are allowed and ignored by the comparison), `severity` in `ok, info, warn, fail`, `detail` free text, `value` a number or null, `items` a list of strings |

## The catalogue

Level `burst`. "engine" means the check is required in every engine report; "engine (optional)" means the engine runs it when it can (`ponzi_pipeline.engine` does not); "PONZI" means `ponzi.contracts.validate` alone. PONZI runs every row, and one check outside the catalogue: `window`, a fail when the `time` coordinate's length is not `coh`'s time dimension.

| Check | Rule | Severity | Who |
|---|---|---|---|
| `structure` | `coh (time, y, x, baseline)` with `time`, `y`, `x`, `baseline` coordinates of matching length; optional pair tables `bperp`, `platform`, `platform_secondary`, `secondary_date`, `n_finite` are `(time, baseline)`; `coh` float32 or float64 | fail | engine |
| `dtype` | written only for a float64 `coh` (cast to float32 on read); any dtype other than float32 or float64 fails `structure` | warn | engine |
| `baseline_days` | attr present, one int per baseline position, positive, strictly increasing; `items` = the list | fail | engine |
| `revisit_days` | attr present, a positive int; `value` = the int | fail | engine |
| `time_axis` | strictly increasing, no duplicates; a gap above `GAP_FACTOR` (1.5) times the median spacing warns; `value` = the median spacing in days | fail, warn | engine |
| `chunking` | time chunk exactly 1; tiled spatial chunks warn | fail, warn | engine |
| `valid_pixels` | present, `(y, x)`, at least one nonzero pixel (NaN counts as 0); below `MIN_VALID_FRACTION` (1 %) or a dtype other than uint8 warns | fail, warn | engine |
| `range` | finite values in `[0, 1]`, sampled on `RANGE_SAMPLE_STEPS` (2) evenly spaced time steps, baseline 0 | warn | engine |
| `crs` | `epsg` attr present, an int; `value` = the int | fail | engine |
| `identity` | `sensor`, `producer`, `contract_version` attrs present, an empty `sensor` or `producer` counting as missing (ponzi-core CR-092); PONZI also warns when `contract_version` is not C1's | warn | engine |
| `consolidated` | consolidated metadata present | warn | engine |
| `complete_sentinel` | `_complete` sibling present (info for a store not named `*.coh.zarr`) | fail | engine |
| `partial` | no `.partial` sibling (info for a store not named `*.coh.zarr`) | fail | engine |
| `pairs_declared` | `n_pairs_packed` attr equals the populated cells of the platform table (fail); cell collisions (`n_cell_collisions`) or a `secondary_date` off `time - baseline_days[b]` by more than `SNAP_TOLERANCE_DAYS` (3) days warn; info without a platform table | fail, warn, info | engine |
| `chunk_completeness` | every `coh` chunk holding a declared pair exists on disk (a directory listing of the zarr v3 layout), and every other array has all its chunks; absent chunks without declared pairs and whole absent baseline blocks are info | fail, info | engine |
| `availability_matrix` | from `n_finite (time, baseline)` (C1): a declared cell with `n_finite` 0 outside an absent chunk is lost data (fail); data in an undeclared cell warns. PONZI never reads the slabs and, without the table, trusts the engine and says so (info) | fail, warn, info | engine |
| `finite_fraction` | per populated acquisition, the best baseline's `n_finite` over the valid footprint at or above `FINITE_FLOOR` (0.5); `items` = the slices below; info without `n_finite` or valid pixels | warn, info | engine |
| `generation` | the archive folder (`coherence/<generation>/`) equals the `estimation_strategy` attr and the expected generation (`validate_store(expected_generation=)`); info outside an archive tree | warn, info | engine (optional) |
| `cell_quality` | populated cells flagged low validity (`cell_quality`) at most `LOW_VALIDITY_FLOOR` (10 %); info without the table, without a platform table, or with no declared cell | warn, info | engine (optional) |
| `engine_report` | this report against PONZI's run, compared last: info when absent (fail with `require_engine_report=True`); warn on an unreadable file, another schema, another schema version, a contract version other than PONZI's, a verdict `published_with_fail` or outside the three, or any catalogue check present in both whose severity differs (`items` = those checks) | fail, warn, info | PONZI |

## What the engine does with it

Per burst, before publishing (`ponzi_pipeline.assemble.assemble`): write into `{burst}.coh.zarr.partial` one acquisition at a time (counting `n_finite`), consolidate the metadata, run its own checks (every `engine` row above; the two sentinel checks state what publication then makes true), write the report, and on `pass` rename to `{burst}.coh.zarr` and write `_complete`. A store that fails stays `.partial` and the failure is raised (`AssembleError`); the engine writes no `published_with_fail`.

The two implementations give every shared check the same severity on a conforming store, a float64 `coh` store and a store with a declared pair's chunk absent (ponzi-pipeline `tests/test_engine_agreement.py`). They differ only where the engine checks a store being published: the two sentinel checks.
