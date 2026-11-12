# CR-060: when the bursts were and will be acquired

- **Requested by / date:** owner, 2026-11-05 ("temporal availability of the bursts"; chose "server asks ASF").
- **Status:** implemented on the owner's instruction (2026-11-05)
- **Superseded in part:** the boundary availability route and the visual's drawing of bursts by acquisition were removed (CR-067).

## Why

ponzi-visual's map is rebuilt to show, over a chosen administrative boundary, which bursts were acquired when and which will be acquired next. The server had no acquisition dates: only the worker asks ASF, and only for the bursts of a job.

## What changes

- **`ponzi_spec.api`:** `BurstAcquisition` (a time and its platform) and `BurstAvailability` (a burst, its track and pass, its acquisitions, its cadence in days, and the next acquisitions predicted).
- **`ponzi_server.availability`:** the server's only call out.
  - **The search:** read only and with no login, ASF's search API for `SLC-BURST`, VV, up to 40 bursts per request, the same search `ponzi_pipeline.discover` makes.
  - **The cache:** answers are kept per burst in `{home}/catalog/availability/<burst>.json`. A span is searched again when it reaches past what is kept, or when it reaches today and the copy is older than six hours.
  - **The prediction:** the cadence is the median gap between a burst's last eight acquisitions (12 days for one satellite, 6 for two). The next acquisitions are the last one plus whole cadences within the horizon. It forecasts the schedule; it is no promise.
- **Routes:**
  - `GET /v1/boundaries/{level}/{code}/availability?orbit_pass=&tracks=&start=&end=&horizon_days=` covers the bursts meeting a boundary, at most 400. The span defaults to the year to today, and the horizon to 30 days.
  - `GET /v1/bursts/{burst_id}/availability` covers one burst.
  - ASF out of reach is a 503.
- **ponzi-client:** `boundary_availability` and `burst_availability`.
- **ponzi-visual:** the main map, rebuilt on d3-geo, draws the bursts of a selected boundary by when they were and will be acquired (the visual's changelog).

## Do results change?

No.

## Tests

ponzi-server `test_server_availability.py`, against a fake ASF:
- a boundary's bursts with their acquisitions and cadences;
- the cache answers a second time, and the tracks filter works;
- one burst over a narrower span;
- the prediction;
- ASF out of reach;
- a stale cache and a wider span are searched again.

`local_server` refuses any real ASF call.

## Version

- `ponzi-spec`: minor.
- ponzi-server and ponzi-client: minor (new routes and calls).
