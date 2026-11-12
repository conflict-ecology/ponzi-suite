# CR-081: a spec is named by its file

- **Requested by / date:** owner, 2026-11-12 ("run through the spec system. remove all stale items, comments, and references to old repos. every spec yaml should have a human or agent given file name which should be fairly unique and indentifiable by dependent specs (e.g panel). The panel should have the structure is is now and the unique name being the dir name.")
- **Status:** signed off (2026-11-12), implemented (unreleased)
- **Superseded in part:** `register-model` no longer reads `formerly` (CR-082).

## Why
A spec's name lived in two places. A training spec said its name in a `training_id` key, and its file had another name (`tide/candidates/fill-median.yaml` was `tide-weather-fill-median`), so a spec could only be found by name by opening every file. A panel spec said its name in `id` and in its folder's name, and was refused when they differed. The test cases' specs were named by their place (`testcases/gaza/training.yaml`, `testcases/gaza/detection.yaml`), so nothing could name them. The other kinds were already named by their files. The files also carried history that no longer applies: `formerly` keys, the registered models and scoring specs of the old registry, scripts and paths of the retired repositories (`hpc/*.sbatch`, `training/train.py`, `majortom-package`, the `upstream` block of the panel), and change-request trails in their comments.

## What changes
- A spec's name is its file's name without `.yaml`; a panel spec's is its folder's. No spec file says its name: `training_id` in a training spec and `id` in a panel spec's `panel.yaml` are refused, and the loaders fill them from the file or folder. Writers leave them out.
- `find_spec` looks a name up as `<name>.yaml` anywhere under the kind's folder (subfolders only arrange them) and, for a panel spec, as the folder `<name>/`. Two files of one name in one folder are refused.
- `TrainingSpec.formerly` is removed. A fit exported before this is still read: its recorded spec's `formerly` is dropped, like its `fit_id` and `fit_spec` are renamed.
- ponzi-suite: the training specs are renamed to their names (`tide/tide-weather.yaml`, `tide/candidates/tide-weather-fill-median.yaml`, ...); the Gaza test case's training spec is `specs/training_specs/tide/tide-weather-gaza-finetune.yaml` and its detection spec `specs/detection_specs/single-path-gaza-release.yaml`; `testcases/gaza/` keeps the area. `panel.yaml` of `majortom-global` loses `id` and `upstream`. Every spec's comments say what it is and how to use it, without history.
- Docs, docstrings and tests follow.

## Do results change?
No computation changes. The hashes of the training specs change (the removed `formerly` was hashed, as null where absent) and so does `majortom-global`'s (its `upstream` block was hashed). No standard is published and the registry holds none of them, so nothing is pinned to the old hashes; a fit made before keeps its recorded hash.

## Tests
`test_specs.py`: a name is found under subfolders, two files of one name are refused. `test_training_missing.py`, `test_spec_names.py`: `training_id` in a file is refused and the name is the stem. `test_panel_folder.py`, `test_panel_build.py`: `id` in `panel.yaml` is refused, the name is the folder's, a written spec has no `id`. `test_suite_names.py`: every spec of the suite is named by its file, the names unique within a kind. `test_panels.py`, `test_testcases.py`: the moved files.

## Version
Library: `ponzi-spec` and `ponzi-models` minor (a key refused that was read). Standard: no change.
