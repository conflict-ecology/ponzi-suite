# CR-053: watched areas chosen from administrative boundaries

- **Requested by / date:** owner, 2026-11-05 ("add these links for the admin boundaries when the server starts to select areas to monitor ... a drop down to select admin level 0-2 ... hover over the admin boundary, select it, enter a date range and orbit, then submit").
- **Status:** implemented on the owner's instruction (2026-11-05), awaiting review; uncommitted

## Why

A watched area was a list of burst ids picked one by one on the map. The places watched are administrative units (the Gaza Strip is the World Bank's Admin 1 `PSE001`), and an area watched over a span and in one orbit direction had no way to say so.

## What changes

**ponzi-spec (`ponzi_spec.api`).**
- New models:
  - `Boundary`: level 0 to 2, code, name, country, admin 1 name, ISO code, box, outline.
  - `BoundarySummary`.
  - `AreaBoundary`: level and code.
- `AreaCreate` gains `boundary`, `orbit_pass` (`ASCENDING` or `DESCENDING`), `start_date` and `end_date`.
  - An area is given either `burst_ids` or a `boundary`.
  - A boundary needs an `orbit_pass`.
  - The first day is not after the last.
- `AreaUpdate` gains the two dates. `Area` carries them all, and its `burst_ids` (required) are the bursts chosen.

**ponzi-server.**
- **Boundaries:** `ponzi_server.boundaries`.
  - The World Bank Official Boundaries (CC BY 4.0, dataset 0038272 version 3), admin 0, 1 and 2 as GeoParquet, pinned by sha256. The Admin 1 file is the one the Gaza test case's outline came from.
  - On the first start the server downloads them into `{home}/catalog/boundaries/` and builds `{home}/catalog/boundaries.sqlite3` in the background: 44,464 boundaries, each simplified to 0.001 degrees, with an R*Tree. Measured on this laptop: 28 s, 2 GB of memory, 271 MB.
  - Until the file is ready the boundary routes answer 503 with `Retry-After`. A failed download is reported and the rest of the API works.
  - Settings: `boundaries` (a built file), `fetch_boundaries`.
- **Routes:**
  - `GET /v1/boundaries?level=&bbox=&limit=&tolerance=`: by name, at most 2000.
  - `GET /v1/boundaries/{level}/{code}`.
  - `GET /v1/boundaries/summary`.
  - An outline is simplified to `tolerance` degrees (rounded up to a power of two, no finer than the stored one), and parts smaller than about two pixels are left out. Outlines are cached in memory once made. The whole world at level 0 at zoom 2 is about 200 kB.
- **Areas:**
  - `POST /v1/areas` with a boundary watches the catalog's bursts of the orbit pass whose footprints meet the stored outline (`bursts_in`).
  - A boundary meeting more than 5000 bursts, or none, is refused (422).
  - The scheduler's jobs take the area's `start_date` and end at today or its `end_date`, whichever is first. Before the first day no job is made; past the last day the payloads stop changing, so no new jobs are made.
- **Database:** `areas` gains `boundary`, `orbit_pass`, `start_date` and `end_date`. An older database gets them when the server starts (`db.add_missing_columns`, nullable columns only).
- **Dependencies:** `shapely` and `pyarrow` (both already in the service's environment).

**ponzi-client:** `boundaries`, `boundary` and `boundary_summary`.

**ponzi-worker.**
- The worker downloads nothing new: it gets burst ids in its jobs.
- `ponzi-worker demo` writes `fetch_boundaries: false`, and `--boundaries FILE` serves a built file.

**ponzi-visual.**
- The visual downloads nothing either: it reads the outlines from the server, at the map's scale.
- A drop-down chooses admin level 0, 1 or 2.
- The map draws that level's boundaries in view: countries at any zoom, level 1 from zoom 4, level 2 from zoom 6, and a full page asks to zoom in. Hovering highlights a boundary and names it; a click selects it.
- The Areas panel takes the first and last day and the orbit, and creates the area.
- An area made from a boundary is drawn as the boundary.

## Do results change?

No. Areas made from burst ids without dates make the jobs they made before.

## Tests

- ponzi-server: `test_server_boundaries.py`.
  - The boundaries are made on the first start from three small files through a fake opener, served by level and box, and 503 until then. A restart downloads nothing, and a failed download is reported.
  - An area from a boundary takes the bursts of its pass, and its jobs span its days. An area before its first day makes no job.
  - The refusals; the Python client; an older database migrated.
  - An autouse guard keeps every test from downloading the World Bank files.
- ponzi-visual: `src/test/boundaries.test.tsx`.
  - The query by level, box and tolerance; hover, click and the selected style; zoom-in notes.
  - The area made with its days and orbit; an area drawn as its boundary.
- ponzi-visual e2e: the demo's server, which migrated its existing database.
- A build from the real files was checked: Gaza is `PSE001`, beside North Sinai and Israel's Southern District.

## Version

- `ponzi-spec`: minor (new API models and fields).
- `ponzi-server`: minor (new routes, settings and dependencies).
- `ponzi-client`: minor.
- ponzi-visual: a new feature.
- Standard: none.
