# REST API

!!! warning "Under construction"
    ponzi-server is still being built; the routes and their bodies may change.

Version `v1`. The request and response bodies are the models of `ponzi_spec.api` ([reference](../reference/ponzi-spec.md#rest-api-models)). The table is generated from the OpenAPI document ponzi-server commits (`packages/server/openapi.json` in ponzi-service, written by `ponzi-server openapi`), so it is the server's own list. *Scope* is the key scope a route needs (`x-ponzi-scope`).

<!-- ponzi:rest-api -->

Rules:

- Clients always initiate: the client loop (`ponzi-client serve`, with a `worker` key) claims, heartbeats, uploads and completes. The server never calls a client or a worker (its only call out is the read-only ASF search for a burst's acquisitions, CR-060), and the worker calls it only to upload outputs with a one-time ticket the loop hands it (CR-098).
- Keys are scoped (`user`, `user-admin`, `visual`, `client:read`, `client:write`, `worker`, `admin`) and sent as bearer tokens. `admin` holds every scope, `client:write` holds `client:read`, `user-admin` holds `user`, and `user` holds `client:read`.
- The app's own key (`visual`) holds nothing without a person's session: `POST /v1/sessions` logs a person in and sets the `ponzi_session` cookie, and later calls with the app's key and that cookie act as the person. A cookie without the app's key counts for nothing.
- `/v1/watch-requests` are a person's requests to watch tiles; `/v1/requests` are one-off runs of bursts.
- A lease expires unless heartbeated; an expired lease returns the job to the queue, and completing a job that is already done does nothing.
- Every lease carries the server's `Outputs` (`mode`: `upload` or `path`, and the `root` in `path` mode), which says how the final assets are delivered.
- The burst and boundary routes answer 503 with `Retry-After` while the server is still building their catalogs, and so do the Major TOM tile routes (`/v1/majortom/...`) and making an area, which need the land (the level 0 boundaries, the disputed areas included, CR-069). The boundary routes are for drawing a map: an area is made of tiles only (CR-067).
- Errors are `Problem` bodies (RFC 9457).
