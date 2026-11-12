# CR-091: a standard's workflow is recorded once, in the registry, and every run is held to it

- **Requested by / date:** owner, 2026-11-12 (on the gap left by CR-089: "what are my options for the hash problem?", then option 1 with the registry as the one record)
- **Status:** signed off (2026-11-12; files without `workflow_hash` accepted), implemented (unreleased)

## Why
A standard's key, `<id>@<hash8>` (CR-089), is the hash of its bundle: its fields and the hashes of the specs it names. It does not cover the workflow `ponzi-models standard-workflow` builds from the bundle: the steps, as the installed ponzi-models lays them out, from the pipeline or from existing stores (`--source`). One key can so name different workflows: built by two releases of ponzi-models, or from the two sources. Outputs do not mix (a job's id is the content id of its payload, which holds the whole workflow), and one server refuses two files of one key, but "areas run `s1-general@3f9a12c4`" does not say which steps ran, and two servers, a server before and after a rebuild, or an agent's local run (CR-090) can run different steps under one key.

Remembering the workflow per key in two places (the server and each worker) would let them disagree. The registry is already where a key is made (`register-standard`), never changes, and is read by every worker that runs the standard; it is the one record.

## What changes
**One function.** `ponzi_spec.identity.workflow_hash(workflow)`: `digest_bytes(canonical_json(workflow))`, the function of spec and contract hashes, over the workflow as data with its `${variables}` unfilled (as the server file and a job's payload hold it). ponzi-models, ponzi-server and ponzi-worker all call it; a test pins the hash of a fixed workflow, so a change to it is a ponzi-spec major.

**The registry records it (ponzi-models).** `standard-workflow` builds the workflow, computes its hash and:
- records it beside the registered standard the first time for that source: `standards/<id>@<hash8>/workflow-<source>.json` (`workflow_hash`, `built_by`: the ponzi-models version, the source, the time; written once, like the rest of the registry);
- later, refuses a build whose hash differs from the record, naming both `built_by`;
- refuses a standard that is not registered (`register-standard` first), since there is no record to keep.
It writes `workflow_hash` and `built_by` into the server file.

**The server checks the file against itself (ponzi-server).** `ponzi_server.catalog.Standard` gains `workflow_hash` and `built_by`. At start the server recomputes `workflow_hash` from the file's `workflow` and refuses a file whose stored hash differs (edited by hand), as it refuses two files of one key. It keeps no memory of its own and never reads the registry, which may be on another machine. `GET /v1/standards` lists `workflow_hash`; a job's payload carries `workflow_hash` and `built_by`.

**The worker holds every run to the registry (ponzi-worker).** Before it runs a standard's workflow, `ponzi-worker job` (a server job) and `ponzi-worker run FILE` (a standard's server file, CR-090) recompute `workflow_hash` from the workflow they were given and compare it with the record in the registry the standard names (`${registry}`): none, or another, is refused before anything runs, with the hashes and `built_by` of both. A bare workflow (no standard) is not checked.

So a key names one workflow per source wherever it runs: the record is written once, the server only checks its file is whole, and the worker, which every run passes through, checks the run against the record. Two registries are two separate worlds, as they are for models and calibrations.

**Decided at sign-off: a server file without `workflow_hash` is accepted.** Files written by hand (the tests' fixtures) have none. The server accepts such a file and lists `workflow_hash: null`, and the worker runs its jobs without the registry check, with a warning in its output; every file `standard-workflow` writes has one. (Refusing them would make every test fixture build a registry.) A job's payload of a standard with a hash gains `workflow_hash` and `built_by`, so such jobs get new ids once.

## Do results change?
No. The steps, their parameters and their content ids are unchanged; a run is refused only when its workflow is not the one recorded.

## Tests
- ponzi-spec: `workflow_hash` of a fixed workflow is pinned; key order and yaml formatting do not change it.
- ponzi-models: `standard-workflow` records the hash once per source, gives the same file again, refuses a different workflow under the recorded key (e.g. a changed step) and an unregistered standard; the server file carries `workflow_hash` and `built_by`.
- ponzi-server: a file whose `workflow_hash` is not its workflow's is refused at start; `GET /v1/standards` and job payloads carry it; a file without one is accepted (per the decision).
- ponzi-worker: a server job and `run FILE` are refused when the registry's record is missing or differs, and run when it matches (the rehearsal's standard, `test_standard.py`); a file without `workflow_hash` runs with a warning.

## Version
Library: `ponzi-spec` minor (a function), `ponzi-models` major (`standard-workflow` needs a registered standard and records it), ponzi-server and ponzi-worker minor (new fields; a refusal of what was always wrong). Standard: no change to keys.
