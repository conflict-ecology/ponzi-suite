# CR-038: the burst catalog, every Sentinel-1 burst for the server

- **Requested by / date:** owner, 2026-10-23 ("is there a way for visual to have all bursts available for selection?", then "build 1-3")
- **Status:** implemented on the owner's instruction (2026-10-23), awaiting review; uncommitted (plan decision D10)

## Why

The server's burst catalog was a JSON list held in memory, fine for a demo's five bursts but not for the 1.1 million bursts of Sentinel-1. A client selecting bursts needs all of them, queried by the box in view.

## What changes

| Where | Change |
| --- | --- |
| `ponzi_pipeline.catalog`, `ponzi-pipeline burst-catalog` | the catalog from the OPERA burst database (opera-adt/burst_db). Sources: the release GeoJSON (`burst-id-geometries-simple-<v>.geojson[.zip]`, streamed one feature per line) or the bbox SQLite (UTM boxes reprojected, edges densified). Output: `bursts` (id, track, subswath, orbit pass, land flag, box, GeoJSON footprint), an R*Tree on the boxes (two entries for a burst across the antimeridian), and `meta` (format, source, sha256, count, duplicates skipped, extent). Written through `.partial`. An exact duplicate is kept once; a burst with two different footprints is refused |
| `ponzi_spec.api` | `Burst.orbit_pass`, `Burst.geometry`; new `BurstSummary` (count, extent, source, `max_limit`, `bbox_required`) |

The server reads the catalog with `sqlite3` only (ponzi-service: `ponzi_server.catalog.SqliteBursts`). The layout is documented in the module text of `ponzi_pipeline.catalog`.

## Do results change?

No.

## Tests

- `packages/pipeline/tests/test_catalog.py`:
    - the release layout, zipped, with a repeated feature and an antimeridian burst;
    - two different footprints for one id are refused;
    - the bbox SQLite agrees with `BurstMap.bursts_in`.
- In ponzi-service, `test_server_bursts.py`: a catalog written here and read by the server.
- On the real burst_db 0.18.0:
    - 1,127,661 bursts in 20 to 30 s, a 371 MB file;
    - 140,955 repeated features kept once;
    - a city-sized view answers in 7 ms through the server.

## Version

- `ponzi-pipeline` 0.2.0 (not yet released).
- `ponzi-spec` 0.3.0 (not yet released).
