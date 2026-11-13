# Standard versions

A standard is cited by its id and its version, and a registered version never changes. Nothing a person writes has a version number: a standard, like a spec, is known by its name, its file's name, and its version is its content hash (ponzi-core CR-089). Every version in PONZI is laid out in [Versions](../reference/versions.md). This page says how the two are written, how specs are pinned, what a change means, the commands that write and register a version, how a version reaches the server and how the server holds it. How a standard is made and checked against the registry is in [Building a standard](standards.md); the names of specs, models and standards and the spec folders are in [Naming rules](naming.md).

The rules are code: `ponzi_models.standards.Standard`, `change_kind` and `ponzi_models.standards.versions` in ponzi-core, and `ponzi_server.catalog` in ponzi-service (ponzi-core CR-055, CR-070, CR-089).

## The id, the version and the key

| What | Form | Example |
| --- | --- | --- |
| id | `<sensor>-<scope>`, both words listed in `ponzi_spec.naming`: the file's name | `s1-general` |
| file | `<id>.yaml`, one per standard | `standards/s1-general.yaml` |
| version | the first 8 characters of its content hash | `3f9a12c4` |
| key | `<id>@<version>` | `s1-general@3f9a12c4` |

- **The id** says what the standard is for, `<sensor>-<scope>` ([Naming rules](naming.md)). It is the file's name: the file writes no `id:` (refused). A copy in the registry, `standards/<id>@<version>/standard.yaml`, takes its id from its folder.
- **The version is the content.** `Standard.bundle_hash` hashes the bundle's fields and the hashes of the specs it names; the version is its first 8 characters (`Standard.version`). The file writes no `version:` (refused). `description` is left out of the hash, so rewording is not a new version; any other field, or a spec it names changing its hash (edited in place), is. Editing the file is making the next version: nobody writes or raises a number.
- **The key** is how everything else names a standard: a watched area's `standard`, a run request's `standard`, the server's setting `default_standard`, and the `standard` field at the top of the server's file. `Standard.key` makes it, from the resolved specs. Where the server holds one version of an id, the id alone names it ([below](#how-the-server-tracks-a-standard)).

## Draft and published

`status` is `published` (the default) or `draft`.

| | A draft | A published standard |
| --- | --- | --- |
| `scoring_spec_hash` | may be empty | required |
| `calibrations` | may be empty | at least one |
| `check-standard` | the form and its specs, and the change from the version before | the same, then the registry, the panel and `requires` ([Building a standard](standards.md)) |
| `standard-workflow` | refused | writes the server's file |
| its file | edited in place: each content is its own version | the same; a registered version never changes |

A draft is written before its model and calibrations are registered. ponzi-suite `standards/s1-general.yaml` is one: publishing it means filling `model.ref`, `scoring_spec_hash` and `calibrations` from the registry, setting `status: published`, and `register-standard`. A draft can be registered too, and its version is citable from then on.

## Specs: a name and a hash

Every spec ([Naming rules](naming.md#spec-folders)) is known by its name, and its version is its content hash, `spec_hash` (ponzi-core CR-083): it has no version field, and is cited `name@<hash8>`. The hash is `ponzi_spec.identity.spec_hash`: BLAKE2b with a 16-byte digest of the canonical JSON of the keys the spec's class declares and their values, every setting the file leaves out filled with the code's default, without its name. Comments, `description`, a panel spec's `notes`, key order and a default written out do not change it; a changed code default does. A panel spec's hash also covers its geojson files, by name and bytes, and the hash of the coherence spec it names.

- **Where a spec is used, it is recorded** as a `specs:` block of `{name, hash, suite_commit}` per kind (`ponzi_spec.specs.spec_record`): on a model card (its training, scoring and panel specs), on a built panel's `panel.json` (its panel spec), on a calibration (its scoring and panel specs), on a standard's registry record and in the server's file `standard-workflow` writes (every spec it names, and the bundle). `suite_commit` is the ponzi-suite commit the file was read from, or null when the file is not tracked, has an uncommitted change, or is not in ponzi-suite (a working copy in the home).
- **A spec may be edited in place.** An edit is a new version under the same name: anything made from it records the new hash, and model ids and built panels carry it (`tide-weather@59bfd3dc--majortom-global@77941f85`, `$PONZI_HOME/panels/majortom-global@77941f85/`).
- **A reference is a name or a version.** A spec that names another (a panel spec's `coherence`, a standard's specs) writes `name` (the file of that name now) or `name@<hash>` (that version); the named spec's hash enters the dependent's hash, so editing a coherence spec changes every panel spec that names it.
- **The registry keeps every version used.** Building a panel, registering a model and registering a standard archive each spec they use, resolved, under the registry's `specs/<kind>_specs/<name>/<hash>/`, its references pinned. `name@<hash>` is found there once the file has moved on (`ponzi_spec.specs.find_spec`).
- **The stored fields name the spec.** A run's stamp and a model card hold `scoring_spec_name` and `scoring_spec_hash`, a run's `run_meta.json` a `scoring_spec` record, a calibration `scoring_spec_hash`; an events store holds `detection_spec` and `detection_spec_hash`; a coherence store `coherence_spec` and `coherence_spec_hash`; an Item `ponzi:spec_hash` ([STAC catalog profile](../using/stac-profile.md)).

## What a change means

Nothing is raised: a change is a new hash. What it means is reported, by `change_kind`, and recorded when the version is registered. A spec field counts as changed when its name or its hash does.

| Change | When | Fields | Means |
| --- | --- | --- | --- |
| `run` | any field of `RUN_IDENTITY` | `sensor`, `coherence`, `onboarding`, `panel`, `model`, `scoring_spec_hash` | new forecast runs: earlier outputs are not comparable |
| `products` | only `PRODUCT_FIELDS` | `calibrations`, `detection` | the same runs, new p-values and events |
| `other` | any other field | `requires`, `status` | neither the runs nor the products |

`ponzi-models check-standard FILE` prints the key, and compares the file with the latest version registered under its id when there is one, else with `--previous FILE` when given: each changed field, and the kind of change with what it means. With neither, there is nothing to compare. Nothing is refused for the kind of change.

## Writing and registering a version

Two commands write and register a standard, so no hash is copied by hand. Each takes `--registry DIR`; the spec folders looked in first are the PONZI home's (`$PONZI_HOME`; CR-088).

| Command | Use it | What it does |
| --- | --- | --- |
| `ponzi-models new-standard --model MODEL_ID --detection-spec NAME --coherence-spec NAME --onboarding-spec NAME [--scope general] [--calibrations ID,...] [--description TEXT] [--out DIR\|FILE]` | for a new id | from the registry: the model's reference, its scoring spec's hash, its panel spec and its calibrations (all, or those named); the id `<sensor>-<scope>` from the model card's sensor, refused when that id is registered; each named spec resolved and pinned; `requires` from the installed versions as lower bounds; `status: draft`; written to `$PONZI_HOME/specs/standards/<id>.yaml`, apart from the server's `standards/` (or `--out`, a folder or `<id>.yaml`), then checked as `check-standard` does |
| `ponzi-models register-standard FILE [--allow-uncommitted]` | to make the file's current content a citable version | files the bundle and its record in the registry as `standards/<id>@<version>/`, once, and archives the specs it names (CR-083). The record holds its hash, status, `specs:` block, the time it was registered, and, against the latest registered version of the id, `previous` (its key), `changes` (the fields) and `change` (`run`, `products` or `other`). The same content again (a reworded description included) does nothing. A `published` standard whose bundle or specs are not in a ponzi-suite commit is refused unless `--allow-uncommitted`, which the record says |

## Two files for one version

| | The bundle | The server's file |
| --- | --- | --- |
| Model | `ponzi_models.standards.Standard` | `ponzi_server.catalog.Standard` |
| Written by | a person, kept in git (ponzi-suite `standards/`) | `ponzi-models standard-workflow`, from a published, registered bundle and the registry |
| Says | what runs: model, scoring spec hash, calibrations, and the panel, detection, onboarding and coherence specs by name, `requires` | how it runs: the steps of `ponzi-worker`, each spec's resolved fields given to the steps that use it |
| Fields | `status`, `sensor`, `description`, `panel`, `coherence`, `onboarding`, `model`, `scoring_spec_hash`, `calibrations`, `detection`, `requires` | `standard` (the key), `description`, `final` (`[cells]`, CR-100), `requires`, `variables` (`registry` and those given with `--set`), `workflow` (`{workflow: <id>, version: <hash8>, steps: [...]}`), `workflow_hash` and `built_by` (below), `specs` (the `specs:` block of every spec named and of the bundle) |
| Read by | `check-standard`, `register-standard`, `standard-workflow` | the server, and through each job's payload the worker |

The steps of the server's file, and the `--source pipeline|stores` choice, are in [Building a standard](standards.md#from-bundle-to-server).

**How the server's file reaches the server:**

1. Write it with `standard-workflow` ([Building a standard](standards.md#from-bundle-to-server)). Its default name, `<id>@<version>.yaml`, keeps two versions apart in one folder; the server goes by the `standard` field inside, not the file name.
2. Unless it was written there, copy it into the server's standards folder, `$PONZI_HOME/standards/`.
3. Restart the server. It reads every `*.yaml` of the folder once, when it starts (`Catalog`), and never looks again while it runs. A file that does not parse, two files with the same key, or a file whose `workflow_hash` is not its workflow's (edited by hand), stop it from starting.
4. `GET /v1/standards` (`ponzi-client standards`) lists what it holds: each key, its workflow as `<id>@<version>`, its final steps, its stages, its description, the bundle's `hash` and `suite_commit` from the file's `specs:` block, and its `workflow_hash`.

With one standard in the folder, an area made without one takes it. With several, name one in the server's settings file (`server: {default_standard: s1-general}`, an id when the server holds one version of it, else a key; given as `ponzi-server serve --settings FILE`, or as `PONZI_SERVER_SETTINGS` in the [Quickstart](../getting-started/quickstart.md)); a `default_standard` the server does not hold is logged as a warning at start (CR-068).

## One key, one workflow

The key hashes the bundle, not the workflow `standard-workflow` builds from it, which depends on the ponzi-models that builds it and the source (`pipeline` or `stores`). So that a key names one workflow wherever it runs, the registry records it, once (ponzi-core CR-091):

- **The record.** `standard-workflow` needs a registered standard. The first time it builds the standard's workflow from a source, it writes `workflow-<source>.json` beside the registered standard (`standards/<id>@<hash8>/`): its `workflow_hash` (`ponzi_spec.identity.workflow_hash`, the hash of the workflow as data, its `${variables}` unfilled) and `built_by` (the ponzi-models version, the source, the time). A later build must give the same hash, or is refused with both `built_by`. The server file carries `workflow_hash` and `built_by`.
- **The server** checks the file against itself: it hashes the file's workflow and refuses a file whose `workflow_hash` differs. It keeps no record and never reads the registry. A job's payload carries `workflow_hash` and `built_by`.
- **The worker** holds every run to the record: `ponzi-worker job` and `ponzi-worker run FILE` hash the workflow they are given and compare it with the record in the registry the standard names (`${registry}`); none, or another, is refused before anything runs.
- **A file written by hand** has no `workflow_hash`: the server takes it (and lists `null`), and the worker runs it with a warning, unchecked.

## How the server tracks a standard

- **An area stores the key.** A request or an area may name a standard by its id alone when the server holds exactly one version of it; with several it is refused (422) with the keys held (`Catalog.resolve`, CR-089). An area made without a standard gets `default_standard`, else the one standard held. The key is resolved when the area is made. The key is written in the area's row, so a later change of `default_standard`, or a new version in the folder, does not move an existing area. `PATCH /v1/areas/{area_id}` with `standard` switches it, to a key the server holds ([Watched areas](../using/watched-areas.md)).
- **A job carries the whole workflow.** Each job's payload is the server file's workflow, its variables (with the burst and the dates), the final steps, the key and `requires`. The job's id is the content id of that payload, so an unchanged payload is the same job and never a second one. A new version changes the payload (its key and its workflow's version at least), so it makes new jobs. On the worker, each step is again decided by its own content id ([Content ids and reuse](../using/content-ids.md)): steps whose inputs and parameters did not change, such as the coherence of a version that only adds a calibration (a `products` change), are found in the cache.
- **A worker checks `requires`.** Before anything runs, a job whose `requires` the worker's installed distributions do not meet fails, with the reason.
- **A missing standard makes no jobs.** When an area names a key the server no longer holds (its file removed, and the server restarted), the scheduler makes no jobs for it and logs a warning at each tick; `POST /v1/areas/{area_id}/discover` answers 422. The area is kept, and makes jobs again once the file is back.

## What is and isn't recorded

These are the gaps today.

- **The registry holds each registered version.** `register-standard` writes `standards/<id>@<version>/` (`standard.yaml`, the bundle as registered, and `record.json`, its hash, status and `specs:` block) once, and never changes it; `standard-workflow` adds the record of its workflow per source ([One key, one workflow](#one-key-one-workflow)). ponzi-suite `standards/` in git is the record of the bundles as written, drafts included. The server's file is a file in its standards folder.
- **Outputs do not name their standard.** They record what made them by content id: a run's content id covers its scoring spec, which names the model's weights by `registry:<model id>@sha256:<digest>`, and a p-value Item links its calibration (`ponzi:calibration`), whose content id is the sha256 of its files. The `ponzi:standard` field and link of the [STAC catalog profile](../using/stac-profile.md) are not filled, so a manifest's `standard` is empty too, and the `ponzi-standards` collection is defined but nothing publishes to it. The server's database keeps each job's payload, key included, and the Items the job made, for as long as that database is kept.
- **A version is its content.** Since the version is the content hash, two registries, or a version never registered, cannot give one key two contents (but for a collision of 8 characters, which `register-standard` refuses against its full hash). What a change meant is in the record of the registry it was registered in.
