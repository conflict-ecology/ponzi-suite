# The clients

## Python: `ponzi_client.Client`

```python
from ponzi_client import Client

c = Client("https://ponzi.example.org", key)        # or Client.from_config() (server.url, server.key_env)
c.standards(); c.bursts(bbox=(51.2, 35.5, 51.6, 35.8))
unit = c.boundaries(level=1, bbox=(34.2, 31.2, 34.6, 31.6))[0]          # World Bank units, levels 0 to 2
area = c.create_area(name="Tehran", burst_ids=["t028_058198_iw3"], standard="s1-general@1.0.0")
gaza = c.create_area(name="Gaza", boundary={"level": 1, "code": unit.code}, orbit_pass="ASCENDING",
                     start_date="2023-01-01", standard="s1-general@1.0.0")
c.update_area(area.area_id, active=False); c.discover_area(area.area_id); c.jobs(area_id=area.area_id)
run = c.submit(burst_ids=["t028_058198_iw3"], standard="s1-general@1.0.0")
c.request(run.request_id).status                      # queued, running, done, failed
items = c.search(collections=["ponzi-events-cell"], bbox=(51.2, 35.5, 51.6, 35.8))
c.manifest(items[0].properties["ponzi:content_id"])
c.download(items[0], "events", "out/")               # a zipped store comes back unpacked
```

Every call takes and returns the `ponzi_spec.api` models. An error response raises `ApiError`, which carries the server's problem. The worker's own calls are `claim`, `heartbeat`, `upload`, `complete` and `fail`.

## The command line: `ponzi-client`

The commands are:

- `standards`, `bursts`, `burst`, `burst-summary`;
- `areas`, `area`, `area-create`, `area-update`, `area-delete`, `area-discover`;
- `submit`, `request`, `requests`, `jobs`;
- `search`, `item`, `manifest`, `download`.

They print JSON. The server and key come from `--url` and `$PONZI_KEY` (or `--key-env`, or the file `$PONZI_KEY_FILE`), or else from the deployment config. The boundaries are reached from Python and ponzi-visual only; the command has no boundary command yet.

## TypeScript (in ponzi-visual)

ponzi-visual carries its own client, `src/client`. It is not a separate package.

```ts
import { createPonziClient, contentId } from "./client";
const c = createPonziClient({ baseUrl: "https://ponzi.example.org", key });
const cells = await c.search({ collections: ["ponzi-events-cell"] });
const m = await c.manifest(contentId(cells[0]));
```

Its types are generated from ponzi-server's committed `openapi.json` with `pixi run gen` in ponzi-visual, and `pixi run check-gen` fails when they are stale.
