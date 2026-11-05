# Content ids

Every Item is named by what made it:

```
content_id = sha256(canonical_json({
    "stage":  {"name": ..., "version": ...},
    "inputs": [sorted content ids of the inputs],
    "config": {identity config of the stage},
}))[:32]
```

- **Computed before the work runs.** A worker computes the content id of a stage's output from its inputs and config; if the catalog has an Item with that id, the stage does not run. Submitting the same request twice computes nothing the second time.
- **Identity fields only.** The config holds what changes the result (the run config, the coherence config, the detection recipe). Paths, chunk shapes, thread counts and overwrite flags are request fields: recorded in `ponzi:request`, never hashed.
- **The stage version is the stage's own.** A stage raises its identity version whenever its output bytes may change for the same inputs and config. A release that changes no bytes keeps it, so it invalidates no cached result.
- **External inputs** (Sentinel-1 granules, orbit files) get an id from their name and checksum (`external_id`).
- **Item ids** read `<collection>-<scope>-<first 12 digits>`, for example `ponzi-run-t028_058198_iw3-9c1e4d2a7b10`.

Canonical JSON: sorted keys, compact separators, UTF-8, no NaN or infinity. The hashing rule is fixed by a test; changing it would change every id in every catalog.

```python
from ponzi_spec import StageRef, content_id

cid = content_id(StageRef(name="run", version="1"), [coherence_id, sidecar_id], {"config_hash": h})
```
