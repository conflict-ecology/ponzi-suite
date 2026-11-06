# Standards

One file per standard version, `<id>-<version>.yaml`: everything a watched area runs (`ponzi_models.standards`, ponzi-core CR-028, CR-055 and CR-070). A standard's id is `<sensor>-<scope>` (`s1-general`, `s1-gaza`; `ponzi_spec.naming`), and it names its specs: its panel spec (`panel_specs/`), its coherence, onboarding and detection specs (`coherence_specs/`, `onboarding_specs/`, `detection_specs/`), and its model's scoring spec by its hash. The standard is the one thing with a version: a spec has none, and a changed spec is a new name. A registered standard never changes; a change is a new version.

| File | Status |
| --- | --- |
| `s1-general-2.0.0.yaml` | draft: waits for its model and calibrations on the panel spec `majortom-global` |

- Check one with `ponzi-models check-standard standards/<file> [--registry DIR]`. A draft is checked for its form and its specs. A published one is held against the registry, its panel spec, the installed versions it `requires`, and the version before it (the latest in the registry, else the one before it in this folder).
- A change to the runs (the sensor, the workflow, the coherence, onboarding or panel spec, the model, the scoring spec) is a new major version; to the outputs (the calibrations, the detection spec) a new minor; to anything else (the description, `requires`) a patch. A spec counts as changed when its name or its hash does. `ponzi-models bump-standard FILE` writes the next version of an edited bundle beside it.
- `ponzi-models new-standard --model ID --detection-spec NAME --coherence-spec NAME --onboarding-spec NAME` writes a new standard's first version from the registry. `ponzi-models register-standard FILE` files a version in the registry (and assigns it when the file has none); a published standard must be in a ponzi-suite commit, its specs too.
- `ponzi-models standard-workflow` turns a published standard into the server's file, in the PONZI home's `standards/`, with the `specs:` block of every spec it names.
