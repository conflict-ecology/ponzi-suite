# Using PONZI (agents)

## The rule

Use PONZI only through `ponzi-client`: the Python package or its command line. Do not import `ponzi`, `ponzi_pipeline` or `ponzi_models`, do not read or write the server's storage or a worker's cache directly (both are in a PONZI home), and do not submit cluster jobs. Those are the worker's job, behind the server.

## What you can do

| Task | Client call (Python) | Command | Notes |
| --- | --- | --- | --- |
| Find bursts over an area | `c.bursts(bbox=...)` | `ponzi-client bursts --bbox ...` | burst ids look like `t028_058198_iw3` |
| See what can be run | `c.standards()` | `ponzi-client standards` | a standard id has a version: `s1-general@1.0.0` |
| Watch an area | `c.create_area(name=..., burst_ids=[...], standard=...)` | `ponzi-client area-create ...` | needs a `client:write` key |
| Watch an administrative unit | `c.boundaries(level=1, bbox=...)`, then `c.create_area(name=..., boundary={"level": 1, "code": ...}, orbit_pass="ASCENDING", standard=...)` | none: Python only | the server picks the bursts of that pass; `start_date` and `end_date` bound the span |
| Pause or change a watched area | `c.update_area(area_id, active=False)` | `ponzi-client area-update ID --active false` | fields left out stay as they are |
| Look at an area now | `c.discover_area(area_id)` | `ponzi-client area-discover ID` | whatever its cadence |
| Run once | `c.submit(burst_ids=[...], standard=...)` | `ponzi-client submit ...` | returns existing results when they exist (`reused: true`) |
| Follow a run | `c.request(request_id)`, `c.jobs(request_id=...)` | `ponzi-client request ID` | a done job lists the Items it made (`items`) |
| Find results | `c.search(collections=["ponzi-events-cell"], bbox=..., datetime=...)` | `ponzi-client search ...` | Items of the [STAC profile](../concepts/stac-profile.md) |
| Explain a result | `c.manifest(content_id)` | `ponzi-client manifest CID --yaml` | the provenance, see [Manifests](../concepts/manifests.md) |
| Fetch a result's file | `c.download(item, "events", "out/")` | `ponzi-client download COLLECTION ID events out/` | a zipped store comes back unpacked |

## Rules of thumb

- Identify results by content id, not by path; paths differ between installations.
- Before submitting, search: an identical request costs nothing the second time, but it is still a request.
- A run needs a standard; do not compose configs yourself.
- Report a failure with the job id and the `Problem` body the server returned.
