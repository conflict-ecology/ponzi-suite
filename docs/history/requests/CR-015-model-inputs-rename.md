# CR-015: `fm_windows` becomes `model_inputs`

- **Requested by / date:** owner, 2026-10-13
- **Status:** signed off 2026-10-13; implemented

## Why

`ponzi.core.forecast.fm_windows` builds the input windows of a learned forecaster (targets, acquisition indicators, covariates) for training and for inference. The name came from the reference implementation's `fm` package and says nothing about what the module does.

## What changes

- The module is `ponzi.core.forecast.model_inputs`. Its functions and classes keep their names (`build_features`, `assemble_windows`, `assemble_single_anchor`, `SingleAnchorTemplate`, `burst_shared_fcov`, ...).
- The test files are `tests/test_model_inputs.py` and `tests/test_model_inputs_single.py`.
- No alias is kept under the old name: the only users are this library and `ponzi-models`, which changes with it.

Left as they are, because they name data and not code:

- the attr `fm_context_depth` of the reference prediction stores (read by `contracts/pred.py`);
- the artifact path `data/models/fm/<fit>/torchscript` inside the registered run configs: the string is part of the config hash (CR-004), so it stays until run configs name a model by its registry id;
- earlier change requests, which record the names of their day.

## Do results change?

No. A file and its imports are renamed; no line of arithmetic changes.

## Tests

The same tests under the new names; the layering test and the results lock unchanged.

## Version

Library: minor (a public module path disappears).
