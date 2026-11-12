# CR-037: the first standard on the CPU, on local disk (phases 8b to 12, the laptop's part)

- **Requested by / date:** owner, 2026-10-23 ("build through phase 8b-12 ... some functionality off the gpu on disk")
- **Status:** implemented on the owner's instruction (2026-10-23), awaiting review; uncommitted (plan decision D10). The HPC part of 8b is open: see ponzi-docs `contributing/roadmap.md`
- **Superseded in part:** `tests/test_retired.py` was deleted (CR-087).

## Why

The first standard is made on ISCE3 stores and a GPU (phase 8b), and needs the cluster. Its lifecycle should still run, as it is, anywhere:

- panel;
- prepare, train, export, register;
- null runs and null rows;
- calibrate, register the calibration;
- the standard bundle.

Then a contributor can change any step and see the whole chain work, and the worker, the server and the front end can be developed and tested against a real standard.

## What changes

| Where | Change |
| --- | --- |
| `ponzi_models.synthetic` | the synthetic bursts and panels of the tests, moved from `tests/panel_world.py` (which re-exports them) |
| `ponzi_models.rehearsal`, `ponzi-models rehearse` | the lifecycle on the CPU, the registry on disk: a tiny TiDE fit (`ml` environment, about 10 s) or the rolling fit; null runs on both layers, the plain and ceiling calibrations, the standard bundle checked against the registry; the stores' engine reports |
| `ponzi_models.standards.workflow`, `ponzi-models standard-workflow` | a standard bundle as the server and the workers run it: the coherence chain (`--source pipeline`: discover, dem, coherence per pair, assemble; `--source stores`), onboard, a staged run with Et, the calibrations from the registry, pvalues, detect, tile |
| `ponzi_models.panels.cells` | the index arrays are copied before they are shuffled. pandas 3.1 hands out read-only views, which made `build_cells` fail; same values, same splits |
| `ponzi-spec` collections | `ponzi-pairs` gains the optional asset `acquisitions` |
| docstrings | every public name of ponzi-spec and ponzi-pipeline is documented; `packages/core/tests/test_docstrings.py` holds all four distributions to it, with the 180 names of `ponzi` and `ponzi_models` undocumented today in `tests/data/docstring_allowlist.txt` (the list only shrinks) |
| `packages/core/tests/test_retired.py` | phase 12: no import of, `sys.path` edit for, or path into the retired repositories |

## Do results change?

No. Every suite passes with the counts of before plus the new tests. The pandas fix gives the same values.

## Tests

- ponzi-core: `pixi run test` 527 passed and 14 skipped; `test-models` 94 passed and 18 skipped, and 112 in `-e ml`; `test-pipeline` 82; `test-spec` 39. The same four suites pass in ponzi-service's environment (pandas 3.1).
- ponzi-service: `test_standard.py`, where a rehearsed standard runs through the server and a worker, and `test_watched.py`.

## Version

- `ponzi-models` 0.3.0: new modules and commands, and `tests/panel_world.py` re-exports.
- `ponzi-spec` 0.3.0: not yet released.
