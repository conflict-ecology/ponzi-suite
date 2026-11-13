# CR-100: the tiles are the only upload

- **Requested by / date:** owner, 2026-11-13 ("make the tile the only upload")
- **Status:** implemented on the owner's instruction (2026-11-13), awaiting review; uncommitted

## Why
A standard's jobs delivered two final Items per burst: `events` (`detect`, the burst's events on its own grid, `ponzi-events`) and `cells` (`tile`, the same burst's events on each Major TOM cell it reaches, `ponzi-events-cell`). The delivered output is on the Major TOM grid (overhaul plan D18, CR-030); the per-burst store was the final output before CR-030 added the tiles and was never removed. It doubled what each job zips and uploads, and gave two products for one pixel.

## What changes
- `ponzi_models.standards.workflow.FINAL` is `["cells"]`: `standard-workflow` writes `final: [cells]`, so the worker packages and the client uploads the `ponzi-events-cell` Items only.
- The `events` step stays in the workflow and still runs: its store stays in the worker's cache (`{cache}/ponzi-events/<content_id>/`) for checking a tile against its burst. The steps, the workflow hash (CR-091) and the standard's key (CR-089) are unchanged; a standard's server file must be written again (`ponzi-models standard-workflow`) for the server to deliver the tiles only.
- Items already uploaded to `ponzi-events` stay on the server; no new ones arrive.
- ponzi-visual draws an area's outline from its `ponzi-events` Items only when neither its tiles nor its bursts are known (`footprints.ts`); that fallback finds nothing for new jobs. Its test fixtures (a server snapshot) still show `final: [events, cells]` until made again.

## Do results change?
No. No store or number changes; only which Items a job delivers.

## Tests
`ponzi-models`: the standard workflow tests. `ponzi-service` worker: `test_standard.py` holds the printed finals to the server file's `final`.

## Version
`ponzi-models` minor. Standard: neither; its key does not change.
