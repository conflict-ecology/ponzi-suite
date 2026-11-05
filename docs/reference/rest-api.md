# REST API

Version `v1`. The request and response bodies are the models of `ponzi_spec.api` ([reference](ponzi-spec.md#rest-api-models)). The full description is the OpenAPI document ponzi-server commits (`packages/server/openapi.json` in ponzi-service, written by `ponzi-server openapi`); this table is a summary.

| Resource | Methods | Who | Purpose |
| --- | --- | --- | --- |
| `/v1/bursts`, `/v1/bursts/summary`, `/v1/bursts/{burst_id}` | GET | client | the burst catalog for selection (`Burst`, `BurstSummary`) |
| `/v1/boundaries`, `/v1/boundaries/summary`, `/v1/boundaries/{level}/{code}` | GET | client | the administrative boundaries areas are made from (`Boundary`, `BoundarySummary`) |
| `/v1/standards`, `/v1/models`, `/v1/calibrations` | GET | client | what can be run |
| `/v1/areas`, `/v1/areas/{area_id}` | GET, POST, PATCH, DELETE | client | watched areas (`AreaCreate`, `AreaUpdate`, `Area`) |
| `/v1/areas/{area_id}/discover` | POST | client | the area's jobs now, whatever its cadence |
| `/v1/requests`, `/v1/requests/{request_id}` | GET, POST | client | one-off runs (`RunSubmission`, `RunRecord`) |
| `/v1/jobs`, `/v1/jobs/{job_id}` | GET | client | jobs and where they stand (`Job`) |
| `/v1/jobs/claim` | POST | worker | lease work (`ClaimRequest` → `ClaimResponse`) |
| `/v1/jobs/{job_id}/heartbeat` | POST | worker | extend a lease (`Heartbeat` → `Lease`) |
| `/v1/jobs/{job_id}/complete`, `/fail` | POST | worker | finish a job (`JobComplete`, `JobFail`) |
| `/v1/uploads`, `/v1/uploads/{upload_id}` | POST, PUT | worker | where to put a final asset (`UploadRequest` → `UploadTicket`), then its bytes; refused (409) in `path` mode |
| `/v1/assets/{item_id}/{asset}` | GET | client | a final asset |
| `/v1/stac/...` | GET | client | collections, items, search |
| `/v1/manifests/{content_id}` | GET | client | a manifest (`?format=yaml` for the readable form) |
| `/v1/health` | GET | any key | the server's version |

Rules:

- Workers always initiate: they claim, heartbeat, complete and upload. The server never calls a worker.
- Keys are scoped (`worker`, `client:read`, `client:write`, `admin`) and sent as bearer tokens. `admin` holds every scope, and `client:write` holds `client:read`.
- A lease expires unless heartbeated; an expired lease returns the job to the queue, and completing a job that is already done does nothing.
- Every lease carries the server's `Outputs` (`mode`: `upload` or `path`, and the `root` in `path` mode), which says how the worker delivers the final assets.
- The burst and boundary routes answer 503 with `Retry-After` while the server is still building their catalogs.
- Errors are `Problem` bodies (RFC 9457).
