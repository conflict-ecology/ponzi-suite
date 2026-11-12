# Versions

Three numbers in PONZI are set by a person: the release tags, the REST API's version and the PONZI STAC extension's version. Every other version is computed by the code, from one of three sources:

- the **major of a release tag**, for stages and their content ids;
- the **hash of a file's content**, for specs, standards, models and built panels;
- the **hash of a declared layout**, for store contracts and record files.

Nothing else is raised by hand, so no version can be forgotten (ponzi-core CR-083, CR-085, CR-086, CR-089). This page lays the system out; the pages it links hold the details.

```
release tag (person) ──► installed version ──► major ──► content id of every Item ──► cache reused or work made again
                                                 └─────► calibrations accepted or refused (CR-020)
spec file (person) ────► spec hash ──► name@hash8 ──► model id, built panel, standard's references
contract declaration ──► contract hash ──► attr or field in each store and file ──► reader accepts or refuses
standard file (person) ► id@hash8 ──► specs, model, calibrations, requires ──► what a watched area runs
```

## Set by a person

| Version | Where | Form | Raised when |
| --- | --- | --- | --- |
| **release** | git tags, one prefix per distribution (below) | `MAJOR.MINOR.PATCH` | a release is cut, by [what X, Y and Z mean](#what-x-y-and-z-mean) |
| **REST API** | `ponzi_spec.api.API_VERSION`, the path prefix and openapi's `info.version` | `v1` | a breaking change to the API ([REST API](../service/rest-api.md)) |
| **STAC extension** | `ponzi_spec.stac.PONZI_EXTENSION_VERSION`, its schema's folder and `$id` | `v0.2.0` | the `ponzi:*` fields change ([STAC catalog profile](../using/stac-profile.md)) |

## Releases: the tags

Every distribution takes its version from git tags at install time (`hatch-vcs`, `fallback-version = "0.0.0"`); no `pyproject.toml` or `package.json` holds a number.

| Repository | Distribution | Tag |
| --- | --- | --- |
| ponzi-core | `ponzi` | `vX.Y.Z` |
| | `ponzi-spec` | `spec-vX.Y.Z` |
| | `ponzi-pipeline` | `pipeline-vX.Y.Z` |
| | `ponzi-models` | `models-vX.Y.Z` |
| ponzi-service | `ponzi-client` | `client-vX.Y.Z` |
| | `ponzi-server` | `server-vX.Y.Z` |
| | `ponzi-worker` | `worker-vX.Y.Z` |
| ponzi-visual | the app | `vX.Y.Z`, read by `git describe --tags --match 'v*' --dirty` at build and shown at the foot of the drawer |

### What X, Y and Z mean

A tag is [SemVer](https://semver.org), `X.Y.Z`, each distribution numbered on its own. Raise the leftmost part the change calls for, and set the parts to its right to 0.

| Part | Raise it when | What follows |
| --- | --- | --- |
| **X**, major | the change breaks something that exists: a store or record format changes, an existing spec's default behaviour changes, or a result changes for an existing spec (**RESULTS-CHANGING**); for ponzi-spec, ponzi-server and ponzi-client, a change their callers must follow (a schema, the hashing rule, a route) | everything the distribution computes gets new content ids, so the worker makes it again; calibrations made under another major of `ponzi` are refused (CR-020) |
| **Y**, minor | something new that is opt-in: every existing spec gives the same bytes, every existing call works as before | nothing is made again: content ids, caches and calibrations stay |
| **Z**, patch | a fix or a speed-up the tests show bit-identical, or a change to docs and docstrings only | nothing changes |

**Below 1.0, which is where every distribution is now,** the major is `0.Y`, not `0` (`ponzi_spec.identity.library_major`): Y takes the place of X, and Z covers both new features and fixes.

| From | To | Because |
| --- | --- | --- |
| `v0.3.1` | `v0.4.0` | a fix that changes the scores of an existing scoring spec: results-changing, so the major moves |
| `pipeline-v0.3.1` | `pipeline-v0.4.0` | a new ISCE3 build that changes coherence values ([Stages](#stages-the-majors-of-their-code)) |
| `models-v0.3.1` | `models-v0.3.2` | a new opt-in flag of a command, or a fix with identical results |
| `v1.4.2` | `v2.0.0` | a store format changes (after 1.0) |
| `v1.4.2` | `v1.5.0` | a new forecaster, opt-in (after 1.0) |
| `v1.4.2` | `v1.4.3` | a faster kernel, bit-identical (after 1.0) |

Between tags:

- A commit after a tag carries the distance and the commit: `0.2.5.dev3+gabc1234` for a Python distribution, `v0.2.5-3-gabc1234-dirty` for the app. Its major is its tag's (`0.2`).
- With no tag in reach, a Python distribution falls back to `0.0.0`; a version that cannot be read has no major, and content ids record it as unknown (`null`).
- `ponzi-server` reports its version at `/v1/health`; `ponzi-worker stages` prints each stage's code majors.

## Stages: the majors of their code

A stage has no version. `StageSpec.code` names the distributions whose code computes it, and their majors enter its content id:

```
content id = sha256(canonical_json({"stage": name, "inputs": sorted ids, "config": identity params,
                                    "code": {distribution: major}}))[:32]
```

- A patch or minor release keeps every id, so the cache is reused; a major gives everything its distribution computes a new id, so it is made again ([Content ids and reuse](../using/content-ids.md)).
- Every Item and manifest step records `ponzi:stage = {name, code}`, the releases that made it.
- A stage that computes nothing (`ingest-coherence`, `ingest-calibration`) and the server's jobs and batches (`workflow-job`, `slurm-batch`) name no code: their ids follow their payload alone.
- A calibration made under another `ponzi` major is refused (CR-020).
- A standard's `requires` gives the releases it runs on; a worker whose installed versions do not meet it fails the job (CR-055).

## Specs, models and panels: the content hash

A spec has no version field: its version is its `spec_hash`, cited `name@<hash8>` (CR-083). Comments, `description`, `notes`, key order and a default written out do not change it; a changed setting or code default does. A spec that names another takes in its hash.

| What | Version | Example |
| --- | --- | --- |
| a spec (panel, coherence, onboarding, detection, training, scoring) | `spec_hash` | `majortom-global@2436d8cb` |
| a model | its training spec's and panel spec's hashes | `tide-weather-fill-previous@93771aa3--majortom-global@2436d8cb` |
| a built panel | its panel spec's hash | `$PONZI_HOME/panels/majortom-global@2436d8cb/` |
| a standard | the hash of its file `standards/<id>.yaml`, but its description, with the hashes of the specs it names (CR-089) | `s1-general@3f9a12c4` ([Standard versions](../models/versions.md)) |
| a calibration | the sha256 of its files, and the staged rule's version (below) | |

Where a spec is used it is recorded as `{name, hash, suite_commit}`, and the registry archives every version used ([Standard versions](../models/versions.md#specs-a-name-and-a-hash)).

## Store contracts and record files: the hash of the declaration

Each contract declares its layout as data in its module (`CONTRACT`, or `SCHEMA` or `RULE`): dims, variables and dtypes, required attrs, its meta model, and for C1 its check thresholds. Its version is `ponzi_spec.contract_hash` of that: 32 hex digits, written into each store or file it describes. Docstrings and field descriptions are not hashed; a field, a dtype, a threshold or the declaration's `notes` is.

| Contract or file | Constant | Written as |
| --- | --- | --- |
| C1 coherence store | `ponzi.contracts.coherence.CONTRACT_VERSION` | attr `contract_version` |
| C2 covariates sidecar | `ponzi_pipeline.onboard.onboard.CONTRACT_VERSION` | attr `contract_version` |
| C2 `onboard_meta.json` | `ponzi_pipeline.onboard.onboard.STAMP_VERSION` | `stamp_version` |
| C3 pixel sample | `ponzi.core.sample.CONTRACT_VERSION` | attr `contract_version` |
| C7/C8 run stamp | `ponzi.contracts.stamp.STAMP_CONTRACT_VERSION` | attr `ponzi_contract_version` |
| C9 `run_meta.json` | `ponzi.contracts.run_meta.RUN_META_CONTRACT_VERSION` | `contract_version` |
| C10 forecasting accumulators | `ponzi.core.forecasting_stats.CONTRACT_VERSION` | `schema_version` |
| C11 label store | `ponzi.evaluation.labels.LABEL_SCHEMA` | attr `label_schema` |
| C18 engine report | `ponzi.contracts.validate.ENGINE_REPORT_SCHEMA_VERSION` (the writer, `ponzi_pipeline.engine`, imports it) | `schema_version` |
| C20 row set | `ponzi.contracts.row_set.ROW_SET_CONTRACT_VERSION` | `contract_version` in the npz's `meta` |
| C23 mask store | `ponzi.contracts.masks.CONTRACT_VERSION` | attr `contract_version` |
| staged rule | `ponzi.core.staged.RULE_VERSION` | a calibration's `staged_rule.version` |
| `panel.json` | `ponzi_models.panels.panel.SCHEMA_VERSION` | `schema_version` |
| manifest | `ponzi_spec.manifest.MANIFEST_VERSION` | `manifest_version` |
| calibration file | `ponzi.calibration.product.FORMAT` (one for the unstaged and the staged layout; CR-086) | `format` in the npz's `meta` |
| burst catalog `bursts.sqlite3` | `ponzi_spec.catalog.FORMAT` (CR-086) | the `format` row of its `meta` table |
| prepared training folder | `ponzi_models.training.prepare.FORMAT` (CR-086) | `features.format` of `prepare.json`, part of the folder's tag |
| `boundaries.sqlite3` (ponzi-server) | `ponzi_server.boundaries.FORMAT` (CR-086) | the `format` row of its `meta` table |

- **Each hash is pinned by a test** (ponzi-core `packages/core/tests/test_contract_versions.py` for `ponzi`'s; `test_onboard.py`, `test_engine_agreement.py`, `test_panel_build.py`, `test_manifest.py`, `test_home_catalog.py` and `test_training_data.py` for the others; ponzi-service `test_server_boundaries.py` for the boundaries). A changed declaration fails it; the change is then a new version: update the pin, the contract's page in [Store formats (contracts)](contracts.md), and the CHANGELOG, as a major.
- **Hashes have no order.** A reader can only tell "ours" from "not ours": a sidecar, a sample, a `panel.json`, a calibration file or the boundaries of another version are refused, a catalog or a prepared folder of another version is built again, `validate-store` and the engine report warn. A file of another version is made again, never migrated (CR-085).
- **The limit:** a change of meaning the declaration does not hold, such as a variable's units, does not change the hash. Write it into the declaration's `notes`, which is hashed.

## Changing something: which version moves

| You change | You do | What follows by itself |
| --- | --- | --- |
| code, same results | release a minor or patch | nothing: ids, caches and calibrations stay |
| code, new results | release a major of the distribution that computes it | new content ids for its outputs, work made again, old calibrations refused |
| a store's or a file's layout | change its declaration, update the pin, release a major | a new contract hash; files of the old layout refused |
| a spec | edit the file | a new hash, so new model ids, built panels and content ids where it enters |
| what a standard runs | edit its file, then `register-standard` | a new `id@hash8`, new jobs on the server |
| the API or the `ponzi:*` fields | raise `API_VERSION` or the extension's version | |
