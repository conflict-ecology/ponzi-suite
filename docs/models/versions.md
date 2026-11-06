# Standard versions and naming

A standard is cited by its id and its version, and a published version never changes: a change is a new version. This page says how the two are written, which number a change raises, how a version reaches the server and how the server holds it. How a standard is made and checked against the registry is in [Making a standard](standards.md); the names of panels, forecasters and models are in [Naming](naming.md).

The rules are code: `ponzi_models.standards.Standard` and `check_versions` in ponzi-core, and `ponzi_server.catalog.Standard` in ponzi-service (ponzi-core CR-055).

## The id, the version and the key

| What | Form | Example |
| --- | --- | --- |
| id | lowercase letters, digits and hyphens, starting with a letter or digit (`^[a-z0-9][a-z0-9-]*$`) | `s1-general` |
| version | `MAJOR.MINOR.PATCH`, three whole numbers | `1.0.0` |
| key | `<id>@<version>` | `s1-general@1.0.0` |
| file | `<id>-<version>.yaml` | `standards/s1-general-1.0.0.yaml` |

- **The id** says what the standard is for. By convention the sensor comes first (`s1-`), then the purpose (`general`). It never holds a version or a date: those are in the `version` field. The id is not held to the naming rules of `ponzi_spec.naming` (those cover panels, forecasters, models and run configs), only to its pattern.
- **The key** is how everything else names a standard: a watched area's `standard`, a run request's `standard`, the server's setting `default_standard`, and the `standard` field at the top of the server's file. `Standard.key` makes it.
- **The file** of a bundle is named by its id and version, and ponzi-models' `test_suite_standards.py` holds every file in ponzi-suite `standards/` to it. `check-standard` finds the version before a file by this name (below).

## Draft and published

`status` is `published` (the default) or `draft`.

| | A draft | A published standard |
| --- | --- | --- |
| `run_config_hash` | may be empty | required |
| `calibrations` | may be empty | at least one |
| `check-standard` | the version rules and the form only | the version rules, then the registry, the panel and `requires` ([Making a standard](standards.md)) |
| `standard-workflow` | refused | writes the server's file |
| may change in place | yes, until it is published | never: a change is a new version |

A draft is written before its model and calibrations are registered. ponzi-suite `standards/s1-general-1.0.0.yaml` is one: publishing it means filling `model.ref`, `run_config_hash` and `calibrations` from the registry, setting `status: published`, and passing `check-standard`.

## When to raise which number

`check_versions(new, old)` holds a version against the one before it. The version must rise, and the id must be the same.

| Raise | When | Fields |
| --- | --- | --- |
| major | anything that changes the runs (`RUN_IDENTITY`) | `sensor`, `workflow`, `coherence`, `onboarding`, `panel`, `model`, `run_config_hash` |
| minor | the same runs, other outputs (`MINOR_FIELDS`): new p-values and events | `calibrations`, `recipe` |
| patch | the same outputs | `description`, `requires` |

A major may change anything. A minor may change its own fields and a patch's, never a field of `RUN_IDENTITY`. A patch may change neither. A version that changes more than its number allows is refused with the fields it changed and the number it needed.

`ponzi-models check-standard FILE` compares the file with `--previous FILE` when given, else with the highest earlier `<id>-<version>.yaml` in the same folder (`previous_version`). With neither, there is nothing to compare, and only the version's own checks run.

## Two files for one version

| | The bundle | The server's file |
| --- | --- | --- |
| Model | `ponzi_models.standards.Standard` | `ponzi_server.catalog.Standard` |
| Written by | a person, kept in git (ponzi-suite `standards/`) | `ponzi-models standard-workflow`, from a published bundle and the registry |
| Says | what runs: model, run config hash, calibrations, panel, recipe, onboarding, coherence config, `requires` | how it runs: the steps of `ponzi-worker` |
| Fields | `id`, `version`, `status`, `sensor`, `description`, `panel`, `workflow` (stage names and versions), `coherence`, `onboarding`, `model`, `run_config_hash`, `calibrations`, `recipe`, `requires` | `standard` (the key), `description`, `final` (`[events, cells]`), `requires`, `variables` (`registry` and those given with `--set`), `workflow` (`{workflow: <id>, version: <version>, steps: [...]}`) |
| Read by | `check-standard`, `standard-workflow` | the server, and through each job's payload the worker |

The steps of the server's file, and the `--source pipeline|stores` choice, are in [Making a standard](standards.md#from-bundle-to-server).

**How the server's file reaches the server:**

1. Write it with `standard-workflow ... --out FILE`. Naming it `<id>-<version>.yaml` too keeps two versions apart in one folder; the server goes by the `standard` field inside, not the file name.
2. Copy it into the server's standards folder: the setting `standards`, by default `$PONZI_HOME/standards/`.
3. Restart the server. It reads every `*.yaml` of the folder once, when it starts (`Catalog`), and never looks again while it runs. A file that does not parse, or two files with the same key, stop it from starting.
4. `GET /v1/standards` (`ponzi-client standards`) lists what it holds: each key, its workflow as `<id>@<version>`, its final steps, its stages and its description.

With one standard in the folder, an area made without one takes it. With several, name one in the server's settings file (`server: {default_standard: s1-general@1.0.0}`, given as `ponzi-server serve --settings FILE`, or as `PONZI_SERVER_SETTINGS` in the [Quickstart](../getting-started/quickstart.md)); a `default_standard` the server does not hold is logged as a warning at start (CR-068).

## How the server tracks a standard

- **An area stores the key.** An area made without a standard gets `default_standard`, else the one standard held, resolved when the area is made. The key is written in the area's row, so a later change of `default_standard`, or a new version in the folder, does not move an existing area. `PATCH /v1/areas/{area_id}` with `standard` switches it, to a key the server holds ([Watched areas](../using/watched-areas.md)).
- **A job carries the whole workflow.** Each job's payload is the server file's workflow, its variables (with the burst and the dates), the final steps, the key and `requires`. The job's id is the content id of that payload, so an unchanged payload is the same job and never a second one. A new version changes the payload (its key and its workflow's version at least), so it makes new jobs. On the worker, each step is again decided by its own content id ([Content ids](../using/content-ids.md)): steps whose inputs and parameters did not change, such as the coherence of a new minor that only adds a calibration, are found in the cache.
- **A worker checks `requires`.** Before anything runs, a job whose `requires` the worker's installed distributions do not meet fails, with the reason.
- **A missing standard makes no jobs.** When an area names a key the server no longer holds (its file removed, and the server restarted), the scheduler makes no jobs for it and logs a warning at each tick; `POST /v1/areas/{area_id}/discover` answers 422. The area is kept, and makes jobs again once the file is back.

## What is and isn't recorded

These are the gaps today.

- **A version lives only as files.** The bundle is a file in git, and git history of ponzi-suite `standards/` is the lasting record of every version. The server's file is a file in its standards folder. Neither is stored anywhere else.
- **The registry does not hold standards.** It holds models and their calibrations (`ponzi_models.registry`), and nothing of the standards made from them.
- **Outputs do not name their standard.** They record what made them by content id: a run's content id covers its run config, which names the model's weights by `registry:<model id>@sha256:<digest>`, and a p-value Item links its calibration (`ponzi:calibration`), whose content id is the sha256 of its files. The `ponzi:standard` field and link of the [STAC profile](../using/stac-profile.md) are not filled, so a manifest's `standard` is empty too, and the `ponzi-standards` collection is defined but nothing publishes to it. The server's database keeps each job's payload, key included, and the Items the job made, for as long as that database is kept.
- **A version number could be reused.** Nothing outside the files holds a version's content, so if the files were lost, the same `<id>@<version>` could be written again with other content. Results would still not mix, since every output is named by the content id of what made it, but the key alone would no longer say which content a result came from.
