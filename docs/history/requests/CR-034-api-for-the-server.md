# CR-034: the API models the server and the client needed

- **Requested by / date:** owner, 2026-10-23 (phase 7 of the overhaul plan: ponzi-server and ponzi-client, in ponzi-service)
- **Status:** implemented on the owner's instruction (2026-10-23), awaiting review; uncommitted (plan decision D10)

## Why

The server never imports the computing distributions, so it cannot plan stages or compute ingest digests. The unit of work it hands out is therefore a whole workflow, the standard's workflow for one burst, and the worker plans its stages. Building the server and the client also showed what `ponzi_spec.api` was missing.

## What changes in `ponzi_spec.api`

| Model | Change |
| --- | --- |
| `JobKind` | gains `workflow`: the payload is a workflow, its variables and its final steps |
| `Job` | `stages`: the stages a worker needs, so a claim leases only what the worker can run |
| `JobComplete` | `manifests: list[Manifest]` replaces `manifest`: a job publishes several final Items |
| `UploadTicket` | `href`: where the asset is read from once it is uploaded, the href the Item carries |
| `StandardInfo` | new: what `GET /v1/standards` lists |
| `Burst` | new: one entry of the burst catalog, `GET /v1/bursts` |

## Do results change?

No. These are API shapes; no store or Item changes.

## Tests

`pixi run test-spec`: 39 passed. The models are exercised by ponzi-service's 49 tests, which run the server and run the client and the worker against it.

## Version

`ponzi-spec` 0.3.0. `JobComplete.manifest` is gone, which is a breaking change below 1.0. The version also covers CR-033, not yet released.
