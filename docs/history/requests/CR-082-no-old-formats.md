# CR-082: no guards for old formats, no old-package fields in the panel

- **Requested by / date:** owner, 2026-11-12 ("remove Old-format guards backwards compatabiility to old repos are no longer needed. Scoring specs: remove if redundant", then "remove Old-package fields")
- **Status:** signed off (2026-11-12), implemented (unreleased)

## Why
The code still carried guards whose only job was to explain a format of before: files, registry entries and configs from the retired repositories or from earlier releases of this one. Nothing of that kind is kept any more, so the guards are dead weight. The panel spec `majortom-global` carried fields of the package it was taken from (`in_v0_4_package`, its delivery `reason`, `outline` and `window_from` naming its `aois.csv`, and the package's subpanel names `majortom_v1` and `majortom_arid_v1`), which nothing reads.

## What changes
- Removed, each now an ordinary validation failure or lookup miss:
  - the detection spec's `preset` refusal (`detection_spec_fields`, in ponzi-core and in ponzi-worker's detect stage);
  - `SpecFolderMoved`, for spec folders of before CR-078;
  - the registry's refusal of an entry of before CR-070 (`RENAMED_CR070`, `REGISTER_AGAIN`), and of a calibration with `run_config_hash`;
  - the standard's refusal of the field names of before CR-070, of a spec given inline, and of a versioned panel reference;
  - the panel spec's refusal of an inline coherence spec;
  - `register-model`'s reading of artifacts of before CR-070 (`fit_id`, `fit_spec`) and of before CR-081 (`formerly`);
  - the deployment config's refusal of a `credentials` section (CR-059).
- Kept, because they are rules of the current format, not explanations of an old one: a panel spec has no `version`, and no spec file says its name (CR-081).
- The scoring spec's `name` is kept: it is not redundant. The registry keeps a model's scoring spec as `scoring_spec.yaml`, and the null runs run that copy as it is, so the `name` inside it is what names the runs and the stamp. A spec in ponzi-suite leaves it out and is named by its file.
- `majortom-global`: `in_v0_4_package`, `reason`, `outline` and `window_from` are removed from its geojson, and `subpanel` takes the names of `panel.yaml`'s `subpanels` (`majortom`, `majortom-arid`). The two sha256 of `panel.yaml` follow.

## Do results change?
No computation changes. `majortom-global`'s hash changes with its files; nothing is built from or pinned to it yet.

## Tests
The tests of the removed guards are removed; the cases that remain refused are checked as ordinary failures. `test_panels.py`: no old-package field in the panel, the subpanel counts per split those of `panel.yaml`.

## Version
Library: `ponzi-spec`, `ponzi` and `ponzi-models` minor; ponzi-worker patch. Standard: no change.
