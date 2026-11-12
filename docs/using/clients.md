# Clients: Python, CLI, TypeScript

!!! warning "Under construction"
    ponzi-client is still being built; its calls and commands may change.

## Python: `ponzi_client.Client`

```python
from ponzi_client import Client

c = Client("https://ponzi.example.org", key)        # or Client.from_env(): $PONZI_URL and $PONZI_KEY
c.standards(); c.bursts(bbox=(51.2, 35.5, 51.6, 35.8))
unit = c.boundaries(level=1, bbox=(34.2, 31.2, 34.6, 31.6))[0]          # World Bank units, to draw: name, outline
tiles = [x.cell_id for x in c.majortom_cells(bbox=(51.38, 35.68, 51.42, 35.72))]   # Major TOM tiles over land
c.majortom_bursts(tiles); c.majortom_tracks(tiles)                       # what an area of them watches
area = c.create_area(cells=tiles, tags=["Tehran"], start_date="2023-01-01", standard="s1-general")
c.update_area(area.area_id, active=False); c.discover_area(area.area_id); c.jobs(area_id=area.area_id)
tagged = c.search(tags=["Tehran"])                    # the analysis Items of the areas tagged so
run = c.submit(burst_ids=["t028_058198_iw3"], standard="s1-general")
c.request(run.request_id).status                      # queued, running, done, failed
items = c.search(collections=["ponzi-events-cell"], bbox=(51.2, 35.5, 51.6, 35.8))
c.manifest(items[0].properties["ponzi:content_id"])
c.download(items[0], "events", "out/")               # a zipped store comes back unpacked
```

Every call takes and returns the `ponzi_spec.api` models. An error response raises `ApiError`, which carries the status and the server's problem (title, detail). `download` copies an asset when its href is a local path (shared storage), and otherwise fetches it through the server. The loop's calls are `claim`, `heartbeat`, `upload`, `complete` and `fail`, made by `ponzi-client serve` (`ponzi_client.serve`) with a `worker` key.

## The command line: `ponzi-client`

The commands are:

- `standards`, `bursts`, `burst`, `burst-summary`;
- `areas`, `area`, `area-create`, `area-update`, `area-delete`, `area-discover`;
- `submit`, `request`, `requests`, `jobs`;
- `search`, `item`, `manifest`, `download`;
- `serve`, the client loop (with a `worker` key).

The commands but `serve` print JSON. The server is `--url`, else `$PONZI_URL`; the key `$PONZI_KEY` (or `--key-env`, or the file `$PONZI_KEY_FILE`). There is no config file (CR-088).

- `area-create --cells C[,C] [--standard S] [--tags T[,T]] [--name N] [--start D] [--end D]` makes an area of 1 or more Major TOM tiles (past 64 the server logs a warning); it watches every burst of both passes meeting them. There is no `--bursts`: an area is its tiles. Without `--standard` the server chooses it ([Watched areas](watched-areas.md)).
- `submit --bursts B[,B] --standard S` runs given bursts once; a run is not an area.
- `search --tags T[,T]` finds the analysis Items of the areas with those tags.
- The boundaries and the tile listings are reached from Python and ponzi-visual only.

## TypeScript (in ponzi-visual)

ponzi-visual carries its own client, `src/client`. It is not a separate package. The app uses it to make, list and manage areas ([Using the map](map.md)); it makes no run requests (the client still has `submit`, which its end-to-end test uses).

```ts
import { createPonziClient, contentId } from "./client";
const c = createPonziClient({ baseUrl: "https://ponzi.example.org", key });
const cells = await c.search({ collections: ["ponzi-events-cell"] });
const m = await c.manifest(contentId(cells[0]));
```

Its types are generated from ponzi-server's committed `openapi.json` with `pixi run gen` in ponzi-visual, and `pixi run check-gen` fails when they are stale.
