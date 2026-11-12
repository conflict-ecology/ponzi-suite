# CR-089: a standard is named by its file and versioned by its content hash

- **Requested by / date:** owner, 2026-11-12 ("make the standard id be the filename. if the version is not used remove it", then, on a version a person raises, "recommend non human incremented versioning schemes" and "lets do content hash")
- **Status:** signed off (2026-11-12, on the owner's instruction), implemented (unreleased)

## Why
The standard was the last thing of PONZI a person numbers by hand. Specs are versioned by their hash (CR-083) and the code by its release tags (CR-085), but a standard wrote `id:` and `version: MAJOR.MINOR.PATCH` inside its file, one file per version (`s1-general-2.0.0.yaml`), and `bump-standard` raised the number by rules (a change of the run identity a major, of the calibrations or the detection a minor, else a patch). The version is used: requests and watched areas name `s1-general@2.0.0`, the registry files `standards/<id>@<version>/`. Its MAJOR.MINOR meaning is used by nothing but the bump rules themselves: the server and the areas treat the key as a name. The bundle already has a content hash (`Standard.bundle_hash`: its fields and the hashes of the specs it names), recorded in its `specs:` block.

## What changes
**One file per standard, named by its id.** `standards/<id>.yaml` (ponzi-suite, or the PONZI home's `specs/standards/` for a working copy, `Layout.standard_specs`: never the home's `standards/`, which holds the server's files and all of which the server reads). The file's name is the id (`<sensor>-<scope>`, checked as before); a file that writes `id:` or `version:` is refused. A copy filed in the registry (`standards/<id>@<hash8>/standard.yaml`) takes its id from its folder. ponzi-suite's `s1-general-2.0.0.yaml` becomes `s1-general.yaml`.

**The version is the content hash.** A standard's version is the first 8 characters of its bundle hash, its key `<id>@<hash8>` (`Standard.version(resolved)`, `Standard.key(resolved)`; the specs must be resolved to know it). The hash leaves out `description`, as a spec's leaves out its description (CR-083), so rewording is not a new version; any other field, or a spec it names changing its hash, is. Editing the file is making the next version; nobody writes a number.

**Commands.**
- `new-standard` writes `$PONZI_HOME/specs/standards/<id>.yaml` (or `--out`): no `id:`, no `version:`. Refused when that file exists or a standard of that id is registered, as before.
- `bump-standard` is removed: there is nothing to raise.
- `register-standard FILE` files the bundle as `standards/<id>@<hash8>/` once; the same content again is a no-op. Its record adds `registered` (the time) and, against the latest registered version of the id (by that time), `previous` and `changes`: each changed field, and what the change means, `run` when a field of the run identity changed (sensor, coherence, onboarding, panel, model, scoring spec: new forecast runs, earlier outputs not comparable), `products` when only the calibrations or the detection changed (new p-values and events from the same runs), else `other`. The meaning is reported and recorded, not encoded in a number, and nothing is refused for it.
- `check-standard FILE [--previous FILE]` prints the key, and the same change report against the latest registered version (else `--previous`). No file beside it is looked for: there is one file per standard.
- `standard-workflow` writes the server's standard with `standard: <id>@<hash8>`, by default to `$PONZI_HOME/standards/<id>@<hash8>.yaml`, and the workflow's `version` is the hash.

Removed from `ponzi_models.standards`: `Standard.version` as a field, `SEMVER`, `BUMPS`, `bump_of`, `bumped`, `bump_between`, `check_versions`, `previous_version`, `versions.bump`, `versions.with_version`, `FIRST_VERSION`. `MINOR_FIELDS` is renamed `PRODUCT_FIELDS`; `change_kind(changed)` gives `run`, `products`, `other` or None.

**The server.** A request or a watched area may name a standard by its id alone when the server holds exactly one version of it; the server stores the full key it resolved (`Catalog.resolve`), so an area keeps the version it was made with. With several versions of the id held, a bare id is refused with a 422 naming them. `default_standard` may be a bare id, by the same rule. A key is otherwise a name, as before (`<id>@<version>`, the version any text).

**Not changed.** A registered standard's folder is still immutable. Specs are named and versioned as in CR-083. Standards registered before (`standards/<id>@<semver>/`) are not read any more: the overhaul starts on a clean slate, and no standard has been published.

## Do results change?
No. No computed number depends on a standard's version. The keys areas and requests name change form (`s1-general@<hash8>`).

## Tests
- ponzi-models: a standard's id is its file's name; `id:` or `version:` in the file is refused; the key is `<id>@<bundle hash8>`; a description change keeps it, a spec's hash change or a calibration change moves it; `register-standard` files once, is a no-op for the same content, and records `previous` and `changes` with their kind; `new-standard` writes `<id>.yaml`; `check-standard` reports the change; `standard-workflow` writes `standard: <id>@<hash8>`; the rehearsal registers its standard and the worker runs it.
- ponzi-server: a bare id resolves when one version is held and is stored as the full key; refused with several; `default_standard` by id.
- ponzi-suite: `standards/s1-general.yaml` loads (`test_suite_standards.py`).

## Version
Library: `ponzi-models` major (the standard's file and its commands change; `bump-standard` removed). ponzi-server minor (a bare id accepted). Standard: every standard's key changes form; there is no published one.
