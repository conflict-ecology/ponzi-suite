# CR-057: areas from a boundary on chosen tracks

- **Requested by / date:** owner, 2026-11-05 (approved a per-track choice for boundary areas).
- **Status:** implemented on the owner's instruction (2026-11-05)
- **Superseded in part:** tracks are no longer chosen for an area, and the boundaries' `/tracks` route is gone (CR-067).

## Why

An area made from a boundary (CR-053) watched every burst of its orbit pass that meets the boundary, on every track. A place is often covered by several tracks of one pass (Gaza's descending bursts come from more than one), and there was no way to watch only some of them.

## What changes

- **`ponzi_spec.api`:**
  - `AreaCreate.tracks`: relative orbits from 1 to 175, distinct, with a boundary only. None means every track of the pass. `Area` holds it.
  - `BoundaryTrack`: a track, its pass, and how many of its bursts meet the boundary.
- **ponzi-server:**
  - `GET /v1/boundaries/{level}/{code}/tracks?orbit_pass=`: the tracks whose bursts meet a boundary, with their counts (`boundaries.track_counts`).
  - `bursts_in(..., tracks=)` keeps only those tracks. No burst on the chosen tracks is a 422.
  - `areas.tracks`, a new nullable column, is added to an older database at start.
- **ponzi-client:** `boundary_tracks`.
- **ponzi-visual:**
  - the Areas panel lists the tracks of the chosen orbit with their burst counts, all ticked;
  - an area sends `tracks` only when some are unticked;
  - with none ticked there is nothing to watch, so Watch is disabled;
  - the list says which tracks an area watches.

## Do results change?

No. An area without `tracks` watches what it did before.

## Tests

- ponzi-server `test_server_boundaries.py`: the counts per track and pass, an area on one track, a track of the other pass, an empty or out-of-range list, tracks with `burst_ids`, an unknown boundary.
- ponzi-visual `boundaries.test.tsx`: the track list for the chosen orbit, and an area limited to the tracks left ticked.
- The service and visual suites.

## Version

- `ponzi-spec`: minor.
- ponzi-server: minor (a new route and field).
