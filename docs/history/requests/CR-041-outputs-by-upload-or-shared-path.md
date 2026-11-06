# CR-041: final outputs reach the server by upload or by a shared path

- **Requested by / date:** owner, 2026-11-04 ("the server should only be managing what runs to run, status from which other services get status information from, as well as servicing the final outputs which either get sent from worker to server via api or a path is sent. This path should be determined at startup ... worker is also responsible for handling saving outputs to the right paths.")
- **Status:** signed off by the owner (2026-11-04, "approved"; decisions 1 and 2 as recommended; on 3: "if cluster mounts the share path then the work can just send the path like they are effectively the same machine"), implemented (2026-11-04), awaiting review; uncommitted

## Why

The server's job is to decide what runs, keep the status that other services read, and serve the final outputs. It never computes and never contacts a worker. That's already true except for one thing: final outputs always travel over the API. When the worker runs on a SLURM cluster and the server runs elsewhere, that's the only way. When both run on one machine, or share a file system, the worker uploads bytes the server could read straight from disk, so every output is copied once more and held in the server's memory and network path for no reason.

So the server decides at startup how outputs reach it, and the worker saves them where the server says.

## What changes

**The server's settings** gain an `outputs` section, read once at startup:

```yaml
server:
  outputs:
    mode: upload                    # default: the worker sends each asset over the API
  # outputs:
  #   mode: path                    # the server and its workers see one file system
  #   root: /shared/ponzi/outputs   # at this same path
```

- `upload` (the default, and today's behaviour): the outputs folder is `data/assets`. The worker uploads, and the server writes the files there.
- `path`: the outputs folder is `root`, which the server creates if it's missing. The worker writes the files itself, and the server only reads them. The server can't detect whether a worker shares its file system, so the owner states it here.
- The startup log names the mode and the folder, next to the database line.

**The contract (`ponzi_spec.api`, C-API):**

- `Lease` gains `outputs: Outputs`:
  - `mode`: `upload` or `path`;
  - `root`: the folder, set only in `path` mode.

  It's a new field with a default (`upload`), so an older worker reading a newer server, or the reverse, keeps today's behaviour.
- `JobComplete`: in `path` mode, an asset's href is the absolute path the worker wrote. In `upload` mode, it stays the upload ticket's href.

**The worker (`ponzi_worker.loop.publish`)** follows the lease:

- `upload`: unchanged.
- `path`:
  - The worker writes each final asset to `root/<item_id>/<asset name>`.
  - A store folder is zipped exactly as it would be for an upload, so the outputs folder has one layout in both modes.
  - Each file is written as `<name>.partial` and then renamed, so the server never serves half a file.
  - An asset already there with the same bytes is kept, since outputs are content-addressed.
  - The worker makes no upload calls.

**The server's completion (`jobs.complete`):**

- `path` mode: every local href must point to an existing file `root/<item_id>/<asset>`. Anything else is a 422 (no file there, outside `root`, a different item).
- `upload` mode: local hrefs are refused, as they are now.
- In both modes, the server stores the Item with each href set to `public_url/v1/assets/<item_id>/<asset>`. Clients, ponzi-visual included, which fetches hrefs over HTTP, see the same Items whichever mode the server runs in. `GET /v1/assets` serves from the outputs folder in both modes.
- In `path` mode, `POST /v1/uploads` answers 409 ("this server takes outputs by path").

**What the server does stays inside the owner's list.** Runs to run means requests, watched areas and the scheduler, standards and the burst catalog. Status means jobs, leases, heartbeats and requests. Final outputs means Items, manifests, STAC search and assets. Nothing moves.

## Decisions for the owner

1. **The href a client sees in `path` mode.** Recommended: the server URL, as above, so a remote client or the browser can still read it. The alternative is to store the local path. A client on the same machine would then copy the file directly (`Client.download` already does this), but ponzi-visual and remote clients couldn't read the asset.
2. **Store folders in `path` mode.** Recommended: zipped, as in uploads, so there's one layout and `GET /v1/assets` is unchanged. The alternative is to keep them as folders, which avoids the zip step but means the server has to zip them on the fly when serving.
3. **A cluster that mounts the share.** Decided by the owner: a cluster that mounts the share at the server's path counts as the same machine and uses `path`. A cluster without that mount uses `upload`. A mount at a different path is not covered.

## Do results change?

No. Only where the bytes travel changes. The files, the Items (apart from the transport) and the manifests are the same.

## Tests

- ponzi-core: `Lease` round-trips with and without `outputs`, and the default is `upload`.
- ponzi-server:
  - settings: `path` without `root` is refused; `root` is created at startup; the startup log names the mode;
  - every lease carries the server's mode;
  - `path` completion accepts a file under `root`, refuses a missing file, a path outside `root` and another item's path, and stores server-URL hrefs;
  - uploads are refused in `path` mode, and `GET /v1/assets` serves a path-mode file;
  - the committed `openapi.json` is regenerated because `Lease` changed.
- ponzi-worker:
  - `path` mode writes the zip atomically, makes no upload calls, and keeps an identical existing file;
  - `upload` mode is unchanged;
  - `serve --once` end to end against a test server in each mode.
- ponzi-visual: `pixi run gen` for the new `Lease` field, then `pixi run check-gen` and the tests.
- `pixi run test` passes in every repository.

## Version

- ponzi-spec: minor (0.3.0 to 0.4.0), for one additive field with a default.
- ponzi-server and ponzi-worker: unchanged at 0.1.0, which has never been released, so this change goes into their first release.
- No standard changes.
