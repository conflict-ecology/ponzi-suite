# The service: server and clients

**`ponzi-server`** holds run requests, watched areas, jobs and their leases, the published Items, their manifests and assets. It never computes and never calls a worker. It imports only ponzi-spec.

- **Requests.** A request makes one `workflow` job per burst, its id being the content id of the payload: the standard's workflow, its variables and the final steps. The same request is the same job, and a request whose jobs are done is answered with their Items at once (`reused`).
- **Leases.**
    - A claim is atomic and leases only jobs whose stages the worker has.
    - A lease expires unless the client loop holding it (`ponzi-client serve`) heartbeats it, and a heartbeat may move the job to `running`.
    - An expired lease returns the job to the queue, and the job fails after its attempts.
    - A completion of a done job is a no-op. A completion pointing at an asset that was never uploaded (or, in `path` mode, at no file under the outputs root) is refused.
- **Outputs.** The server's settings fix at startup how final assets reach it (`outputs: {mode, root}`), and every lease carries it. In `upload` mode (the default) the client loop uploads them; in `path` mode the server and the machines doing the work see one folder at one path, the client loop writes the files there itself, and uploads are refused. Either way the stored Item points at `/v1/assets/<item_id>/<asset>` on the server, and the outputs folder defaults to `$PONZI_HOME/outputs` (`{data}/assets` when the settings name `data` but no root).
- **The catalogs.** The burst catalog and the administrative boundaries (World Bank Official Boundaries, levels 0 to 2) are downloaded and built into `$PONZI_HOME/catalog` on the first start, in the background. Until they are ready, their routes answer 503, and so do the Major TOM tile routes: a tile is served only over land, a country outline.
- **Watched areas** ([Watched areas](../guides/watched-areas.md)) are made from 1 to 64 Major TOM tiles over land. The server picks every burst, of both passes, meeting the tiles, and makes the area's jobs when it is made; then the scheduler makes them at the area's cadence. `start_date` and `end_date` bound the days it watches. An area made without a standard takes the server's `default_standard`, else the one standard it holds; when it cannot choose, it refuses with a 422 that says to set `default_standard` (CR-068). The boundaries are drawn on a map, never chosen.
- **Tags.** An area's tags are added to the analysis Items of its bursts and tiles as the server serves them (`ponzi:tags`), never stored in an Item or its content id; search takes `tags`.
- **Keys** are scoped (`worker`, `client:read`, `client:write`, `admin`) and kept as hashes. Errors are RFC 9457 problems. The OpenAPI document is committed, and the TypeScript client is generated from it.

**`ponzi-client`** (Python, and the `ponzi-client` command) is the only way agents reach the system. The front end reaches it the same way through its own TypeScript client, generated from the same OpenAPI document. See [The clients](../reference/clients.md).
