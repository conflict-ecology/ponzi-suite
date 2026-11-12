# Data sources and catalogs

Where each input of PONZI comes from, who fetches it and where it lands. The server fetches its catalogs once, on its first start; the worker fetches the inputs of a burst as its jobs need them. Every downloaded file is fetched once and reused. The citations of the data and software are in [Citations](../reference/references.md), the logins in [Logins and keys](../getting-started/authentication.md), and the whole home layout in [Folders and environment variables](../getting-started/paths.md).

| Input | Fetched by | When | Lands in | Login |
| --- | --- | --- | --- | --- |
| [Burst catalog](#the-burst-catalog) (OPERA burst database) | server | first start | `$PONZI_HOME/catalog/bursts.sqlite3` | none |
| [Boundaries](#the-administrative-boundaries) (World Bank) | server | first start | `$PONZI_HOME/catalog/boundaries.sqlite3` | none |
| [Major TOM grid](#the-major-tom-grid) | nobody: computed | | | |
| [Burst availability](#burst-availability) (ASF search) | server | when asked, cached | `$PONZI_HOME/catalog/availability/` | none |
| [Burst map](#the-burst-map) (OPERA burst database) | worker | first job that needs it | `$PONZI_HOME/catalog/opera-burst-bbox-only.sqlite3` | none |
| [Acquisitions](#slcs-and-orbit-files) (ASF search) | worker, `discover` | per job | the job's `ponzi-pairs` Item | none |
| [SLCs and orbit files](#slcs-and-orbit-files) (ASF) | worker, `coherence` | per pair | `$PONZI_HOME/downloads/slc/`, `orbits/` | Earthdata |
| [DEM](#the-dem) (Copernicus GLO-30) | worker, `dem` | per burst | `$PONZI_HOME/downloads/dem/` | none |
| [Weather](#era5-land-weather) (ERA5-Land) | worker, `onboard` | per burst and month | `$PONZI_HOME/downloads/era5/` (CDS); Earth Data Hub is read in place | Earth Data Hub or CDS |
| [Built-up and land](#ghsl-built-up-and-land) (GHSL) | worker, `onboard` | per tile | `$PONZI_HOME/downloads/ghsl/` | none |

`$PONZI_HOME` is the home of every part: the server's, the worker's, the SLURM tasks' (CR-088; [Workflows and the cache](../service/worker.md)).

## Fetched by the server on its first start

The server makes the burst catalog and the boundaries in the background when they are missing, each in its own thread, and keeps answering meanwhile. Until one is ready its routes answer 503, and so do the Major TOM tile routes, which need the boundaries. A download goes through a `.part` file, is checked against its pinned sha256, then renamed; a file that does not match is removed and refused. A failure is logged, and the routes then say why. A built file records the sha256 of its source, so a new pin in the code makes the server rebuild it on its next start.

To skip the downloads, copy built files into the home's `catalog/` (`bursts.sqlite3`, `boundaries.sqlite3`; `ponzi-pipeline burst-catalog` writes the first there), which the server uses whatever built them, or turn them off with `fetch_catalog: false` and `fetch_boundaries: false` ([Quickstart](../getting-started/quickstart.md)).

### The burst catalog

Every Sentinel-1 IW burst with its footprint in lon/lat, about 1.1 million bursts, from the OPERA burst database (burst_db). The server lists bursts and finds a watched area's bursts with it.

- **Source:** `burst-id-geometries-simple-0.18.0.geojson.zip` of the burst_db 0.18.0 release (59.7 MB), pinned by URL and sha256 in `ponzi_spec.catalog.GEOMETRIES` (CR-038, CR-045).
- **Built** by `ponzi_spec.catalog.ensure_catalog` with the standard library only: the GeoJSON is streamed and written to `bursts.sqlite3` (its `format` the hash of `ponzi_spec.catalog.CONTRACT`, CR-086), with an R*Tree over the boxes. A burst across the antimeridian has two index entries; a burst repeated with the same footprint is kept once (burst_db 0.18.0 repeats about 141,000). The layout is the contract `ponzi_server.catalog` reads with `sqlite3` only.
- **Lands in** `$PONZI_HOME/catalog/`: the zip as downloaded, and `bursts.sqlite3`.
- **Other ways:** `ponzi-pipeline burst-catalog --source FILE` builds a catalog from another release into the home's `catalog/bursts.sqlite3` (CR-088; `pixi run catalog VERSION` in ponzi-visual writes one to its `.e2e/`). A small JSON list `bursts.json` in its place also works (a demo, a test).

### The administrative boundaries

The administrative units of the World Bank Official Boundaries, drawn on the map as outlines with their names, and, at level 0, the land a Major TOM tile must meet to be listed or watched (CR-053, CR-067). No area is chosen from a boundary.

- **Source:** dataset 0038272 version 3, as GeoParquet, one file per level, each pinned by sha256 in `ponzi_server.boundaries.SOURCES`. Licence CC BY 4.0.

    | Level | File | Holds |
    | --- | --- | --- |
    | 0 | `Admin 0_all_layers` (59 MB) | the 251 countries and territories, and the 24 areas of non-determined legal status (NDLSA), 275 in all |
    | 1 | `Admin 1` | their first subdivisions |
    | 2 | `Admin 2` | their second subdivisions |

- **The disputed areas** (CR-069): the plain Admin 0 file leaves out the NDLSA areas (Jammu and Kashmir, Aksai Chin, Western Sahara, Abyei, the Golan Heights, the Falklands and others); the "all layers" file holds them, so level 0 covers the land. They are kept with `disputed` true. They have no code in the file: theirs is `NDLSA-` and the name in capitals with dashes, with the sovereign's ISO code after it when two share a name (`NDLSA-JAMMU-AND-KASHMIR-IND`, `NDLSA-JAMMU-AND-KASHMIR-PAK`). Each belongs to no country. Antarctica is in neither file and has no tiles.
- **Built** by `ponzi_server.boundaries.ensure_boundaries` (with `pyarrow` and `shapely`) into `boundaries.sqlite3` (its `format` the hash of `ponzi_server.boundaries.CONTRACT`, CR-086): each outline made valid and simplified to `SHAPE`, 0.001 degrees (about 100 m), with an R*Tree over the boxes. The map's outlines are simplified further to its scale when asked.
- **Lands in** `$PONZI_HOME/catalog/`: the Parquet files in `boundaries/`, and `boundaries.sqlite3`.

## The Major TOM grid

The 10 km grid of the panels' cells, the delivered outputs and the tiles of a watched area ([Grids: processing and outputs](grids.md)). Nothing is downloaded: the cells, their ids (`433U_621R`, row then column, named by the bottom-left corner) and their bounds are computed, by `ponzi.grid.MajorTomGrid` and, without numpy for the server, by `ponzi_spec.majortom` (CR-066). Rows cover latitudes -85 to 85.

## Burst availability

When each burst was acquired, and when it will be next (CR-060), for `GET /v1/bursts/{burst_id}/availability`.

- **Source:** ASF's public search API (`dataset=SLC-BURST`, VV), up to 40 bursts per request; the same search the worker's `discover` makes. Read only, no login. Apart from the downloads of its first start, it is the only call the server makes out.
- **Kept** per burst in `$PONZI_HOME/catalog/availability/<burst>.json`. A span is searched again when it reaches past what is kept, or when it reaches today and the copy is older than six hours.
- **The next acquisitions** are predicted from the burst's own cadence (the median gap of its last eight acquisitions): a forecast of the schedule, not a promise. ASF out of reach is a 503.

## Fetched by the worker, per job

The steps of a standard's workflow name their shared inputs by variables (`burst_map`, `slc_dir`, `orbit_dir`, `dem_dir`). Those a job does not set come from the worker's home. They are request parameters, never part of a content id, so where a home is changes no output ([Building a standard](../models/standards.md#from-bundle-to-server)).

### The burst map

Every burst's box in its UTM zone, from which each burst's fixed grid is made (`ponzi_pipeline.bursts.BurstMap`). `opera-burst-bbox-only.sqlite3` of burst_db 0.10.0 (52.7 MB), the last release that publishes it, pinned in `ponzi_spec.catalog.BURST_MAP`. The worker downloads it into `$PONZI_HOME/catalog/` the first time a job needs it (`ponzi_worker.home.ensure_burst_map`), sha256 checked. No login.

### SLCs and orbit files

- **The acquisitions:** the `discover` stage searches ASF's `SLC-BURST` dataset for each burst over the job's span (`ponzi_pipeline.discover`, through `asf_search`) and reads each hit's parent SLC off its download URL. No login.
- **The SLCs:** the `coherence` stage downloads the parent SLC of each acquisition of its pair from ASF, as a zip, into `$PONZI_HOME/downloads/slc/` (`ponzi_pipeline.acquire`, CR-032).
- **The orbit files:** from ASF's S1QC listing, precise (POEORB) before restituted (RESORB), into `$PONZI_HOME/downloads/orbits/`.
- **Login:** Earthdata, for the SLCs and orbits: `EARTHDATA_USERNAME` and `EARTHDATA_PASSWORD`, else the netrc file, never a config (CR-044). The account needs the ASF data access application approved ([Logins and keys](../getting-started/authentication.md)).

A file already in the folder is used as it is. A download writes a `.part` file and renames it, under a lock folder, so array tasks that need the same SLC wait for one download.

### The DEM

The Copernicus DEM GLO-30, stitched by `dem_stitcher` to ellipsoidal heights over the burst's fixed grid, widened by `margin_km` (5 km by default; the coherence spec's `dem: {source: glo_30, margin_km: 5.0}`). The `dem` stage writes `dem_ellipsoidal_glo_30_<box>.tif` into `$PONZI_HOME/downloads/dem/`, with the tiles in `dem/tiles/`; a stitched DEM that already covers the box is reused. No login.

### ERA5-Land weather

The weather series of the sidecar (`era5_*`; by default 2 m temperature, total precipitation, snow cover, snow depth, the 10 m wind components and the top layer's soil moisture), made by the `onboard` stage's `weather` step from ERA5-Land, by `weather_source` of the onboarding spec (`ponzi_pipeline.onboard.weather`). Each source gives the same series with the same definitions:

| Source | From | Login |
| --- | --- | --- |
| `edh` (the default) | the DestinE Earth Data Hub ERA5-Land Zarr store over HTTPS: a lazy open and a few chunk reads, nothing downloaded whole. The store lags real time by months; its quota is 500,000 requests a month. | Earth Data Hub token in the netrc file |
| `cdsgrid` | the gridded ERA5-Land of the Copernicus CDS, one request per calendar month, a few days behind real time | CDS key in `~/.cdsapirc`, and the ERA5-Land licence accepted on the CDS |
| `edh_cdsgrid` | `edh` for what its store covers, `cdsgrid` for the newer acquisitions | both |

A burst's value is the mean over the valid ERA5-Land cells (0.1 degree) covering its footprint and one cell around it. The CDS downloads land in `$PONZI_HOME/downloads/era5/`, shared by every burst (CR-079: a standard's `onboard` step names `${era5_dir}`, which a worker fills from its home; `ponzi-pipeline onboard --era5-cache` defaults to it too). With `weather_area` (CR-023), the bursts of one area share one request per month.

### GHSL built-up and land

The `built` and `land` layers of the sidecar, from the Global Human Settlement Layer of the European Commission's JRC: the built-up surface fraction `GHS_BUILT_S` (R2023A, epoch 2020) and the land fraction `GHS_LAND` (R2022A), both at 100 m on the World Mollweide grid, in 1000 km tiles (`ponzi_pipeline.onboard.built`). The `onboard` stage's `built` step downloads the tiles a burst meets from the JRC's open data server, unzips them and averages them onto the burst's grid. They land in `$PONZI_HOME/downloads/ghsl/`, downloaded once for every burst that meets them (CR-079: `${ghsl_dir}`, filled from the worker's home; `ponzi-pipeline onboard --ghsl-cache` defaults to it too). No login.
