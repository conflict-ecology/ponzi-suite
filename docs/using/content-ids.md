# Content ids

Every Item is named by what made it:

```
content_id = sha256(canonical_json({
    "stage":  {"name": ..., "version": ...},
    "inputs": [sorted content ids of the inputs],
    "config": {identity config of the stage},
    "code":   {distribution: major version}       # only for a stage that names its code
}))[:32]
```

- **Computed before the work runs.** A worker computes the content id of a stage's output from its inputs and config; if the catalog has an Item with that id, the stage does not run. Submitting the same request twice computes nothing the second time.
- **Identity fields only.** The config holds what changes the result (the scoring spec, the coherence spec, the detection spec). Paths, chunk shapes, thread counts and overwrite flags are request fields: recorded in `ponzi:request`, never hashed.
- **The stage version is the stage's own.** A stage raises its identity version whenever its output bytes may change for the same inputs and config. A release that changes no bytes keeps it, so it invalidates no cached result. Every stage, the ingest stages included, is at version `"2"` since ponzi-core CR-070, which renamed the identity parameters (`run` takes `scoring_spec` and `scoring_spec_name`, `detect` and `tile` take `detection`): every content id changed, and everything was made again.
- **The code is part of it** (ponzi-core CR-054). A stage names the distributions whose code computes it (`StageSpec.code`: `ponzi` for `run`, `pvalues`, `detect` and `tile`; `ponzi-pipeline` for `discover`, `dem`, `coherence` and `onboard`; both for `assemble`), and their major versions enter the id (`ponzi_spec.identity.code_majors`). A patch or minor release keeps every id, as the version rules promise the same bytes; a new major gives every output it computes a new id, so the work is done again. The ingest stages name no code and keep their ids. ISCE3 is not named: its build is pinned in the lock file, so a new build that changes results needs a new `ponzi-pipeline` major to rerun the coherence.
- **External inputs** (Sentinel-1 granules, orbit files) get an id from their name and checksum (`external_id`).
- **Item ids** read `<collection>-<scope>-<first 12 digits>`, for example `ponzi-run-t028_058198_iw3-9c1e4d2a7b10`.

Canonical JSON: sorted keys, compact separators, UTF-8, no NaN or infinity. The hashing rule is fixed by a test; changing it would change every id in every catalog.

```python
from ponzi_spec import StageRef, content_id

cid = content_id(StageRef(name="run", version="2"), [coherence_id, sidecar_id], {"scoring_spec": spec, "scoring_spec_name": name})
```
