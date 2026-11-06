# C18: Engine report and check catalogue

> Note (CR-008, 2026-10-12; CR-032): the comparison lives in `ponzi.contracts.validate` (command `ponzi validate-store PATH [--json]`), and the engine's own checks in `ponzi_pipeline.engine`, run by `ponzi_pipeline.assemble` (`ponzi-pipeline assemble`, the ponzi-worker stage `assemble`). The catalogue holds the store checks only; the request-row checks (`window`, `expected`, `platform_vs_sat`, `missing_acquisitions`, `baseline_set`), the row digest and the AOI checks (`targets`, `aoi_cover`, `bursts_delivered`, `aoi_cover_union`, `aoi_window`, `baselines_consistent`, `crs_consistent`, `revisit_consistent`, `track_dates_consistent`, `event_slots`) of the former catalogue are run by no code here.

Status: implemented 2026-09-09; `ponzi.contracts.validate`
(PONZI's side) and `ponzi_pipeline.engine` (the engine's side, CR-032). The
two are independent implementations of this page and C1: the engine's checks
read the store with zarr and numpy only and import nothing of
`ponzi.contracts.validate`, and PONZI compares the report the engine writes
with its own run.

## Purpose

Two things the coherence engine and PONZI agree on without sharing code:

1. **The check catalogue**: every check a delivered store is judged by, with
   its exact rule, threshold and severity, and who runs it. The thresholds
   are written down ONCE, here and as the constants at the top of
   `ponzi/contracts/validate.py` (`GAP_FACTOR`, `MIN_VALID_FRACTION`,
   `RANGE_SAMPLE_STEPS`, `LOW_VALIDITY_FLOOR`, `SNAP_TOLERANCE_DAYS`,
   `FINITE_FLOOR`; the catalogue itself is `CATALOGUE`); the engine repeats
   them in `ponzi_pipeline/engine.py`. A change to either is a
   `contract_version` bump.
2. **The engine report**: a JSON file the engine writes beside every store it
   publishes, in the vocabulary of the catalogue, so PONZI can read it
   regardless of how it was produced and flag any disagreement per check.

Drift is caught, not prevented: two independent implementations that must
agree on every store, with the diff visible in the `engine_report` check of
`ponzi validate-store`.

## Producer and consumers

Written by the coherence engine (`ponzi_pipeline.engine.checks` and
`report`, called by `ponzi_pipeline.assemble.assemble`) after its own checks
and before the `_complete` sentinel; read by `ponzi.contracts.validate`
(`read_engine_report`, `check_engine_report`: the `engine_report` check of
`validate_store`) and by people. The ponzi-worker stage `ingest-coherence`
refuses a store without the file beside it and copies both into the cache;
the file is the `engine_report` asset of a `ponzi-coherence` Item.

## The file

`{burst}.coh.zarr.validation.json`, a sibling of the store like `_complete`
(`engine_report_path`):

```json
{
  "schema": "ponzi.engine_report",
  "schema_version": 1,
  "contract_version": 1,
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
| `schema`, `schema_version` | `ponzi.engine_report`, 1. PONZI warns on another schema or a newer version |
| `contract_version` | the C1 version the checks were written against (1). A mismatch with PONZI's is a warning that names both, never a failure |
| `burst_id`, `store` | the burst and the store's directory name |
| `producer`, `validator` | the writer and the validator, name and version |
| `validated_at` | UTC timestamp. Allowed here: the report is the engine's record; PONZI's own report stays reproducible |
| `request` | `null` when the store was validated without a request row (the engine always writes `null`); else the request `name` and `row_digest`. PONZI does not read it |
| `verdict` | `pass`, `fail`, or `published_with_fail` with a non-empty `reason` (for instance "ASF has no granules after 2024-03-01"). The engine writes `fail` with the failed check names as `reason` when any check fails, else `pass`. A store with verdict `fail` must not carry `_complete`. PONZI warns on `published_with_fail` (naming the reason) and on any other value than the three |
| `checks[]` | `name` from the catalogue (names outside it are allowed and ignored by the comparison), `severity` in `ok, info, warn, fail`, `detail` free text, `value` a number or null, `items` a list of strings |

## The catalogue

Level `burst`. "Engine" means the check is required in every engine report;
"engine (optional)" means the engine runs it when it can (`ponzi_pipeline.engine`
does not); "PONZI" means `ponzi.contracts.validate` alone. PONZI runs every
row.

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
| `identity` | `sensor`, `producer`, `contract_version` attrs present (PONZI also takes `writer_command` or `schema` as the producer of a legacy store) | warn | engine |
| `consolidated` | consolidated metadata present | warn | engine |
| `complete_sentinel` | `_complete` sibling present (info for a store not named `*.coh.zarr`) | fail | engine |
| `partial` | no `.partial` sibling (info for a store not named `*.coh.zarr`) | fail | engine |
| `pairs_declared` | `n_pairs_packed` attr equals the populated cells of the platform table (fail); cell collisions (`n_cell_collisions`) or a `secondary_date` off `time - baseline_days[b]` by more than `SNAP_TOLERANCE_DAYS` (3) days warn; info without a platform table | fail, warn, info | engine |
| `chunk_completeness` | every `coh` chunk holding a declared pair exists on disk (a directory listing, zarr v3 or v2 layout), and every other array has all its chunks; absent chunks without declared pairs and whole absent baseline blocks are info | fail, info | engine |
| `availability_matrix` | from `n_finite (time, baseline)`, the count of finite pixels the engine writes per cell (C1): a declared cell with `n_finite` 0 outside an absent chunk is lost data (fail); data in an undeclared cell warns. The engine computes the count while writing each slab (`ponzi.contracts.coherence.CoherenceWriter`); PONZI never reads the slabs (80 GB per BRIGHT burst) and, without the table, trusts the engine and says so (info) | fail, warn, info | engine |
| `finite_fraction` | per populated acquisition, the best baseline's `n_finite` over the valid footprint at or above `FINITE_FLOOR` (0.5); `items` = the slices below; info without `n_finite` or valid pixels | warn, info | engine |
| `generation` | the archive folder (`coherence/<generation>/`) equals the `estimation_strategy` attr and the expected generation (`validate_store(expected_generation=)`); info outside an archive tree | warn, info | engine (optional) |
| `cell_quality` | populated cells flagged low validity (`cell_quality`) at most `LOW_VALIDITY_FLOOR` (10 %); info without the table | warn, info | engine (optional) |
| `engine_report` | this report against PONZI's run, compared last: info when absent (fail with `validate_store(require_engine_report=True)`); warn on an unreadable file, another schema, a newer schema version, a contract version other than PONZI's, a verdict `published_with_fail` or outside the three, or any catalogue check present in both whose severity differs (`items` = those checks) | fail, warn, info | PONZI |

## What the engine does with it

Per burst, before publishing (`ponzi_pipeline.assemble.assemble`): write into
`{burst}.coh.zarr.partial` one acquisition at a time, consolidate the
metadata, run its own checks (every `engine` row above; the two sentinel
checks state what publication then makes true), write the report, and on
`pass` rename to `{burst}.coh.zarr` and write `_complete`. A store that
fails stays `.partial` and the failure is raised (`AssembleError`); the
engine writes no `published_with_fail`. PONZI's reference run for comparison
is `ponzi validate-store PATH`; nothing in the engine imports
`ponzi.contracts.validate`.

The two implementations give every shared check the same severity on a
conforming store, a float64 `coh` store and a store with a declared pair's
chunk absent (`ponzi-pipeline` `test_engine_agreement.py`, CR-051). They
differ only where the engine checks a store being published: the two
sentinel checks (above), and `chunk_completeness` reads the zarr v3 layout
only, the one the engine writes.

## Interim (2026-09)

Stores assembled by `ponzi-pipeline assemble` carry both the report and
`n_finite`; archive stores made before may carry neither.
`ponzi validate-store` treats an absent report as info and an absent
`n_finite` as "availability trusted to the producer" (info); nothing on
PONZI's side ever reads every acquisition (80 GB per BRIGHT burst, far beyond
the five minute budget per burst). `validate_store(...,
require_engine_report=True)` makes an absent report a failure; the command
has no flag for it.
