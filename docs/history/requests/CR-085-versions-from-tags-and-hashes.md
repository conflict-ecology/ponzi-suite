# CR-085: no version a person raises but the release tags

- **Requested by / date:** owner, 2026-11-12 ("Stage identity versions, Internal job refs, ponzi-service distributions, and Store contract versions should all be automated", then the choices "tags only" for stages and "hash of declared schema" for contracts)
- **Status:** signed off (2026-11-12), implemented (unreleased)

## Why
CR-083 made a spec's hash its version. Four kinds of version are still numbers a person must remember to raise, and nothing fails when they forget:

| Version | Where | Now |
| --- | --- | --- |
| stage identity versions | `StageSpec.version` (ponzi-service `ponzi_worker/stages/`), `panel-assemble` (ponzi-models) | all `"2"`, held there by `test_stage_versions.py` |
| internal job refs | `workflow-job@1` (server `jobs.py`), `slurm-batch@1` (worker `executors/slurm.py`) | `"1"`, never raised |
| ponzi-service distributions | `version = "0.0.1"` in the `pyproject.toml` of `client`, `server`, `worker` | literals; ponzi-core's four take theirs from the tags (`hatch-vcs`) |
| store contract versions | `CONTRACT_VERSION` of C1 (`ponzi.contracts.coherence`), the mask store, the pixel sample (`ponzi.core.sample`), the covariates sidecar (`ponzi_pipeline.onboard`), the engine report's C1 (`ponzi_pipeline.engine`); `STAMP_CONTRACT_VERSION`, `RUN_META_CONTRACT_VERSION`, `ROW_SET_CONTRACT_VERSION` | all `1` |
| ponzi-visual | `"version": "0.0.1"` in `package.json` (and `package-lock.json`) | a literal beside the repository's `v0.0.1` tag; nothing reads it (the package is private, the app never shows it) |
| record file versions | `SCHEMA_VERSION` of the forecasting accumulators (C10, `ponzi.core.forecasting_stats`), of the engine report (`ponzi_pipeline.engine`, repeated as `ENGINE_REPORT_SCHEMA_VERSION` in `ponzi.contracts.validate`) and of `panel.json` (`ponzi_models.panels.panel`); `WINDOW_SCHEMA` of the run stamp (`ponzi.contracts.stamp`); `STAMP_VERSION` of `onboard_meta.json` (`ponzi_pipeline.onboard`) | `1`, `panel.json` `2`; the engine report's number kept twice, in two distributions |

A stage version that is not raised leaves old outputs in the cache under the ids of new code; a contract version that is not raised lets a reader take a store of another layout. The release tags are already the record of what changed, and a declared schema already says what a store holds.

## What changes

### Stages: the tags only
- `StageSpec.version` is removed. A content id is `sha256(canonical_json({"stage": name, "inputs": sorted ids, "config": identity config, "code": {distribution: major}}))[:32]`: the major of each distribution of `StageSpec.code` (CR-054, `code_majors`) is what changes it when the code does.
- **The release rule changes:** a RESULTS-CHANGING release is a MAJOR (below 1.0, it raises `y` of `0.y`). Until now it was "at least MINOR", released as `0.y.z+1`, which left the content ids as they were; the stage version was what forced the work to be done again. ponzi-core's CHANGELOG rules and [Versions](../../models/versions.md) say so.
- What changes a stage's output bytes lives in the distributions of its `code`. A stage whose `code` is empty (`ingest-coherence`, `ingest-calibration`: they take in what exists) is named by its name alone.
- `StageRef` is `{name, code}`: the stage's name and the majors its output was computed by, recorded on every Item (`ponzi:stage`) and manifest step, so an Item says which releases made it. The PONZI STAC extension moves to `v0.2.0` (`ponzi:stage` requires `name` and `code`, an object of strings or null); `PONZI_EXTENSION_VERSION` and the schema's folder and `$id` follow.
- `test_stage_versions.py` (ponzi-service) is replaced by a test that every stage that computes names its distributions in `code`.
- The cost, accepted: a major is coarse. A fix that changes only `detect` is a `ponzi` major, which gives new ids to everything `ponzi` computes (`run`, `pvalues`, `detect`, `tile`) and, by CR-020, refuses the calibrations made under the old major.

### Internal job refs: the payload only
`workflow-job` and `slurm-batch` hash their whole payload already (the workflow, its variables, the key and `requires`; the job ids and the profile). Their version is removed: a job's id is `content_id({"name": "workflow-job"}, [], payload)`, a batch's the same with `slurm-batch`. Their `code` is empty: a new release of the server is not a new job.

### ponzi-service distributions: the tags
`ponzi-client`, `ponzi-server` and `ponzi-worker` take their versions from git tags by `hatch-vcs`, as ponzi-core's do: `client-v*`, `server-v*` and `worker-v*`, `fallback-version = "0.0.0"`. The repository's `v0.0.1` tag is followed by `client-v0.0.1`, `server-v0.0.1` and `worker-v0.0.1` on the same commit, made by the owner.

### ponzi-visual: the tag, shown in the app
- `version` is removed from `package.json` (a private package needs none); `package-lock.json` loses it when it is next written.
- `vite.config.ts` reads `git describe --tags --match 'v*' --dirty` at build time (`0.0.0` without git, as `hatch-vcs`'s fallback) and defines it as `__PONZI_VISUAL_VERSION__`: `v0.0.1` built from the tagged commit, `v0.0.1-3-gabc1234-dirty` after it.
- The app shows it in a footer line, so the build deployed on the VM can be told from the page.

### Store contracts: the hash of the declared schema
- Each contract declares what it holds as data, `CONTRACT` in its module: its dimensions, its required and optional variables and their dtypes, its required attrs, and its meta model (`CoherenceMeta`, `MaskMeta`, `SampleMeta`, `RunStamp`, `RunMeta`, `RowProvenance`, the sidecar's layer dims and boolean variables).
- `CONTRACT_VERSION` (and `STAMP_CONTRACT_VERSION`, `RUN_META_CONTRACT_VERSION`, `ROW_SET_CONTRACT_VERSION`) is `contract_hash(CONTRACT)`: `digest_bytes` of the canonical JSON of the declaration, the meta model by its JSON Schema without `title` and `description`, so a docstring or a field's description does not change it (as CR-083 for specs). 32 hex digits, written to a store's `contract_version` attr as a string.
- C1's declaration also holds the check thresholds of `ponzi.contracts.validate` (`GAP_FACTOR`, `MIN_VALID_FRACTION`, ...), which the engine report says are part of it. `ponzi_pipeline.engine` reports `ponzi.contracts.coherence.CONTRACT_VERSION` instead of its own, and a test holds the thresholds it repeats equal to validate's.
- Readers compare as they do now (a mismatch is what each reader made of one before: a failed check in `validate_sidecar`, a problem in `validate-store`, a warning in the engine report). A store whose `contract_version` is an integer is of before this CR and is refused as any mismatch, and made again: nothing published is pinned to one.
- A test per contract pins its hash, so a change to a declaration is seen in review: the test fails and says to update the pin and the contract's page.
- The limit, accepted: a change of meaning the declaration does not hold (the units of a variable, say) does not change the hash. Such a change is a MAJOR of the library by the version rules and is written into the declaration's `notes` field, which is hashed, to change it.

### Record files: the hash of the declared schema
The small files PONZI writes and reads back are versioned as the stores are: each declares its layout (`SCHEMA` or `STAMP` in its module, its keys and their types, or its model) and its version is `contract_hash` of that, a string of 32 hex digits where an integer was.
- The forecasting accumulators (C10): `SCHEMA_VERSION`, the npz's `schema_version`. It is a contract, and is named `CONTRACT_VERSION` with the others.
- The engine report: one declaration and one hash, in `ponzi.contracts.validate` (the reader); `ponzi_pipeline.engine` (the writer, which depends on `ponzi`) imports it. `ENGINE_REPORT_SCHEMA_VERSION` and the engine's `SCHEMA_VERSION` are removed. The reader's "newer than ours" becomes "not ours", since hashes have no order.
- `panel.json` (`ponzi_models.panels.panel`): `SCHEMA_VERSION`, refused when it differs, as now.
- The run stamp's window (`WINDOW_SCHEMA`, stamped `ponzi_window_schema`): folded into the run stamp's declaration, so `STAMP_CONTRACT_VERSION` covers it, and the separate number is removed.
- `onboard_meta.json` (`ponzi_pipeline.onboard`): `STAMP_VERSION`, the file's `stamp_version`.
Each hash is pinned by a test, as a contract's is.

Found while implementing, and versioned the same way:
- the manifest (`ponzi_spec.manifest`): `MANIFEST_VERSION`, a manifest's `manifest_version`, is the hash of `Manifest` and the summary keys;
- the label store (C11, `ponzi.evaluation.labels`): `LABEL_SCHEMA`, the store's `label_schema`;
- the staged rule (`ponzi.core.staged`): `RULE_VERSION`, the `version` of every `staged_rule`, is the hash of the rule's text (`RULE`); a calibration made under another rule is refused, as before.

### What a reader does with another version
C1's `contract_version` was only required to be present; `validate-store`'s `identity` check now also warns when it is not C1's. A pixel sample of another version fails its `identity` check (it is exported again), a sidecar fails `contract_version`, an engine report is warned of, a `panel.json` is refused.

### Found while implementing
- `output_id` (ponzi-service, the id of each output of a stage with many, `tile`) left the code majors out; with `StageRef` carrying them, every id built from a stage's ref has them.
- C1's check thresholds and catalogue move from `ponzi.contracts.validate` into `ponzi.contracts.coherence`, beside the declaration that holds them; `validate` imports them.
- ponzi-service's `openapi.json` `info.version` is the API's (`v1`), not the server's version, which now changes with every commit; `/v1/health` reports the server's.
- ponzi-visual shows its version at the foot of the open drawer.

### Not changed here
`API_VERSION` (`v1`) and the extension's own version stay numbers a person sets.

## Do results change?
No number changes. Every content id changes once (the stage version leaves the payload), so a cache made before is not reused; every store's `contract_version` and every record file's version change from an integer to its hash, so files written before are refused (a built panel, an onboarding stamp, a run's forecasting accumulators) and are made again. Nothing published is pinned to either.

## Tests
ponzi-spec: content ids without a stage version, with and without `code`; `StageRef` and `PonziFields` validate against the v0.2.0 extension schema; `contract_hash` ignores titles and descriptions. ponzi (core): each contract's and record file's hash pinned, a store of an integer `contract_version` refused. ponzi-pipeline: the engine's thresholds equal validate's, its report carries the reader's hash. ponzi-models: a `panel.json` of an integer `schema_version` refused. ponzi-service: every computing stage names its `code`; job and batch ids from the payload alone; the three distributions report their tag's version. ponzi-visual: its fixtures' `ponzi:stage`; the footer shows the defined version; a build without git gives `0.0.0`.

## Version
Library: `ponzi-spec`, `ponzi`, `ponzi-pipeline` and `ponzi-models` major (content ids, the STAC extension and the store attrs change); ponzi-service's three major; ponzi-visual minor (the footer; its fixtures follow the extension). Standard: none registered; s1-general stays a draft.
