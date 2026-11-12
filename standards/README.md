# Standards

One file per standard version, `<id>-<version>.yaml`: everything a watched area runs (`ponzi_models.standards`, ponzi-core CR-028, CR-055 and CR-070). A standard's id is `<sensor>-<scope>` (`s1-general`, `s1-gaza`; `ponzi_spec.naming`), and it names its specs: its panel spec (`specs/panel_specs/`), its coherence, onboarding and detection specs (`specs/coherence_specs/`, `specs/onboarding_specs/`, `specs/detection_specs/`), and its model's scoring spec by its hash. A spec's version is its hash: a spec is edited in place under its name, and a standard pins one with `name@<hash8>`. A registered standard never changes; a change is a new version.

| File | Status |
| --- | --- |
| `s1-general-2.0.0.yaml` | draft: waits for its model and calibrations on the panel spec `majortom-global` |

- `ponzi-models check-standard standards/<file> [--registry DIR]` checks one: a draft for its form and its specs, a published one also against the registry, its panel spec, the versions it `requires` and the version before it.
- `new-standard` writes a new id's first version, `bump-standard` the next version of an edited bundle, `register-standard` files a version in the registry, and `standard-workflow` turns a published one into the server's file.

Which number a change raises, and what each command does, are on the site: [Standard versions and naming](../docs/models/versions.md) and [Making a standard](../docs/models/standards.md).
