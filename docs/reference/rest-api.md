# REST API

Version `v1`. The request and response bodies are the models of `ponzi_spec.api` ([reference](ponzi-spec.md#rest-api-models)); the server (phase 7) publishes the OpenAPI document built from them, which replaces this page's table.

| Resource | Methods | Who | Purpose |
| --- | --- | --- | --- |
| `/v1/bursts` | GET | client | the burst catalog for selection |
| `/v1/standards`, `/v1/models`, `/v1/calibrations` | GET | client | what can be run |
| `/v1/areas` | GET, POST, PATCH, DELETE | client | watched areas (`AreaCreate`, `AreaUpdate`, `Area`) |
| `/v1/requests` | GET, POST | client | one-off runs (`RunSubmission`, `RunRecord`) |
| `/v1/jobs/claim` | POST | worker | lease work (`ClaimRequest` → `ClaimResponse`) |
| `/v1/jobs/{id}/heartbeat` | POST | worker | extend a lease (`Heartbeat`) |
| `/v1/jobs/{id}/complete`, `/fail` | POST | worker | finish a job (`JobComplete`, `JobFail`) |
| `/v1/uploads` | POST | worker | where to put a final asset (`UploadRequest` → `UploadTicket`) |
| `/v1/stac/...` | GET | client | collections, items, search |
| `/v1/manifests/{content_id}` | GET | client | a manifest |

Rules:

- Workers always initiate: they claim, heartbeat, complete and upload. The server never calls a worker.
- Keys are scoped (`worker`, `client:read`, `client:write`, `admin`) and sent as bearer tokens.
- A lease expires unless heartbeated; an expired lease returns the job to the queue, and completing a content id that is already complete does nothing.
- Errors are `Problem` bodies (RFC 9457).
