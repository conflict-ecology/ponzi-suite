# CR-042: a job lists the Items it made

- **Requested by / date:** owner, 2026-11-04. In ponzi-visual, clicking a watched area's footprint opens a page with that area's output stores. Asked how the page should find them, the owner chose "Server records it": `Job.items`, listed through `GET /v1/jobs?area_id=`.
- **Status:** implemented on the owner's instruction (2026-11-04), awaiting review; uncommitted

## Why

A watched area's jobs carry `area_id`, and the server keeps the ids of the final Items each job made. It already uses them for `RunRecord.items`. `Job` didn't show them, so nothing could say which outputs belong to an area. Searching by the area's box would also pick up the outputs of another area, or of a one-off request, at the same place.

## What changes

`ponzi_spec.api.Job` gains `items: list[str]`: the ids of the final Items, empty until the job is done. A job read from an older server, without the field, reads as an empty list. ponzi-server fills it from the job row. `GET /v1/jobs?area_id=...&status=done` then gives every Item of an area.

## Do results change?

No.

## Tests

- ponzi-spec: `Job` without `items` reads as empty, and with it keeps the ids.
- ponzi-server: a done job lists its request's Items. `openapi.json` is regenerated.
- ponzi-visual: the generated client is regenerated, and the area page reads the field.

## Version

ponzi-spec: minor, in the same unreleased 0.4.0 as CR-041.
