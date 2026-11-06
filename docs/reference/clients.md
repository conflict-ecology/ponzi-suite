# The clients

## Python: `ponzi_client.Client`

```python
from ponzi_client import Client

c = Client("https://ponzi.example.org", key)        # or Client.from_config() (server.url, server.key_env)
c.standards(); c.bursts(bbox=(51.2, 35.5, 51.6, 35.8))
unit = c.boundaries(level=1, bbox=(34.2, 31.2, 34.6, 31.6))[0]          # World Bank units, to draw: name, outline
tiles = [x.cell_id for x in c.majortom_cells(bbox=(51.38, 35.68, 51.42, 35.72))]   # Major TOM tiles over land
c.majortom_bursts(tiles); c.majortom_tracks(tiles)                       # what an area of them watches
area = c.create_area(cells=tiles, tags=["Tehran"], start_date="2023-01-01", standard="s1-general@1.0.0")
c.update_area(area.area_id, active=False); c.discover_area(area.area_id); c.jobs(area_id=area.area_id)
tagged = c.search(tags=["Tehran"])                    # the analysis Items of the areas tagged so
run = c.submit(burst_ids=["t028_058198_iw3"], standard="s1-general@1.0.0")
c.request(run.request_id).status                      # queued, running, done, failed
items = c.search(collections=["ponzi-events-cell"], bbox=(51.2, 35.5, 51.6, 35.8))
c.manifest(items[0].properties["ponzi:content_id"])
c.download(items[0], "events", "out/")               # a zipped store comes back unpacked
```

Every call takes and returns the `ponzi_spec.api` models. An error response raises `ApiError`, which carries the server's problem. The loop's calls are `claim`, `heartbeat`, `upload`, `complete` and `fail`, made by `ponzi-client serve` (`ponzi_client.serve`) with a `worker` key.

## The command line: `ponzi-client`

The commands are:

- `standards`, `bursts`, `burst`, `burst-summary`;
- `areas`, `area`, `area-create`, `area-update`, `area-delete`, `area-discover`;
- `submit`, `request`, `requests`, `jobs`;
- `search`, `item`, `manifest`, `download`.

They print JSON. The server and key come from `--url` and `$PONZI_KEY` (or `--key-env`, or the file `$PONZI_KEY_FILE`), or else from the deployment config.

- `area-create --cells C[,C] [--standard S] [--tags T[,T]] [--name N] [--start D] [--end D]` makes an area of 1 to 64 Major TOM tiles; it watches every burst of both passes meeting them. There is no `--bursts`: an area is its tiles. Without `--standard` the server chooses it (its `default_standard`, else the one it holds).
- `submit --bursts B[,B]` runs given bursts once; a run is not an area.
- `search --tags T[,T]` finds the analysis Items of the areas with those tags.
- The boundaries and the tile listings are reached from Python and ponzi-visual only.

## TypeScript (in ponzi-visual)

ponzi-visual carries its own client, `src/client`. It is not a separate package. The app uses it to make areas of tiles over a monitoring year and to list and manage them; it sends no standard and no cadence, and makes no run requests (the client still has `submit`, which its end-to-end test uses).

```ts
import { createPonziClient, contentId } from "./client";
const c = createPonziClient({ baseUrl: "https://ponzi.example.org", key });
const cells = await c.search({ collections: ["ponzi-events-cell"] });
const m = await c.manifest(contentId(cells[0]));
```

Its types are generated from ponzi-server's committed `openapi.json` with `pixi run gen` in ponzi-visual, and `pixi run check-gen` fails when they are stale.
