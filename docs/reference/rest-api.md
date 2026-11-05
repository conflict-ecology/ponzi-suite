# REST API

Version `v1`. The request and response bodies are the models of `ponzi_spec.api` ([reference](ponzi-spec.md#rest-api-models)). The table is generated from the OpenAPI document ponzi-server commits (`packages/server/openapi.json` in ponzi-service, written by `ponzi-server openapi`), so it is the server's own list. *Scope* is the key scope a route needs (`x-ponzi-scope`).

<!-- ponzi:rest-api -->

Rules:

- Clients always initiate: the client loop (`ponzi-client serve`, with a `worker` key) claims, heartbeats, uploads and completes. The server never calls out, and the worker never calls the server.
- Keys are scoped (`worker`, `client:read`, `client:write`, `admin`) and sent as bearer tokens. `admin` holds every scope, and `client:write` holds `client:read`.
- A lease expires unless heartbeated; an expired lease returns the job to the queue, and completing a job that is already done does nothing.
- Every lease carries the server's `Outputs` (`mode`: `upload` or `path`, and the `root` in `path` mode), which says how the client loop delivers the final assets.
- The burst and boundary routes answer 503 with `Retry-After` while the server is still building their catalogs.
- Errors are `Problem` bodies (RFC 9457).
