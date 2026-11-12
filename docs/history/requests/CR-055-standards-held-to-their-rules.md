# CR-055: standards held to their rules, and the first standard file

- **Requested by / date:** owner, 2026-11-05 (approved the second change request of the versioning gaps; "add a standards file").
- **Status:** implemented on the owner's instruction (2026-11-05)
- **Superseded in part:** specs are cited by hash, not version (CR-083), a standard has no workflow (CR-084), and the standard file is now 2.0.0.

## Why

A standard recorded `requires` but nothing checked it. It named no panel, so nothing tied its model and calibrations to one. No check kept calibration cells out of training. A new version could change anything, whatever its number said. And no standard file existed anywhere.

## What changes

**`ponzi_models.standards.Standard`:**
- `panel: <id>@<version>`, required.
- `status: published | draft`. A draft may leave out `run_config_hash` and `calibrations`; a published standard must have them.
- Each value of `requires` must be a PEP 440 specifier. The new dependency `packaging` parses them.

**`Standard.check(registry, panels=None, installed=None)`** refuses a draft, and checks as before and also:
- every calibration was made on the standard's panel;
- the model card's `panel_id`, when recorded, is that panel;
- the installed distributions meet `requires` (`unmet_requirements`);
- with the built panel in `{home}/panels/<id>@<version>` (or `panels`), no training or validation cell in the artifact's `meta.json` is a test cell of the panel.

It returns notes on what it could not check.

**`check_versions(new, old)`** and **`previous_version(path)`:**
- a version must rise;
- within a major, `RUN_IDENTITY` must not change: sensor, workflow, coherence, onboarding, panel, model and run config hash;
- within a minor, neither may the calibrations or the recipe.

**`ponzi-models check-standard FILE [--registry] [--panels] [--previous]`:**
- holds a standard against the version before it (by default the highest earlier `<id>-<version>.yaml` beside it);
- checks a draft for its form only;
- prints the notes.

**`standard-workflow`** refuses a draft, and writes `requires` into the server's standard.

**ponzi-server:** `catalog.Standard.requires`, carried in each job's payload.

**ponzi-worker:** a job whose `requires` the installed distributions do not meet fails before anything runs, with the reason.

**ponzi-suite:** `standards/` with the draft `s1-general-1.0.0.yaml` on `majortom-global@0.4.0` and a README.

**The rehearsal's standard** names its panel.

## Do results change?

No.

## Tests

- ponzi-models:
  - `test_standards.py`: panel mismatches, unmet and missing requirements, drafts, training cells on test cells, version rules, the previous version found beside a file.
  - `test_suite_standards.py`: every suite standard loads, is named by id and version, names a suite panel at that version, follows the one before, and has its requirements met.
- ponzi-worker `test_loop.py`: a job with unmet `requires` fails and runs nothing.
- The models and service suites.

## Version

- `ponzi-models`: minor (new fields, checks, functions and a dependency). `panel` is required, so existing standard files need it; none is kept in a repository.
- ponzi-server: minor.
