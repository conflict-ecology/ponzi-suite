# CR-045: the PONZI home, and the burst catalog made on the server's first start

- **Requested by / date:** owner, 2026-11-04 ("this should be downloaded whenever the server starts at the default location of ~/.ponzi all the data as well should be there"). Decisions, all as recommended: one root for everything; the server serves at once and makes the catalog in the background; the GeoJSON builder moves to ponzi-spec; a worker elsewhere fetches its own burst map.
- **Status:** implemented on the owner's instruction (2026-11-04), awaiting review; uncommitted
- **Superseded in part:** a worker's home is no longer `roots.data` of a deployment config, and the server's folders can no longer be moved out of the home: the home is `$PONZI_HOME` everywhere (CR-088).

## Why

- **Two OPERA files had to be found and placed by hand.** The server needs the burst catalog built from the OPERA burst database's GeoJSON. The coherence stages need the burst map (the bbox SQLite) as `${burst_map}`.
- **Data was scattered.** The server's data defaulted to `~/.local/share/ponzi-service/server`, the worker's cache to the deployment config's root, which had no default, and the downloads to wherever each run said.

## What changes

**The PONZI home (`ponzi_spec.home`):** `$PONZI_HOME`, else `~/.ponzi`, with a fixed layout:

    server/  keys/  standards/  outputs/  catalog/  cache/  downloads/{slc,orbits,dem}/

**Made, not set up by hand** (owner, 2026-11-04: "when I run the server it should handle the dir creation wherever I designate the ponzi dir or just default to ~/.ponzi"):
- `Layout.make` creates every folder, and gives `keys/` mode 700.
- The server calls it at startup, and `ponzi-server keys` before it opens the database. The worker's `serve` and `run` call it for their own home.
- The home is named by `--home` (on `serve` and `keys`), or by `home:` in the settings, or by `$PONZI_HOME`; else it is `~/.ponzi`.
- `ponzi-worker demo` writes its own folder as the home into the `server.yaml` it makes, and every test runs in its own temporary home, so neither touches the real one.

**The deployment config:** `roots.data` defaults to the home instead of being required. So `roots.cache` defaults to `{home}/cache`.

**The catalog (`ponzi_spec.catalog`):**
- The catalog's format and its builder from the GeoJSON move here from `ponzi_pipeline.catalog`. They use the standard library only, so the server can build the file without the computing distributions.
- `ponzi_pipeline.catalog` keeps the bbox-SQLite source (it needs pyproj) and the command, and imports the rest.
- Two files are pinned by URL and sha256:
  - `GEOMETRIES`: burst_db v0.18.0 `burst-id-geometries-simple-0.18.0.geojson.zip`, 59.7 MB, `e3a52b72…`.
  - `BURST_MAP`: burst_db v0.10.0 `opera-burst-bbox-only.sqlite3`, 52.7 MB, `cef180ef…`. v0.10.0 is the last release that publishes it.
- `fetch` downloads a pinned file once (through `.part`, checked, then renamed), and reuses a file that matches.
- `ensure_catalog` builds `catalog/bursts.sqlite3` when it is missing or was built from another source. `ensure_burst_map` gives the burst map.

**The server:**
- Every default comes from the home: `data` `{home}/server` (the database `server.db` in it), `standards` `{home}/standards` (created), and `outputs.root` `{home}/outputs` in both modes.
- A settings file that names `data` but no `outputs.root` keeps uploads in `{data}/assets`, as before.
- `outputs: {mode: path}` no longer needs a `root` (CR-041 required one). A given root must be absolute.
- With no `bursts`, the server uses the home's catalog. When that isn't built yet, the server starts at once and makes it in a background thread. Until then, the burst routes answer 503 ("the burst catalog is being prepared", `Retry-After: 30`). A failed download keeps the API running and says why on those routes.
- A restart reuses the built catalog and downloads nothing. `fetch_catalog: false` turns this off. A given `bursts` file is used as it is.
- The startup log names the home.

**The worker (`ponzi_worker.home`):**
- Its home is the deployment config's `roots.data` when that is a local path, else the PONZI home. A worker on the server's machine therefore shares the server's home, and a worker on a cluster has its own.
- `ponzi-worker serve` downloads the burst map into its home at start (`--no-fetch` skips this). `ponzi-worker run` does so when the workflow names `${burst_map}` and `--set` does not.
- A job's variables `burst_map`, `slc_dir`, `orbit_dir` and `dem_dir`, when unset, come from the home. They are request parameters, never hashed, so no content id changes.

## Do results change?

No. Only where files are kept and how the catalog's two OPERA files arrive. The catalog is built by the same code as before, moved.

One point to check on the first real run: the burst map comes from burst_db v0.10.0 and the footprints from v0.18.0. Burst ids and their boxes come from ESA's fixed burst map, so they should agree. The first coherence run of a Gaza burst will show whether the fixed grid falls where its footprint is.

## Tests

- ponzi-spec:
  - `test_home_catalog.py`: the home and its layout (nothing created); `fetch` checks the sha256, reuses a match, replaces a stale file, and keeps nothing of a bad download; `ensure_catalog` builds from a GeoJSON zip once, with two index entries across the antimeridian, and rebuilds for another source; the pins.
  - `test_config.py`: no root means the home.
- ponzi-server:
  - `test_server_catalog_home.py`: 503 before the start; made at startup; a restart fetches nothing; a failed download keeps the API and says why; a given catalog fetches nothing.
  - The default-place test uses the home. The outputs defaults are tested.
  - Tests and `ponzi-server openapi` never touch the real home.
- ponzi-worker `test_home.py`: the home from the config or the PONZI home; a job's own variables win; the burst map is downloaded once.
- Results: ponzi-core `test` 542 passed, 14 skipped; `test-spec` 56; `test-pipeline` 90 passed, 1 skipped; `test-models` 95 passed, 18 skipped. ponzi-service 121 passed. ponzi-visual 24 unit and 4 end-to-end, with `schema.d.ts` regenerated for the 503.

## Version

- ponzi-spec: minor (new `home` and `catalog`; `roots.data` optional).
- ponzi-pipeline: minor (the catalog's builder imported from ponzi-spec; the same names exported).
- ponzi-server and ponzi-worker: their first release (0.1.0 has never been released).
