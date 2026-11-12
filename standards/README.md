# Standards

One file per standard, `<id>.yaml`: everything a watched area runs (`ponzi_models.standards`, ponzi-core CR-028, CR-055, CR-070 and CR-089). The file's name is the standard's id, `<sensor>-<scope>` (`s1-general`, `s1-gaza`; `ponzi_spec.naming`); the file writes no `id:` and no `version:`. Its version is its content hash, its key `<id>@<hash8>`: editing the file is making the next version, and nobody writes a number. It names its specs: its panel spec (`specs/panel_specs/`), its coherence, onboarding and detection specs (`specs/coherence_specs/`, `specs/onboarding_specs/`, `specs/detection_specs/`), and its model's scoring spec by its hash. A spec's version is its hash too: a spec is edited in place under its name, and a standard pins one with `name@<hash8>`. A registered version never changes.

| File | Status |
| --- | --- |
| `s1-general.yaml` | draft: waits for its model and calibrations on the panel spec `majortom-global` |

- `ponzi-models check-standard standards/<file> [--registry DIR]` checks one: a draft for its form and its specs, a published one also against the registry, its panel spec and the versions it `requires`; it prints its key and what it changes from the latest registered version.
- `new-standard` writes a new id's file, `register-standard` files its current content in the registry (once per content, with what it changes from the version before), and `standard-workflow` turns a published one into the server's file.

What each command does and what a change means are on the site: [Standard versions and naming](../docs/models/versions.md) and [Making a standard](../docs/models/standards.md).
