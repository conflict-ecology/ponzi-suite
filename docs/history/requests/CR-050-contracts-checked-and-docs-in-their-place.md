# CR-050: the contracts checked against the code, and every document in its place

- **Requested by / date:** owner, 2026-11-04 ("lets make all changes", the recommendations on organizing the Markdown files; "update all the contracts to match the current repo functionality"; "remove what is necessary").
- **Status:** implemented on the owner's instruction (2026-11-04), awaiting review; uncommitted
- **Superseded in part:** contracts and change requests live in ponzi-suite, not the ponzi-core checkout (CR-071).

## Why

The store contracts were written for the monorepo, then carried through the packages layout, the pipeline, the panels, the service and the home. Many named modules, commands, producers and attrs that moved or no longer exist. Two system-wide documents sat in ponzi-service, and the contracts and change requests were visible only in ponzi-core.

## What changes

**Contracts (`docs/contracts/`):**
- Every remaining contract was checked against the code: module paths, functions, commands and flags, arrays, attrs, defaults, locations (the PONZI home), producers and consumers (including ponzi-worker stages and ponzi-models), and invariants. Where it was cheap, a fixture store was built and its arrays listed. Each now states what the code does.
- C1 to C11, C18, and C20 to C26 are kept and updated.
- C15, C16 and C17 are cut to the part code here still uses: one store's validation report (`validate_store`), the design table, and the `onboarding:` section.
- C11 (labels) stays: the library reads and writes it, although no command calls it today.
- **Removed**, because no code in ponzi-core or ponzi-service reads or writes them: C12 (eval result), C13 (AOI registry), C14 (frozen request), C19 (data package). Their formats stayed in the monorepo.
- The index (`README.md`) is rewritten, and references to the removed ids in other contracts, docstrings and the suite's test cases are updated.

**Documents in their place:**
- `ponzi-service/docs/overhaul-plan.md` and `current-system.md` move to ponzi-suite `docs/history/`, since they cover the whole system. Links follow.
- ponzi-suite's docs build publishes ponzi-core's contracts (*Reference › Store contracts*) and change requests (*History*) from the ponzi-core checkout (`$PONZI_CORE`, else `../ponzi-core`), never copied (`hooks/ponzi.py`). Links into code become GitHub addresses.
- `.pytest_cache/` is ignored in ponzi-service, as it already was in ponzi-core.

## Found in the code, not changed here

All fixed in CR-051.


- `ponzi.stac.items.RUN_ASSETS` names `all_channels.zarr`, but the runner writes `channels_z.zarr`, so C21 never appears in a run Item.
- `ponzi_pipeline.assemble` does not write `estimator_params`, which the default `noise_floor: derived` needs. A default run on an assembled store would likely be refused (not run).
- No command builds a format 3 (staged) calibration, so staged runs get final codes only.
- `RunRequest.calibration_window` is recorded but never used, yet it enters the worker's content id.
- A run config that uses relative `extends:` stops resolving once it is copied (worker temp file, registry `run_config.yaml`).
- `ponzi_pipeline.engine` and `ponzi.contracts.validate` disagree on some checks (`dtype`, `structure` on float64 `coh`, `chunk_completeness`).
- Small things:
  - `ponzi --help` lists only three of its commands;
  - `make_coherence_fixture` gives a `.coh` suffix in `burst_id` for `*.coh.zarr`;
  - `pred.zarr` is listed in `written` even when it is not made;
  - `n_null_by_stage` keys differ between provenance and meta;
  - stale `ops/` paths in runner docstrings.

## Do results change?

No. Documentation, docstrings, a test's name, and file moves only.

## Tests

`pixi run test`, `test-spec`, `test-pipeline` and `test-models`, and ponzi-service. The tests of the contracts' stores pass. The docs build with `mkdocs build --strict`, with the contracts and requests published.

## Version

None.
