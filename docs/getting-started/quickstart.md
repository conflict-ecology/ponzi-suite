# Quickstart: the whole system on one machine

The demo makes a working installation on local disk, with no cluster, no GPU and no network beyond package downloads:

- a standard, made by the lifecycle rehearsal on the CPU;
- a server holding it;
- five bursts run by a worker;
- a watched area.

```
# side by side
git clone .../ponzi-core
git clone .../ponzi-service
git clone .../ponzi-visual
cd ponzi-visual && pixi run install
# makes the demo the first time (about 15 s), serves it on :8799,
# prints the keys to log in with
pixi run server
```

Then, in another shell:

```
cd ponzi-visual && pixi run dev      # http://localhost:5173
```

Log in with the **Admin user key** or the **User key** the server printed. Every scope's key is in `ponzi-visual/.e2e/demo/keys.json`; the app's own key (`visual`) is read from there by the dev server, never by the browser.

The demo's five bursts are synthetic and on no land, so the map has no tiles to choose at first. The demo's folder, `.e2e/demo`, is the server's PONZI home (CR-088). Its server downloads no administrative boundaries (`fetch_boundaries: false`); to see the boundaries and choose tiles, copy a built `boundaries.sqlite3`, which a server's first start makes in `$PONZI_HOME/catalog/`, into `.e2e/demo/catalog/`. For the bursts of the tiles chosen, build every Sentinel-1 burst with `pixi run catalog` in ponzi-visual before the first `pixi run server`, which then makes the demo with it; or copy `.e2e/bursts.sqlite3` into `.e2e/demo/catalog/`. With the user key you ask for areas on the map (**Request**); with the admin user key you approve them on the **Admin** page, which makes the area. A `client:write` key makes areas and submits runs from Python or the command line directly.

From ponzi-service, in Python or a shell:

```
export PONZI_KEY=$(python -c \
    "import json, sys; print(json.load(sys.stdin)['user'])" \
    < ../ponzi-visual/.e2e/demo/keys.json)
pixi run ponzi-client --url http://127.0.0.1:8799 \
    search --collections ponzi-events-cell
```

## What the demo did

1. **The rehearsal** (`ponzi-models rehearse`, with the rolling fit: `ponzi-worker demo --model tide` fits a tiny TiDE instead, in the `ml` environment). It made a model, its calibrations and the standard `s1-rehearsal` (written by `new-standard`, registered by `register-standard`) on synthetic bursts, on the CPU. See [Building a standard](../models/standards.md).
2. **The server standard** (`ponzi-models standard-workflow --source stores`). The bundle became the workflow the server hands to workers.
3. **A watched area over two of the bursts, looked at once, and one run request over all five.** The area is written as an area of bursts, as areas were made before CR-067, since its bursts are on no land. The worker ran their jobs, one per burst, through the server in the same process. Each ingested a store, onboarded it, ran the model, coded the p-values, detected events, tiled them onto Major TOM cells, and uploaded the final Items.

To start over, remove `ponzi-visual/.e2e/demo`; the next `pixi run server` makes it again. The cache in `.e2e/demo/cache` can be removed at any time: content ids make every entry reproducible.

## Development setup

For developing and testing on Linux ([Install](install.md)), not for deploying, one command from ponzi-suite starts the server, the client loop and the front end together, on the PONZI home instead of the demo. Install them first with `pixi run dev-install` ([Install](install.md#for-development)).

```
cd ponzi-suite
# the server on :8780, the client loop, the app on http://localhost:5180;
# prints two keys
pixi run dev-up
```

- **The server** is `ponzi-server serve` on the PONZI home, listening on 127.0.0.1 only. On its first start it downloads the World Bank boundaries and the burst catalog in the background.
- **The client loop** is `ponzi-client serve -- --executor local`: it claims the server's jobs and runs each on this machine. Its worker key is `$PONZI_HOME/keys/dev-worker.key`.
- **The front end** is ponzi-visual's dev server, forwarding the API to this server and adding the app's own key to every call.

The first start makes four keys in `$PONZI_HOME/keys/`, and a key file is never overwritten, so later starts use the same keys:

| File | Scope | Used by |
| --- | --- | --- |
| `dev-visual.key` | `visual` | the app's dev server, which adds it to every call; never shown |
| `dev-worker.key` | `worker` | the client loop; never shown |
| `dev-admin.key` | `user-admin` | you: printed as **Admin user key**, to log in and approve requests and make keys |
| `dev-user.key` | `user` | you: printed as **User key**, to log in as a plain user |

A `dev-browser.key` left from before is revoked and removed. The logs are appended to `$PONZI_HOME/logs/server/`, `logs/client/` and `logs/visual/`. Ctrl+C stops all three, and when one of them stops, the others are stopped too.

**The development standard.** `dev-up` writes `s1-dev` into the home's `standards/` when it is not there, and makes it the server's `default_standard` unless your settings name another. Its workflow is one step of the stage `dev-hold`, which no worker installs: an area under it gets its jobs, and they wait in the queue, so nothing is downloaded or computed on a development machine.

**The Gaza example.** Once the server's boundaries and burst catalog are ready (a first start builds them in the background), `dev-up` adds a watch request for the tiles over the Gaza Strip, tag `gaza`, from 7 October 2023 with no last day, asked by `dev-user` and approved by `dev-admin`, so the home has an area to search and look at. It is added once per home; `logs/server/dev-seed.log` says how it went.

| Variable | Sets | Default |
| --- | --- | --- |
| `PONZI_HOME` | the home it runs on | `~/.ponzi` |
| `PONZI_SERVER_PORT` | the server's port | `8780` |
| `PONZI_VISUAL_PORT` | the app's port | `5180` |
| `PONZI_SERVER_HOST` | the address the server listens on | `127.0.0.1` |
| `PONZI_SERVER_SETTINGS` | a server settings file; its `public_url` is set to the server's address when it names none | none |
| `PONZI_WORKER_ID` | the name the server records for the client loop | `dev-<host name>` |

To keep a development home apart from your own, point `PONZI_HOME` elsewhere. To skip the downloads, give a settings file:

```
printf 'server:\n  fetch_boundaries: false\n  fetch_catalog: false\n' \
    > /tmp/dev-server.yaml
PONZI_HOME=/tmp/ponzi-dev PONZI_SERVER_SETTINGS=/tmp/dev-server.yaml \
    pixi run dev-up
```

To run a real standard instead, write its server file into `$PONZI_HOME/standards` with `ponzi-models standard-workflow` ([Building a standard](../models/standards.md)) and name it as `default_standard` in a settings file given as `PONZI_SERVER_SETTINGS` ([Watched areas](../using/watched-areas.md)). Areas made before keep the standard they were made with.
