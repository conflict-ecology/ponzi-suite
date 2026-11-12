# CR-046: panels kept in git, named by design

- **Requested by / date:** owner, 2026-11-04 ("I want a panel that is kept track of by git. the burst.geojson, cells.geojson as well as a meta data file containing version. the naming convention should be just a descriptive name not by sensor. majortom-global. so <design><variant>."), after the owner chose the Major TOM panel as what the Gaza work trains and calibrates on.
- **Status:** implemented on the owner's instruction (2026-11-04), awaiting review; uncommitted
- **Superseded in part:** a panel spec has no `version`: its hash is its version, and it lives under `specs/panel_specs/` (CR-047, CR-048, CR-078, CR-083).

## Why

A panel is the set of bursts and cells that a model is trained, validated and calibrated on. A calibration is only meaningful together with the panel whose test split made its null. The panels lived on the HPC (`artifact/majortom/v0.x`). Here, the Major TOM v0.4 panel had been written into `suites/majortom-v0.4/`. But a suite case is a place, not a panel, and neither had a version anyone could cite.

## What changes

- **One folder per panel:** `data/panels/<id>/`, tracked by git, with three files:
  - `panel.yaml`: the id, the **version** (MAJOR.MINOR.PATCH), a description, sub-panels, split counts, the window rule, the footprints' source, the upstream provenance, and the sha256 of the two data files;
  - `bursts.geojson`: each burst's footprint, track, sub-swath, direction, split, cells, window, and whether it was delivered upstream;
  - `cells.geojson`: each cell's outline, split, sub-panel, stratum, window and bursts.
- **Names:**
  - The id is a descriptive `<design>-<variant>`, lowercase and hyphenated, with no sensor and no version: `majortom-global`.
  - A panel is cited as `<id>@<version>`, for example `majortom-global@0.4.0`. Calibrations are named `<model>/<id>@<version>`.
  - The version lives only in `panel.yaml`. Git holds earlier versions: a new version is a commit that bumps it, and can be tagged `panel/<id>@<version>`.
- **Versions:**
  - MAJOR when the data changes (the cells, a split, a window, or the coherence the bursts are made with), because that is a different null.
  - MINOR for added metadata. PATCH for wording.
  - `0.y` versions are panels inherited from the monorepo and the HPC. A rebuild from these repositories is `1.0.0` or later.
- **The first panel:** `data/panels/majortom-global`, version 0.4.0. It is the upstream Major TOM panel v0.4 (`panel_digest` `0281d85b…`), moved from `suites/majortom-v0.4/` with its data unchanged. It has two sub-panels: `majortom` (40 test cells, 8 per climate) and `majortom-arid` (8).
- **`suites/`** keeps only places (`gaza`).
- **The builder's spec files:** CR-031's `data/panels/<id>-<version>.yaml` naming for panel specs is replaced. A spec written for the builder goes into the panel's folder as part of `panel.yaml`, under its own key, when a panel is built from scratch here.

## Do results change?

No. No code changes, and the panel's data is moved unchanged.

## Tests

`packages/core/tests/test_panels.py`:
- every panel folder is named by its id, has a semver version and exactly the three files, and its files match the sha256 in `panel.yaml`;
- every burst has a footprint, and the cells and bursts name each other;
- the split counts match `panel.yaml`;
- `majortom-global` is the upstream v0.4: 487 bursts (396 delivered), 239 cells, its test sub-panels, its digest.

`test_suites.py` covers only places now.

## Version

None: data and tests only.

**Renamed (owner, 2026-11-04):** `suites/` is now `testcases/`, and `test_suites.py` is `test_testcases.py` ("suites is ambiguous. use 'test' or something similar as it is just for testing"). The text above keeps the old name.

**Moved (owner, 2026-11-04, CR-047):** panel definitions live in `panels/<id>/` at the repository root, not `data/panels/`.
