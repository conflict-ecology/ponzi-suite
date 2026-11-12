# CR-078: the spec folders under one specs/ folder

- **Requested by / date:** owner, 2026-11-12 ("place all specs under a parent specs dir")
- **Status:** signed off (2026-11-12), implemented (unreleased)
- **Superseded in part:** the `SpecFolderMoved` refusal was removed (CR-082).

## Why
The six spec folders (CR-070) sat at the top of the PONZI home and of ponzi-suite, among the home's data folders and the suite's docs, standards and test cases. One parent folder groups what a person writes.

## What changes
- The six folders keep their names and move under `specs/`, in the home and in the suite: `specs/training_specs/`, `specs/scoring_specs/`, `specs/panel_specs/<id>/`, `specs/detection_specs/`, `specs/coherence_specs/`, `specs/onboarding_specs/`. `ponzi_spec.home.Layout` gains `specs`; its six spec properties point under it. `ponzi_spec.specs.SPECS_DIR` names the folder; `spec_folders` and `find_spec` look in `<home>/specs/<kind>_specs/`, then `<suite>/specs/<kind>_specs/`.
- A home or suite that still holds a spec file in a folder of before (`<root>/<kind>_specs/`) is refused when a spec of that kind is looked up (`SpecFolderMoved`, saying where to move it), so a working copy is never passed over for the suite's without a word. An empty old folder is no matter.
- ponzi-suite: the six folders are moved with `git mv`; the one `extends:` across folders (`testcases/gaza/training.yaml`) points at `../../specs/training_specs/tide/weather.yaml`.
- The paths in the code's help texts and docstrings, the tests, the READMEs and the suite's current docs say `specs/<kind>_specs/`. The history (the changelog's released entries, the change requests) is left as written.
- Standards are not specs (`ponzi_spec.specs` names six kinds): ponzi-suite `standards/` and the home's `standards/` stay where they are.

## Do results change?
No. A spec's hash is that of its resolved content without its name, never of its path, and a panel spec's covers its geojson by names relative to its folder, so every hash, every frozen name in a registry's `specs.json` and every content id is the same. A spec read from the suite records the suite commit it was read from, which is a new commit once the move is committed.

## Tests
`test_specs.py`: the home's six folders are under `specs/`; the lookup finds a name in the home's `specs/` first, then the suite's; a spec left in an old folder of the home or of the suite is refused with where to move it, and an empty old folder is not. The suite's own tests (`test_suite_names.py`, `test_panels.py`, `test_testcases.py`, `test_standards.py`, `test_training_missing.py`) read the moved folders.

## Version
Library: `ponzi-spec`, breaking for the layout of the home and the suite (a home or suite of before must move its spec folders); no store format or result changes. Standard: no change.
