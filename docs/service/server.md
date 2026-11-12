# The service: server and clients

**`ponzi-server`** holds run requests, watched areas, jobs and their leases, the published Items, their manifests and assets. It never computes and never calls a worker. It imports only ponzi-spec.

- **Requests.** A request makes one `workflow` job per burst, its id being the content id of the payload: the standard's workflow, its variables and the final steps. The same request is the same job, and a request whose jobs are done is answered with their Items at once (`reused`).
- **Leases.**
    - A claim is atomic and leases only jobs whose stages the worker has.
    - A lease expires unless the client loop holding it (`ponzi-client serve`) heartbeats it, and a heartbeat may move the job to `running`.
    - An expired lease returns the job to the queue, and the job fails after its attempts.
    - A completion of a done job is a no-op. A completion pointing at an asset that was never uploaded (or, in `path` mode, at no file under the home's `outputs/`) is refused.
- **Outputs.** The server's settings fix at startup how final assets reach it (`outputs: {mode}`), and every lease carries it. In `upload` mode (the default) the client loop uploads them; in `path` mode the server and the machines doing the work share one home at one path, the client loop writes the files into its `outputs/` itself, and uploads are refused. Either way the stored Item points at `/v1/assets/<item_id>/<asset>` on the server, and the outputs folder is `$PONZI_HOME/outputs` (CR-088).
- **The catalogs.** The burst catalog and the administrative boundaries (World Bank Official Boundaries, levels 0 to 2; level 0 is read from the "Admin 0_all_layers" file, which adds the 24 areas of non-determined legal status as boundaries with `disputed` true, CR-069) are downloaded and built into `$PONZI_HOME/catalog` on the first start, in the background. Until they are ready, their routes answer 503, and so do the Major TOM tile routes: a tile is served only over land, a level 0 outline (a country or a disputed area).
- **Watched areas** ([Watched areas](../using/watched-areas.md)) are made from 1 or more Major TOM tiles over land (past 64 the server logs a warning, CR-074). The server picks every burst, of both passes, meeting the tiles, and makes the area's jobs when it is made; then the scheduler makes them at the area's cadence. `start_date` and `end_date` bound the days it watches. An area made without a standard takes the server's `default_standard`, else the one standard it holds; when it cannot choose, it refuses with a 422 that says to set `default_standard` (CR-068). The boundaries are drawn on a map, never chosen.
- **Tags.** An area's tags are added to the analysis Items of its bursts and tiles as the server serves them (`ponzi:tags`), never stored in an Item or its content id; search takes `tags`.
- **Keys** are scoped (`worker`, `client:read`, `client:write`, `admin`) and kept as hashes. Errors are RFC 9457 problems. The OpenAPI document is committed, and the TypeScript client is generated from it.

**`ponzi-client`** (Python, and the `ponzi-client` command) is the only way agents reach the system. The front end reaches it the same way through its own TypeScript client, generated from the same OpenAPI document. See [The clients](../using/clients.md).

## How work flows

1. A client submits a run (`POST /v1/requests`): bursts and a standard. The server reads the standard from its file in the standards folder, written by `ponzi-models standard-workflow` ([Making a standard](../models/standards.md#from-bundle-to-server)): the worker's workflow, the steps whose Items are final, and fixed variables. It makes one `workflow` job per burst. A watched area makes its jobs the same way, at once and then at its cadence, at most one job per burst and day (`scheduler.py`).
2. The client loop claims jobs it has the stages for (`POST /v1/jobs/claim`) and gets a lease.
    - A heartbeat or a failure report from a lease that is no longer held gets a 409.
    - A late completion from an expired lease is accepted: the outputs are content-addressed, so they are the ones the job makes anyway.
3. The loop delivers each final asset as the lease says (below), then completes the job with the Items and their manifests.
4. Clients find the Items in the STAC subset (`/v1/stac/...`) and read the assets and manifests from there.

## Outputs

```yaml
server:
  outputs: {mode: upload}                              # default
  # outputs: {mode: path}                             # the workers write into $PONZI_HOME/outputs
```

| Mode | For | How an asset arrives |
| --- | --- | --- |
| `upload` | a server on one machine and the work elsewhere, such as a cluster without a shared mount | the loop announces it (`POST /v1/uploads`, with its size and sha256), then `PUT`s the bytes, which are checked against the announcement; an announced upload stays open `upload_seconds` |
| `path` | a server and machines that share one home at one path (one machine, or a shared mount) | the loop writes it whole to `$PONZI_HOME/outputs/<item_id>/<asset>` (through a `.partial` file, renamed); the server checks each is a file of that Item there, makes the folder at startup, and answers an upload with 409 |

The startup log names the mode and the folder. A store folder is zipped in both modes, and a file already there with the same bytes is kept.

## Keys and the access log

The database is the only list of valid keys: it keeps each key's sha256 hash, scope and name, never the key. `ponzi-server keys` works on the database directly, so a key added or revoked counts on the next request, whether the server runs or not ([Authentication](../getting-started/authentication.md#ponzi-server-keys)). A name is unique among the active keys, so the log names one holder. Without `--out`, `keys add` prints the key once.

No route answers without a valid key, `/v1/health` included (any scope). The server serves no API document or docs page: the API document is the committed `openapi.json` ([REST API](rest-api.md)), and a test checks it against the app.

Each request is one line on the logger `ponzi_server.access`: who (the key's name and id, `-` for no key, `invalid-key` for an unknown or revoked one), the client's address, the method and path, the status and the time. A key is never logged.

```
2026-11-04 10:19:53,179 INFO ponzi_server.access - 127.0.0.1 GET /v1/standards 401 1ms
2026-11-04 10:19:53,188 INFO ponzi_server.access alice[80bf1d30346d12fd] 127.0.0.1 GET /v1/health 200 2ms
```

Behind a proxy or a load balancer, start uvicorn with the proxy's headers trusted, so the address logged is the client's and not the proxy's.

## Running

```
ponzi-server serve                                   # default settings
ponzi-server serve --settings server.yaml --port 8000
ponzi-server openapi --out openapi.json
```

Every file of the server is in the PONZI home, `$PONZI_HOME`, else `~/.ponzi`: the database `server/server.db`, the standards in `standards/`, the final assets in `outputs/`, the burst catalog and the boundaries in `catalog/` ([Paths](../getting-started/paths.md#the-ponzi-home)). No setting or flag moves them (CR-088): for another home, set `PONZI_HOME`. A burst catalog or boundaries file built elsewhere is used when it is copied into `catalog/` (`bursts.sqlite3`, `boundaries.sqlite3`; `ponzi-pipeline burst-catalog` writes there by default). The server makes the home's folders and the database when it starts, and says which home and database it uses and how many keys are active, with a warning when none are. A database made by an older server gets the new area columns when the server starts.

## Settings

A settings file holds a `server:` section (or the fields at its top). Every field has a default (`ponzi_server.settings`). It names no folder: a file that names `home`, `data`, `standards`, `bursts`, `boundaries` or `outputs.root` is refused (CR-088).

| Field | Sets | Default |
| --- | --- | --- |
| `database` | a database server, as a SQLAlchemy URL (for example Postgres); a SQLite file must be inside the home | SQLite, `{home}/server/server.db` |
| `public_url` | the server's address | `http://localhost:8000` |
| `lease_seconds`, `max_attempts` | how long a lease lives unheartbeated; the attempts before a job fails | 600, 3 |
| `upload_seconds` | how long an announced upload stays open | 3600 |
| `scheduler_seconds` | how often watched areas are looked at; 0 never (`POST /v1/areas/{id}/discover` still looks) | 300 |
| `default_standard` | the standard of an area made without one | the one standard held |
| `fetch_catalog` | whether to make the home's burst catalog when it has none | true |
| `fetch_boundaries` | whether to make the home's boundaries when it has none | true |
| `outputs` | `mode` ([Outputs](#outputs)) | `upload` |

## Tests

`ponzi_server.testing.local_server` gives tests the real app in-process, its home a given folder (the one place a home is an argument, not `$PONZI_HOME`), with a settable clock and one key per scope; what it is given (standards, a burst catalog, boundaries) is copied into that home (`into_home`).
