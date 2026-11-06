# Quickstart: the whole system on one machine

The demo makes a working installation on local disk, with no cluster, no GPU and no network beyond package downloads:

- a standard, made by the lifecycle rehearsal on the CPU;
- a server holding it;
- five bursts run by a worker;
- a watched area.

```
git clone .../ponzi-core && git clone .../ponzi-service && git clone .../ponzi-visual   # side by side
cd ponzi-visual && pixi run install
pixi run server        # makes the demo the first time (about 15 s), serves it on :8799, prints the key to enter
```

Then, in another shell:

```
cd ponzi-visual && pixi run dev      # http://localhost:5173
```

Connect with the key the server printed; every scope's key is in `ponzi-visual/.e2e/demo/keys.json`.

The map holds the demo's five bursts. To select from every Sentinel-1 burst, build the full catalog with `pixi run catalog` in ponzi-visual before the first `pixi run server`, which then makes the demo with it; or set `bursts:` in `.e2e/demo/server.yaml` to `.e2e/bursts.sqlite3`. The demo's server downloads no administrative boundaries (`fetch_boundaries: false`); to see the boundaries and choose tiles, set `boundaries:` in `server.yaml` to a built `boundaries.sqlite3`, which a server's first start makes in `$PONZI_HOME/catalog/`. A `client:write` key can create areas in the app, and submit runs from Python or the command line.

From ponzi-service, in Python or a shell:

```
export PONZI_KEY=$(python -c "import json; print(json.load(open('../ponzi-visual/.e2e/demo/keys.json'))['client:read'])")
pixi run ponzi-client --url http://127.0.0.1:8799 search --collections ponzi-events-cell
```

## What the demo did

1. **The rehearsal** (`ponzi-models rehearse`). It built synthetic bursts and a panel, fitted a model (the rolling fit; a tiny TiDE with `--model tide` in the `ml` environment), registered it, ran the null on the panel's test bursts, calibrated, and wrote the standard bundle, checked against the registry. See [Making a standard](standards.md).
2. **The server standard** (`ponzi-models standard-workflow --source stores`). The bundle became the workflow the server hands to workers.
3. **A watched area over two of the bursts, looked at once, and one run request over all five.** The worker ran their jobs, one per burst, through the server in the same process. Each ingested a store, onboarded it, ran the model, coded the p-values, detected events, tiled them onto Major TOM cells, and uploaded the final Items.

To start over, remove `ponzi-visual/.e2e/demo`; the next `pixi run server` makes it again. The cache in `.e2e/demo/cache` can be removed at any time: content ids make every entry reproducible.

## Development on your own home

For developing and testing on Linux (x86-64; the command stops on any other system), not for deploying, one command from ponzi-suite starts the server, the client loop and the front end together, on the PONZI home instead of the demo. Install them first with `pixi run dev-install` ([Install](install.md#for-development)).

```
cd ponzi-suite
pixi run dev-up              # the server on :8780, the client loop, the app on http://localhost:5180
```

- **The server** is `ponzi-server serve` on the PONZI home, listening on 127.0.0.1 only. On its first start it downloads the World Bank boundaries and the burst catalog in the background.
- **The client loop** is `ponzi-client serve -- --executor local`: it claims the server's jobs and runs each on this machine. Its worker key is `$PONZI_HOME/keys/dev-worker.key`.
- **The front end** is ponzi-visual's dev server, forwarding the API to this server.

The first start makes the two keys it needs in `$PONZI_HOME/keys/`: `dev-worker.key` (scope `worker`) and `dev-browser.key` (`client:write`). A key file is never overwritten, so later starts use the same keys. The browser key is printed for you to enter in the app; the worker key is never shown. The logs are appended to `$PONZI_HOME/logs/server/`, `logs/client/` and `logs/visual/`. Ctrl+C stops all three, and when one of them stops, the others are stopped too.

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
printf 'server:\n  fetch_boundaries: false\n  fetch_catalog: false\n' > /tmp/dev-server.yaml
PONZI_HOME=/tmp/ponzi-dev PONZI_SERVER_SETTINGS=/tmp/dev-server.yaml pixi run dev-up
```

A new home has no standard, and a watched area needs one: copy one into `$PONZI_HOME/standards` and start again ([Making a standard](standards.md)). With exactly one there, the areas the app makes take it. With several, name the one areas take in a settings file (`server: {default_standard: s1-general@1.0.0}`) given as `PONZI_SERVER_SETTINGS`; without it the server refuses the app's areas and says so. Run requests from Python or the command line always name their standard.
