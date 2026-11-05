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

The map holds the demo's five bursts. To select from every Sentinel-1 burst, build the full catalog with `pixi run catalog` in ponzi-visual before the first `pixi run server`, which then makes the demo with it; or set `bursts:` in `.e2e/demo/server.yaml` to `.e2e/bursts.sqlite3`. The demo's server downloads no administrative boundaries (`fetch_boundaries: false`); to choose areas from boundaries, set `boundaries:` in `server.yaml` to a built `boundaries.sqlite3`, which a server's first start makes in `$PONZI_HOME/catalog/`. A `client:write` key can create areas and submit runs.

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
