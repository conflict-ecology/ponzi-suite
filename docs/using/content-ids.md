# Content ids

Every Item is named by what made it:

```
content_id = sha256(canonical_json({
    "stage":  name,
    "inputs": [sorted content ids of the inputs],
    "config": {identity config of the stage},
    "code":   {distribution: major version}       # only for a stage that names its code
}))[:32]
```

- **Computed before the work runs.** A worker computes the content id of a stage's output from its inputs and config; if the catalog has an Item with that id, the stage does not run. Submitting the same request twice computes nothing the second time.
- **Identity fields only.** The `config` holds the stage's identity params, what changes the result (the scoring spec, the coherence spec, the detection spec). Paths, chunk shapes, thread counts and overwrite flags are request fields: recorded in `ponzi:request`, never hashed.
- **A stage has no version of its own** (ponzi-core CR-085). What changes its output bytes lives in the distributions of its `code`, and a release that changes results is a major of that distribution (the [version rules](../contributing/process.md)), so the code's majors below are what make the work again. An Item records them in `ponzi:stage` (`{name, code}`), so it says which releases made it.
- **The code is part of it** (ponzi-core CR-054). A stage names the distributions whose code computes it (`StageSpec.code`: `ponzi` for `run`, `pvalues`, `detect` and `tile`; `ponzi-pipeline` for `discover`, `dem`, `coherence` and `onboard`; both for `assemble`), and their major versions enter the id (`ponzi_spec.identity.code_majors`). A patch or minor release keeps every id, as the version rules promise the same bytes; a new major gives every output it computes a new id, so the work is done again. The ingest stages name no code and are named by their name alone. ISCE3 is not named: its build is pinned in the lock file, so a new build that changes results needs a new `ponzi-pipeline` major to rerun the coherence.
- **External inputs** (Sentinel-1 granules, orbit files) get an id from their name and checksum (`external_id`).
- **Item ids** read `<collection>-<scope>-<first 12 digits>`, for example `ponzi-run-t028_058198_iw3-9c1e4d2a7b10`.

Canonical JSON: sorted keys, compact separators, UTF-8, no NaN or infinity. The hashing rule is fixed by a test; changing it would change every id in every catalog.

```python
from ponzi_spec import StageRef, content_id

cid = content_id(StageRef(name="run", code={"ponzi": "0.0"}), [coherence_id, sidecar_id], {"scoring_spec": spec, "scoring_spec_name": name})
```
