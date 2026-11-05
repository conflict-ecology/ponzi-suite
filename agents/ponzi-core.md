# ponzi-core

@shared.md

The PONZI library. Read `README.md` first. This repository is under a strict change process: nothing changes without a written request in `docs/requests/` that the owner has signed off.

- One package `ponzi`; subpackages import one way only (`packages/core/tests/test_layering.py`): `contracts` at the bottom, `core` (the forecast run) on it, the rest on those two; `grid` (geometry) imports no other subpackage. None of `contracts`, `core`, `calibration`, `evaluation`, `grid`, `products`, `stac` loads the geospatial stack or torch at import; `contracts`, `core` and `evaluation` name no dataset.
- Every change ends with `pixi run test` green and a `CHANGELOG.md` entry. The golden files under `packages/core/tests/data/` lock the numbers: never regenerate one to make a test pass unless the change request says results change.
- Distributions under `packages/`: `spec` (`ponzi-spec`), `core` (`ponzi`), `pipeline` (`ponzi-pipeline`), `models` (`ponzi-models`). `ponzi` never imports `ponzi_pipeline` or `ponzi_models`; `ponzi_models` may import `ponzi_pipeline`, never the reverse. Tests: `pixi run test`, `test-spec`, `test-pipeline`, `test-models` (all of models' in `-e ml`). Service and front-end code do not belong here (ponzi-service, ponzi-visual), nor the files PONZI runs from (panels, forecasters, run configs, test cases: ponzi-suite). The tests of those files find the suite as `$PONZI_SUITE`, else `../ponzi-suite`, and skip without it.
