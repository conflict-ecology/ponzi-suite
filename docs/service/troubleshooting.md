# Troubleshooting

The failures met most often, as you see them, with their cause and what to do. The server answers an error as a problem document (RFC 9457) with a status, a title and a detail; ponzi-client prints it as `status title: detail`, and ponzi-visual shows the same line where the call was made (the note at the top of the map, the side panel). The texts quoted below are the server's and the tools' own.

| You see | Section |
| --- | --- |
| `503 Service Unavailable: the boundaries are being prepared` (or `the burst catalog is being prepared`) | [Being prepared](#the-boundaries-or-the-burst-catalog-are-being-prepared) |
| `... could not be made: ...`, or `no boundaries: set fetch_boundaries ...` | [Could not be made](#the-boundaries-or-the-burst-catalog-could-not-be-made) |
| `422 ...: no standard given and the server has no default: ...` | [No default](#no-standard-given-and-the-server-has-no-default) |
| `422 ...: no standard ...`, or the warning `area ...: no standard ...` | [A standard the server does not hold](#a-standard-the-server-does-not-hold) |
| `401 Unauthorized`, `403 Forbidden` | [Keys](#401-or-403-from-the-server) |
| `no Earthdata credentials: ...`, or a 401 from Earthdata Login | [Earthdata](#earthdata-refuses-the-download) |
| `this worker cannot run ...: requires ...` | [Requirements](#a-worker-refuses-a-standards-job) |
| a box on the map adds no tiles, or only some | [Tiles](#a-box-on-the-map-adds-no-tiles-or-only-some) |
| `No burst of the catalog meets them.` | [No bursts](#no-burst-of-the-catalog-meets-the-tiles) |
| `PONZI runs on Linux (x86-64) only for now: ...` | [Platform](#dev-install-or-dev-up-stops-at-once) |
| pixi refuses `ml-gpu` or `isce3` | [CUDA](#pixi-refuses-ml-gpu-or-isce3) |
| `ENOSPC: System limit for number of file watchers reached` | [File watchers](#the-front-ends-dev-server-runs-out-of-file-watchers) |

## Where to look

- **The server's log.** `ponzi-server serve` logs to its standard error: the home, the database and how many keys are active, the outputs, a `default_standard` it does not hold, the progress of the boundaries and the burst catalog, the scheduler's warnings, and one access line per call (who, address, method, path, status, time). Under `pixi run dev-up` it is appended to `$PONZI_HOME/logs/server/serve.log`.
- **`$PONZI_HOME/logs/`** holds every log PONZI writes to files (CR-064): each SLURM task's output, the client loop's, and, under `pixi run dev-up`, the server's and the front end's ([Folders and environment variables](../getting-started/paths.md#the-ponzi-home)).
- **A job's error.** A failed job keeps the error its worker reported: `ponzi-client jobs --area AREA_ID` (or `--status failed`) lists it. An area's card, in the map's panel, counts its failed jobs. For a SLURM batch, `ponzi-worker batch BATCH` reads the failed tasks from `sacct` ([Running on SLURM](hpc.md#logs)).

## The boundaries or the burst catalog are being prepared

**You see.** `503 Service Unavailable: the boundaries are being prepared`, or `503 Service Unavailable: the burst catalog is being prepared`. On the map, the controls say `Boundaries: 503 ...` and the map draws only its graticule; from ×32 the note says `Tiles: 503 ...`; with tiles selected, `Bursts: 503 ...`.

**Cause.** On its first start the server downloads the World Bank Official Boundaries and the OPERA burst database and builds them into `$PONZI_HOME/catalog` (`boundaries.sqlite3`, `bursts.sqlite3`), in the background; its log says `boundaries: making them in ...` and `burst catalog: making it in ...`, then the file and its counts when done. Until each is ready, its routes answer 503 with `Retry-After: 30`. The boundaries are the land, so until they are ready the Major TOM tile routes and making an area answer 503 too; the bursts of tiles and making an area also need the burst catalog. The sources are pinned by URL and sha256: a release of the server that pins a new source finds the built file out of date and builds it again on its next start, so the 503 comes back once after such an upgrade.

**Fix.** Wait, and call again. Nothing retries by itself: ponzi-client prints the error and stops, and the map asks again only when the view moves (it asks for the boundaries and tiles in view each time) or when the page is reloaded. Reload the page once the server's log says the file is built.

See [Running the server](server.md) and [Watched areas](../using/watched-areas.md).

## The boundaries or the burst catalog could not be made

**You see.** `503 Service Unavailable: the boundaries could not be made: ...` (or `the burst catalog could not be made: ...`), and the same error in the server's log after `boundaries:` or `burst catalog:`. Or `no boundaries: set fetch_boundaries to make .../catalog/boundaries.sqlite3` (and `no burst catalog: build .../catalog/bursts.sqlite3 (ponzi-pipeline burst-catalog), or set fetch_catalog to make it`).

**Cause.** The download or the build failed (the network, the disk, a file whose sha256 does not match its pin); the API keeps running and answers 503 with the reason. The second form means the home's `catalog/` has no such file and `fetch_boundaries` (or `fetch_catalog`) is false, as in the demo, so the server never makes one.

**Fix.** Mend the cause and restart the server: the build is tried at start only, and a downloaded file whose sha256 matches is kept, not fetched again. For the second form, copy a built file into the home's `catalog/` (`boundaries.sqlite3`, `bursts.sqlite3`) or set the `fetch_` setting to true ([Running the server](server.md#running)).

## No standard given and the server has no default

**You see.** Making an area (from the map's **Watch**, or `area-create` without `--standard`):

```
422 Unprocessable Content: no standard given and the server has no default: it holds 2 (...); give `standard`, or set `default_standard` in the server's settings
```

or `... it holds none; ...`. Or `422 Unprocessable Content: the server's default_standard: no standard ... (known: ...)`, which the server also warns of at start (`default_standard: no standard ... (known: ...); an area made without a standard is refused`).

**Cause.** An area made without a standard takes the server's `default_standard`, else the one standard it holds (ponzi-core CR-068). With several and no `default_standard`, with none, or with a `default_standard` it does not hold, it cannot choose. ponzi-visual never sends a standard, so it always depends on this.

**Fix.** Set `default_standard` in the server's settings (`server: {default_standard: s1-general}`, or a key `s1-general@<hash8>` when it holds several versions) and restart it. Under `pixi run dev-up`, write that to a file and give it as `PONZI_SERVER_SETTINGS` ([Quickstart](../getting-started/quickstart.md#development-setup)). With none held, copy a standard's file into the standards folder, `$PONZI_HOME/standards`, and restart ([Building a standard](../models/standards.md)). From the command line, `--standard` names one instead.

## A standard the server does not hold

**You see.** `422 Unprocessable Content: no standard s1-general@3f9a12c4 (known: ...)` when making or changing an area with that standard (or `standard s1-general: 2 versions are held (...); name one` for an id with several versions held). For an area that already names it, the server logs a warning `area AREA_ID: no standard ...` each time the area is due, makes no jobs for it, and **Look now** (`area-discover`) answers 422 with the same text.

**Cause.** The server reads its standards once, from the standards folder, when it starts. A file added, renamed or removed afterwards is not seen; an area whose standard is no longer there is skipped.

**Fix.** Put the standard's file in the standards folder and restart the server. Or move the area to a standard the server holds: `ponzi-client area-update AREA_ID --standard ...`. `GET /v1/standards` (or **Connect** in the app, which calls it) lists what the server holds.

## 401 or 403 from the server

**You see.** `401 Unauthorized: a valid key is needed (Authorization: Bearer <key>)`, or `403 Forbidden: the key does not hold the scope ...`. In the app, the key form shows it on **Connect**; a key revoked while connected makes every call answer 401.

**Cause.** 401: no key was sent, or the key is unknown or revoked. 403: the key is valid but its scope does not cover the call. The scopes are `client:read` (read), `client:write` (that, and make areas and runs), `worker` (claim jobs and deliver outputs: the key of `ponzi-client serve`, and only that) and `admin` (everything). A `worker` key cannot read areas, and a `client:write` key cannot claim jobs.

**Fix.** Check the key with `ponzi-server keys list` on the server's machine, and make one of the right scope with `ponzi-server keys add` ([Logins and keys](../getting-started/authentication.md#ponzi-server-keys)). ponzi-client reads `$PONZI_KEY`, else the file `$PONZI_KEY_FILE` (an empty file stops it with `$PONZI_KEY_FILE: ... is empty`). In the app, **Disconnect** and enter the new key. A server with no active key logs `no active keys: nothing can be called; make one with ponzi-server keys add` at start.

## Earthdata refuses the download

**You see.** A job fails with ``PermissionError: no Earthdata credentials: set EARTHDATA_USERNAME and EARTHDATA_PASSWORD, or add `machine urs.earthdata.nasa.gov login USER password PASSWORD` to ... (mode 600)``, or with a parse error naming the netrc file and its line, or the Earthdata login answers 401 when the SLCs are downloaded.

**Cause.** The SLCs are downloaded from ASF with Earthdata Login, read on the machine that runs the download: `EARTHDATA_USERNAME` and `EARTHDATA_PASSWORD` when both are set, else the `urs.earthdata.nasa.gov` line of `$NETRC` (else `~/.netrc`). A 401 means the login was refused: a wrong username (it is not the email address) or password, or an account without the application *Alaska Satellite Facility Data Access* approved.

**Fix.** See [Logins and keys](../getting-started/authentication.md#the-netrc-file). On a cluster, the credentials must be where the SLURM tasks run, not only on the login node.

## A worker refuses a standard's job

**You see.** A job fails with `job ...: this worker cannot run s1-general@3f9a12c4: requires ponzi-models ..., installed is ...` (or `..., which is not installed`).

**Cause.** A standard can name the distributions and versions a worker must have (`requires`, PEP 440 specifiers; ponzi-core CR-055). The worker checks them before it runs the job and refuses when its environment does not meet them. The failure is reported to the server, which queues the job again while attempts remain (`max_attempts`, default 3) and then marks it failed.

**Fix.** Install a release of the worker's environment that meets the standard's `requires`. An area's next look on a later day makes new jobs (a job is named by its payload, which holds its last day), so they run again; **Look now** on the same day finds the same failed jobs. A one-off run submitted again (`ponzi-client submit`) gives its failed jobs another round of attempts. See [Workflows and the cache](worker.md) and [Standard versions](../models/versions.md).

## A box on the map adds no tiles, or only some

**You see.** A drag on the map pans, or draws a box that adds nothing, or adds fewer tiles than it covers.

**Cause.**

- Below ×32 there are no tiles, and a left drag pans. The note says `Zoom in to ×32 to choose Major TOM tiles`.
- Past 64 tiles the map and the panel warn (`More than 64 tiles: a large area, with many bursts to fetch`), but the area is still made (CR-074). An area is refused only when its bursts pass 5000: `GET /v1/majortom/bursts` and `/tracks` take at most 64 tiles a request, so a client asks for more in groups.
- A box adds only the tiles loaded for the view. While the note says `Loading tiles…`, some are not there yet.
- There are no tiles over open sea, and none at all while the boundaries are being prepared ([above](#the-boundaries-or-the-burst-catalog-are-being-prepared)).
- Shift held while dragging removes tiles instead.

**Fix.** Zoom in to ×32, wait for the tiles, remove tiles to make room, or make a second area. See [Using the map](../using/map.md#choosing-tiles).

## No burst of the catalog meets the tiles

**You see.** The panel says `No burst of the catalog meets them.` and **Watch** is off; from the command line, `422 Unprocessable Content: no burst of the catalog meets the tile ...` (or `the N tiles`).

**Cause.** The server's burst catalog holds no burst whose footprint meets the tiles. The home's catalog built from the OPERA burst database covers the world's bursts; a home with only a small `catalog/bursts.json`, as the demo's, covers only those.

**Fix.** Choose tiles where the catalog has bursts, or give the home the full catalog, `catalog/bursts.sqlite3` (`ponzi-pipeline burst-catalog`, or the server's own download with `fetch_catalog` true and no `bursts.json` there), which the server reads before `bursts.json`, and restart it. See [Running the server](server.md#running).

## dev-install or dev-up stops at once

**You see.** For example, on a Mac:

```
PONZI runs on Linux (x86-64) only for now: this machine is Darwin arm64.
The pixi workspaces of ponzi-core, ponzi-service and ponzi-visual are solved for linux-64 alone.
```

**Cause.** The pixi workspaces are solved for `linux-64` only, so both scripts stop before they clone or install anything on another platform.

**Fix.** Run them on Linux on x86-64. Other early stops of `pixi run dev-up` say what to do: `... is missing: run pixi run dev-install first`, `port ... is in use: stop what runs there, or set PONZI_SERVER_PORT / PONZI_VISUAL_PORT`, and `ponzi-server stopped; see .../server/serve.log`. See [Install](../getting-started/install.md#for-development).

## pixi refuses ml-gpu or isce3

**You see.** `pixi install -e ml-gpu` (or `isce3`, or `pixi run dev-install ml-gpu`) refuses to install, for want of CUDA.

**Cause.** The two environments are on the platform `linux-64-cuda`: they need an NVIDIA driver for CUDA 12.9 (575 or later), which pixi checks through its virtual package `__cuda`.

**Fix.** On a machine with such a driver, update the driver. On one without a GPU (a CI runner, a laptop), `CONDA_OVERRIDE_CUDA=12.9` installs them anyway. See [GPUs and CUDA](../getting-started/install.md#gpus-and-cuda).

## The front end's dev server runs out of file watchers

**You see.** `pixi run dev` in ponzi-visual (or `pixi run dev-up`) stops with `ENOSPC: System limit for number of file watchers reached`.

**Cause.** Other programs have used up Linux's inotify watchers, which the dev server needs to follow the source files.

**Fix.** Raise the limit with `sudo sysctl fs.inotify.max_user_watches=524288`, and add `fs.inotify.max_user_watches=524288` to `/etc/sysctl.d/99-inotify.conf` to keep it.
