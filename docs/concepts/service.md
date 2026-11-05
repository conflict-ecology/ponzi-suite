# The service: server and clients

**`ponzi-server`** holds run requests, watched areas, jobs and their leases, the published Items, their manifests and assets. It never computes and never calls a worker. It imports only ponzi-spec.

- **Requests.** A request makes one `workflow` job per burst, its id being the content id of the payload: the standard's workflow, its variables and the final steps. The same request is the same job, and a request whose jobs are done is answered with their Items at once (`reused`).
- **Leases.**
    - A claim is atomic and leases only jobs whose stages the worker has.
    - A lease expires unless the worker heartbeats it, and a heartbeat may move the job to `running` or `awaiting_approval`.
    - An expired lease returns the job to the queue, and the job fails after its attempts.
    - A completion of a done job is a no-op. A completion pointing at an asset that was never uploaded is refused.
- **The scheduler** makes watched areas' jobs ([Watched areas](../guides/watched-areas.md)).
- **Keys** are scoped (`worker`, `client:read`, `client:write`, `admin`) and kept as hashes. Errors are RFC 9457 problems. The OpenAPI document is committed, and the TypeScript client is generated from it.

**`ponzi-client`** (Python, and the `ponzi-client` command) is the only way agents reach the system. The front end reaches it the same way through its own TypeScript client, generated from the same OpenAPI document. See [The clients](../reference/clients.md).
