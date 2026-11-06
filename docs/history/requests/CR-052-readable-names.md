# CR-052: readable names for forecasters, panels and models

- **Requested by / date:** owner, 2026-11-05 ("add in a human readable naming convention for forecasters and panels"; the ids renamed too, the old ones kept).
- **Status:** implemented on the owner's instruction (2026-11-05), awaiting review; uncommitted

## Why

The forecasters were named by codes only their authors could read: `tide_c30_pdcompact`, `tide_c30_pdcompact_previous_cd`, `tide_c30_gaza_f1p`, and models such as `tide_c30_pdcompact_mt0.4`. Panels already had a readable name (`majortom-global`, CR-046), but no rule held new ones to it.

## What changes

**The convention, `ponzi_spec.naming`.**
- A name is lowercase words of letters and digits joined by single hyphens, starting with a letter (`NAME`, `is_name`, `check_name`), read from the general to the specific.
- A name has no version, date, sensor, seed or code; those are written in the file.

| What | Name | Example |
| --- | --- | --- |
| panel | `<design>-<scope>` | `majortom-global` (cited `majortom-global@0.4.0`) |
| forecaster | `<family>-<inputs>` | `tide-weather` |
| variant | `<forecaster>-<change>...` | `tide-weather-fill-median` (`variant`) |
| fit at another seed | `<forecaster>-seed<N>` | `tide-weather-fill-median-seed43` (`seeded`) |
| model | `<forecaster>--<panel>-<version>` | `tide-weather--majortom-global-0.4.0` (`model_id`, `parse_model_id`) |

A model id has no `@`, since a registry reference is already `registry:<model id>@sha256:<digest>`.

**Where it applies.**
- Panel definitions (`ponzi_spec.panel`) and panel specs (`ponzi_models.panels.spec.PanelSpec.id`) take the `NAME` pattern. `majortom-global` and the tests' `test-panel` already follow it.
- `ponzi-models train --seed N` names the fit `<fit_id>-seed<N>` (was `_s<N>`).
- `ponzi-models export` names the artifact by its model id `<fit_id>--<panel id>` (was `<fit_id>_<panel id>`). A fit id outside the convention is joined the same way.
- `TideSpec` takes `formerly`: the id a spec had before, a record only.
- Fit ids themselves are not refused when they break the convention (tests and old specs use `tide_tiny`). ponzi-suite's files are held to it by `packages/models/tests/test_suite_names.py`: a forecaster's name is its folder and file, a variant's its base's plus its file, a test case's its base's plus the case, a panel's its folder.

**ponzi-suite renamed.**
- `forecasters/tide/c30_pdcompact.yaml` becomes `weather.yaml` (`tide-weather`).
- The candidates become:
  - `fill-constant`, `fill-median`, `fill-previous`;
  - `fill-previous-augmented`, `fill-previous-augmented-radar-moisture`, `fill-previous-context-dropout`;
  - `fill-sentinel` (formerly `sentinel_flag`) and `fill-sentinel-no-flags` (formerly `sentinel`).
- Gaza's is `tide-weather-gaza-finetune`.
- Each spec keeps its old id as `formerly:`.
- Every spec resolves to the same keys as before apart from `fit_id` and `formerly` (tested).
- Old registered model names in the headers (`tide_c30_pdcompact_mt0.4`) stay, as the names they were registered under.
- The suite's `docs/reference/naming.md` sets out the convention, the words in use and the former names.

## Do results change?

No. The keys of every fit are unchanged, and names enter no config hash, content id or prepared-files identity. The fits, artifacts and registry entries made under the old ids keep those ids; a new fit of a renamed spec is made under its new name.

## Tests

- ponzi-spec: `test_naming.py`.
- ponzi-models:
  - `test_suite_names.py`;
  - `test_training_missing.py` (the suite's specs under their new names, with `formerly`; seeded names);
  - `test_training_fit.py` (artifact names).
- Every suite, and the torch tests in the `ml` environment.

## Version

- `ponzi-spec`: minor (a new module).
- `ponzi-models`: minor (the seeded fit and the artifact are named differently).
- Standard: none.
