# CR-048: the repositories are code only; what PONZI runs from lives in ponzi-suite

- **Requested by / date:** owner, 2026-11-04 ("move all the yamls including panels to suite. running core to generate the panel requires passing the path within suite. same with forecasters."; "core should be code only"; and, for this, "you may run git init this one time").
- **Status:** implemented on the owner's instruction (2026-11-04), awaiting review; uncommitted. ponzi-suite is now a git repository (`git init`), with nothing committed.

## Why

ponzi-core held code next to the files PONZI runs from: panel definitions, forecaster specs, run configs and test cases. They change for different reasons and at different paces, and the files are shared by every repository. They belong to the hub, ponzi-suite, versioned in its git. The code repositories hold only code.

## What changes

| From ponzi-core | To ponzi-suite |
| --- | --- |
| `panels/majortom-global/` | `panels/majortom-global/` |
| `data/forecasters/tide/` | `forecasters/tide/` |
| `data/run_configs/exp_b5h5_base.yaml` | `run_configs/exp_b5h5_base.yaml` |
| `testcases/` (gaza) | `testcases/` |
| `data/standards/` (empty) | none (standards are made into the PONZI home) |

- **Commands take paths into the suite.** There is no lookup by name: for example `ponzi-models panel-check ../ponzi-suite/panels/majortom-global`, `ponzi-models train --spec ../ponzi-suite/forecasters/tide/candidates/previous.yaml`, and `--recipe ../ponzi-suite/testcases/gaza/recipe.yaml`. Messages and help texts name the suite.
- **The schemas stay in ponzi-core,** as code: `ponzi_spec.panel`, `TideSpec`, `RunConfig`, `DetectionRecipe`.
- **Tests:**
  - The tests that check the suite's files (`test_panels.py`, `test_testcases.py`, the candidate files in `test_training_missing.py`) find it as `$PONZI_SUITE`, else `ponzi-suite/` beside ponzi-core, and are skipped without it.
  - The reference tests keep their own fixtures, so they need no suite: the release recipe is inline in `test_products_detect.py`, and `test_config.py` and `test_rolling.py` read `tests/data/exp_b5h5_base.yaml`, a copy, because they pin its config hash.
  - The tests' golden arrays and the docstring allowlist stay in `tests/data/`. They are part of the tests.
- **ponzi-suite:** `git init`; `.claude/settings.local.json` is ignored; the README gains a section on these folders.

## Do results change?

No. Every file moved unchanged apart from `extends:` paths and comments, and every config resolves to the same document.

## Tests

- `pixi run test`, `test-models`, `test-spec` and `test-pipeline` pass with the suite beside ponzi-core.
- With `PONZI_SUITE` pointing at a missing folder, the suite tests are skipped and the rest pass.

## Version

None: no distribution's code changes behaviour.
