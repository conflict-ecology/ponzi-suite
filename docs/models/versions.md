# Standard versions and naming

A standard is cited by its id and its version, and a registered version never changes: a change is a new version. The standard is the one thing in PONZI with a version: a spec has none, and is known by its name and its content hash. This page says how the two are written, how specs are pinned, which number a change raises, the commands that write and register a version, how a version reaches the server and how the server holds it. How a standard is made and checked against the registry is in [Making a standard](standards.md); the names of specs, models and standards and the spec folders are in [Naming](naming.md).

The rules are code: `ponzi_models.standards.Standard`, `check_versions` and `ponzi_models.standards.versions` in ponzi-core, and `ponzi_server.catalog.Standard` in ponzi-service (ponzi-core CR-055, CR-070).

## The id, the version and the key

| What | Form | Example |
| --- | --- | --- |
| id | `<sensor>-<scope>`, both words listed in `ponzi_spec.naming` | `s1-general` |
| version | `MAJOR.MINOR.PATCH`, three whole numbers | `2.0.0` |
| key | `<id>@<version>` | `s1-general@2.0.0` |
| file | `<id>-<version>.yaml` | `standards/s1-general-2.0.0.yaml` |

- **The id** says what the standard is for: its sensor (`s1`), then its scope (`general`, `rehearsal`, or a test case's name such as `gaza`). It never holds a version or a date: those are in the `version` field. `ponzi_spec.naming` checks it ([Naming](naming.md)), and the model card's `sensor` must be the id's sensor.
- **The key** is how everything else names a standard: a watched area's `standard`, a run request's `standard`, the server's setting `default_standard`, and the `standard` field at the top of the server's file. `Standard.key` makes it.
- **The file** of a bundle is named by its id and version, and ponzi-models' `test_suite_standards.py` holds every file in ponzi-suite `standards/` to it. `check-standard` finds the version before a file by this name (below).

## Draft and published

`status` is `published` (the default) or `draft`.

| | A draft | A published standard |
| --- | --- | --- |
| `scoring_spec_hash` | may be empty | required |
| `calibrations` | may be empty | at least one |
| `check-standard` | the version rules, the form and its specs only | the version rules, then the registry, the panel and `requires` ([Making a standard](standards.md)) |
| `standard-workflow` | refused | writes the server's file |
| may change in place | yes, until it is registered | never: a change is a new version |

A draft is written before its model and calibrations are registered. ponzi-suite `standards/s1-general-2.0.0.yaml` is one: publishing it means filling `model.ref`, `scoring_spec_hash` and `calibrations` from the registry, setting `status: published`, and `register-standard`. A draft can be registered too, and its version is citable from then on.

## Specs: a name and a hash

Every spec ([Naming](naming.md#spec-folders)) is known by its name and its content hash, `spec_hash`, and has no version. The hash is `ponzi_spec.identity.spec_hash`: BLAKE2b with a 16-byte digest of the canonical JSON of the spec as its class reads it, every setting the file leaves out filled with the code's default, without its `name`. A changed code default is then a changed hash; key order, comments and a default written out are not. A panel spec's hash also covers its geojson files, by name and bytes. A scoring spec's hash is the value its run config's `config_hash` was before CR-070.

- **Where a spec is used, it is recorded** as a `specs:` block of `{name, hash, suite_commit}` per kind (`ponzi_spec.specs.spec_record`): on a model card (its training, scoring and panel specs), on a built panel's `panel.json` (its panel spec), on a calibration (its scoring and panel specs), on a standard's registry record and in the server's file `standard-workflow` writes (every spec it names, and the bundle). `suite_commit` is the ponzi-suite commit the file was read from, or null when the file is not tracked, has an uncommitted change, or is not in ponzi-suite (a working copy in the home).
- **A spec is frozen once used.** The registry's `specs.json` keeps, per kind, the hash each name was first used with. Registering a model, building a panel or registering a standard with a known name and another hash is refused: give the changed spec a new name.
- **The stored fields name the spec.** A run's stamp and a model card hold `scoring_spec_name` and `scoring_spec_hash`, a run's `run_meta.json` a `scoring_spec` record, a calibration `scoring_spec_hash`; an events store holds `detection_spec` and `detection_spec_hash`; a coherence store `coherence_spec` and `coherence_spec_hash`; an Item `ponzi:spec_hash` ([STAC profile](../using/stac-profile.md)). The names before CR-070 (`run_config_*`, `config_hash`, `recipe`, `recipe_digest`) are not read: a registry entry, calibration or standard with them is refused, saying what to run.

## When to raise which number

`check_versions(new, old)` holds a version against the one before it. The version must rise, and the id must be the same. A spec field counts as changed when its name or its hash does.

| Raise | When | Fields |
| --- | --- | --- |
| major | anything that changes the runs (`RUN_IDENTITY`) | `sensor`, `workflow`, `coherence`, `onboarding`, `panel`, `model`, `scoring_spec_hash` |
| minor | the same runs, other outputs (`MINOR_FIELDS`): new p-values and events | `calibrations`, `detection` |
| patch | the same outputs | `description`, `requires`, `status` |

A major may change anything. A minor may change its own fields and a patch's, never a field of `RUN_IDENTITY`. A patch may change neither. A version that changes more than its number allows is refused with the fields it changed and the number it needed.

`ponzi-models check-standard FILE` compares the file with the latest version registered under its id when there is one, else with `--previous FILE` when given, else with the highest earlier `<id>-<version>.yaml` in the same folder (`previous_version`). With none, there is nothing to compare, and only the version's own checks run. A version registered already must be the registered content.

## Writing and registering a version

Three commands write a standard's versions, so no version number or hash is copied by hand. Each takes `--registry DIR` and `--home DIR` (the home whose spec folders are looked in first).

| Command | Use it | What it does |
| --- | --- | --- |
| `ponzi-models new-standard --model MODEL_ID --detection-spec NAME --coherence-spec NAME --onboarding-spec NAME [--scope general] [--calibrations ID,...] [--description TEXT] [--out FILE]` | for the first version of a new id | from the registry: the model's reference, its scoring spec's hash, its panel spec and its calibrations (all, or those named); the id `<sensor>-<scope>` from the model card's sensor, refused when that id is registered; each named spec resolved and hashed; `requires` from the installed versions as lower bounds; `status: draft`, version `1.0.0`, written to `$PONZI_HOME/standards/<id>-1.0.0.yaml` (or `--out`), then checked as `check-standard` does |
| `ponzi-models bump-standard FILE [--version X.Y.Z]` | after editing a bundle | compares it with the latest registered version (else the highest file beside it), prints each changed field and the bump it implies, and writes `<id>-<version>.yaml` beside it. `--version` asks for a larger bump, never a smaller one. Nothing changed: nothing is written |
| `ponzi-models register-standard FILE [--allow-uncommitted]` | to make a version citable | files the bundle and its record (its hash and `specs:` block) in the registry as `standards/<id>@<version>/`, once, and freezes the specs it names. With no `version` in the file it assigns the next one and writes it into the file; with one it checks it is later than the latest registered by at least the bump the change needs. The same `id@version` with another hash is refused ("raise the version"); the same hash again does nothing. A `published` standard whose bundle or specs are not in a ponzi-suite commit is refused unless `--allow-uncommitted`, which the record says |

## Two files for one version

| | The bundle | The server's file |
| --- | --- | --- |
| Model | `ponzi_models.standards.Standard` | `ponzi_server.catalog.Standard` |
| Written by | a person, kept in git (ponzi-suite `standards/`) | `ponzi-models standard-workflow`, from a published bundle and the registry |
| Says | what runs: model, scoring spec hash, calibrations, and the panel, detection, onboarding and coherence specs by name, `requires` | how it runs: the steps of `ponzi-worker`, each spec's resolved fields given to the steps that use it |
| Fields | `id`, `version`, `status`, `sensor`, `description`, `panel`, `workflow` (stage names and versions), `coherence`, `onboarding`, `model`, `scoring_spec_hash`, `calibrations`, `detection`, `requires` | `standard` (the key), `description`, `final` (`[events, cells]`), `requires`, `variables` (`registry` and those given with `--set`), `workflow` (`{workflow: <id>, version: <version>, steps: [...]}`), `specs` (the `specs:` block of every spec named and of the bundle) |
| Read by | `check-standard`, `bump-standard`, `register-standard`, `standard-workflow` | the server, and through each job's payload the worker |

The steps of the server's file, and the `--source pipeline|stores` choice, are in [Making a standard](standards.md#from-bundle-to-server).

**How the server's file reaches the server:**

1. Write it with `standard-workflow ... --out FILE`. Naming it `<id>-<version>.yaml` too keeps two versions apart in one folder; the server goes by the `standard` field inside, not the file name.
2. Copy it into the server's standards folder: the setting `standards`, by default `$PONZI_HOME/standards/`.
3. Restart the server. It reads every `*.yaml` of the folder once, when it starts (`Catalog`), and never looks again while it runs. A file that does not parse, or two files with the same key, stop it from starting.
4. `GET /v1/standards` (`ponzi-client standards`) lists what it holds: each key, its workflow as `<id>@<version>`, its final steps, its stages, its description, and the bundle's `hash` and `suite_commit` from the file's `specs:` block.

With one standard in the folder, an area made without one takes it. With several, name one in the server's settings file (`server: {default_standard: s1-general@2.0.0}`, given as `ponzi-server serve --settings FILE`, or as `PONZI_SERVER_SETTINGS` in the [Quickstart](../getting-started/quickstart.md)); a `default_standard` the server does not hold is logged as a warning at start (CR-068).

## How the server tracks a standard

- **An area stores the key.** An area made without a standard gets `default_standard`, else the one standard held, resolved when the area is made. The key is written in the area's row, so a later change of `default_standard`, or a new version in the folder, does not move an existing area. `PATCH /v1/areas/{area_id}` with `standard` switches it, to a key the server holds ([Watched areas](../using/watched-areas.md)).
- **A job carries the whole workflow.** Each job's payload is the server file's workflow, its variables (with the burst and the dates), the final steps, the key and `requires`. The job's id is the content id of that payload, so an unchanged payload is the same job and never a second one. A new version changes the payload (its key and its workflow's version at least), so it makes new jobs. On the worker, each step is again decided by its own content id ([Content ids](../using/content-ids.md)): steps whose inputs and parameters did not change, such as the coherence of a new minor that only adds a calibration, are found in the cache.
- **A worker checks `requires`.** Before anything runs, a job whose `requires` the worker's installed distributions do not meet fails, with the reason.
- **A missing standard makes no jobs.** When an area names a key the server no longer holds (its file removed, and the server restarted), the scheduler makes no jobs for it and logs a warning at each tick; `POST /v1/areas/{area_id}/discover` answers 422. The area is kept, and makes jobs again once the file is back.

## What is and isn't recorded

These are the gaps today.

- **The registry holds each registered version.** `register-standard` writes `standards/<id>@<version>/` (`standard.yaml`, the bundle as registered, and `record.json`, its hash, status and `specs:` block) once, and never changes it. ponzi-suite `standards/` in git is the record of the bundles as written, drafts included. The server's file is a file in its standards folder.
- **Outputs do not name their standard.** They record what made them by content id: a run's content id covers its scoring spec, which names the model's weights by `registry:<model id>@sha256:<digest>`, and a p-value Item links its calibration (`ponzi:calibration`), whose content id is the sha256 of its files. The `ponzi:standard` field and link of the [STAC profile](../using/stac-profile.md) are not filled, so a manifest's `standard` is empty too, and the `ponzi-standards` collection is defined but nothing publishes to it. The server's database keeps each job's payload, key included, and the Items the job made, for as long as that database is kept.
- **A version number is held to its content in one registry.** `register-standard` refuses an `id@version` registered with another hash, but a registry knows only what was registered in it: a version registered elsewhere, or never registered, could still be written again with other content. Results would still not mix, since every output is named by the content id of what made it.
