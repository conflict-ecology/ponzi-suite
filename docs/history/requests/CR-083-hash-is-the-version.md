# CR-083: a spec's hash is its version, and the registry keeps every version used

- **Requested by / date:** owner, 2026-11-12 ("lets revisit spec versioning", then "lets do B and D. Hash only keys/values and not docstrings or comments", the choices "description + undeclared notes", "name@hash8 in the id" and "name or name@hash8, hash folded in", and "remove items like schema_version in coherence specs as well")
- **Status:** signed off (2026-11-12), implemented (unreleased)

## Why
A spec was frozen to the hash its name was first used with (CR-070): any edit, even to a panel's description, needed a new name picked by hand; an old version lived on only in git; and each registry froze names on its own. The hash already identifies a spec's content exactly, so it can be the version: names stay what people write, the hash says which version, and the registry keeps a copy of every version it has used.

## What changes
- **What a hash covers.** A spec's hash covers the keys its class declares and their values, never comments, never `description`, and never keys no class declares (a panel's free-form notes: `subpanels`, `windows`, `footprints`, `outlines`). `schema_version` is removed from the coherence and the scoring spec: the hash is the version.
- **Citing a version.** A spec is cited as `name` (the file of that name now) or `name@<hash>` (that version; 8 to 32 hex digits, a prefix of the hash). `find_spec` resolves `name@<hash>` to the file in the home or the suite when its hash matches, else to the registry's archived copy.
- **References fold in.** A spec that names another (a panel spec's `coherence`, a standard's specs) may write either form; the named spec's hash enters the dependent's hash, so editing `isce3-gaussian` changes the hash of every panel spec that names it.
- **No freeze.** A spec may be edited in place under its name. The registry's `specs.json` and the refusal "give the changed spec a new name" are removed.
- **The archive.** Building a panel, registering a model and registering a standard archive every spec they use, resolved, under the registry's `specs/<kind>_specs/<name>/<hash>/` (`<name>.yaml`, a panel spec its folder `<name>/` with its geojson, its references pinned to full hashes). The archived copy loads to the same hash. The registry root is `ponzi_spec.specs.registry_root` (moved from `ponzi_models.registry.default_registry_root`, which calls it).
- **Model ids carry the versions.** `<training spec>@<hash8>--<panel spec>@<hash8>`, e.g. `tide-weather@59bfd3dc--majortom-global@77941f85`; `export` names an artifact so (the prepare stamp records the panel spec's hash). A registry reference stays `registry:<model id>@sha256:<digest>`, read on its last `@sha256:`.
- **Standards.** Their `coherence`, `onboarding`, `detection` and `panel` take either form; `new-standard` writes `name@<hash8>`.

## Do results change?
No computation changes. Hashes change: every panel spec's (description and notes out, its coherence spec's hash in), the coherence and scoring specs' (`schema_version` out), and so every content id downstream of a coherence spec or a scoring spec; the golden scoring spec hash of the tests is updated for that reason alone. Model ids gain their hashes. Nothing published is pinned to the old values.

## Tests
`test_specs.py`: refs parsed, `name@<hash>` resolved to the file or the archive, a wrong hash refused. `test_panel_build.py`: description and notes do not change the hash, a coherence spec's edit does, a pinned and a bare reference to one version hash the same. `test_registry_store.py`: the archive, its copies loading to their hashes, an edited spec under the same name archived beside the first. `test_spec_hashes.py`, `test_scoring_spec.py`, `test_naming.py`, `test_training_fit.py`, `test_standards.py` follow.

## Version
Library: `ponzi-spec`, `ponzi`, `ponzi-pipeline` and `ponzi-models` major (spec hashes, model ids and the registry layout change). Standard: no change.
