# Clients: Python, CLI, TypeScript

!!! warning "Under construction"
    ponzi-client is still being built; its calls and commands may change.

## Python: `ponzi_client.Client`

```python
from ponzi_client import Client

# or Client.from_env(): $PONZI_URL and $PONZI_KEY
c = Client("https://ponzi.example.org", key)
c.standards(); c.bursts(bbox=(51.2, 35.5, 51.6, 35.8))
# World Bank units, to draw: name, outline
unit = c.boundaries(level=1, bbox=(34.2, 31.2, 34.6, 31.6))[0]
# Major TOM tiles over land
tiles = [x.cell_id
         for x in c.majortom_cells(bbox=(51.38, 35.68, 51.42, 35.72))]
# what an area of them watches
c.majortom_bursts(tiles); c.majortom_tracks(tiles)
# a user key; an admin user decides
asked = c.request_watch(cells=tiles, tags="tehran", start_date="2023-01-01")
# yours (all of them for an admin user)
c.watch_requests()
# client:write
area = c.create_area(cells=tiles, tags=["tehran"], start_date="2023-01-01",
                     standard="s1-general")
c.update_area(area.area_id, active=False)
c.discover_area(area.area_id); c.jobs(area_id=area.area_id)
# what a tag covers: tiles, bursts, outputs, places
c.tags("teh"); c.tag("tehran")
# tracts: tiles sharing an edge, managed together (user-admin)
c.tracts(); c.pause_tract("393U_467R")
# the analysis Items of the areas tagged so
tagged = c.search(tags=["tehran"])
run = c.submit(burst_ids=["t028_058198_iw3"], standard="s1-general")
# queued, running, done, failed
c.request(run.request_id).status
items = c.search(collections=["ponzi-events-cell"],
                 bbox=(51.2, 35.5, 51.6, 35.8))
c.manifest(items[0].properties["ponzi:content_id"])
# a zipped store comes back unpacked
c.download(items[0], "events", "out/")
```

Every call takes and returns the `ponzi_spec.api` models. An error response raises `ApiError`, which carries the status and the server's problem (title, detail). `download` copies an asset when its href is a local path (shared storage), and otherwise fetches it through the server. The loop's calls are `claim`, `heartbeat`, `heartbeats`, `report`, `ticket`, `upload`, `complete` and `fail`, made by `ponzi-client serve` (`ponzi_client.serve`) with a `worker` key. `job`, `jobs(worker=...)` and `workers` follow the work (CR-097; the loops and where a job runs need the `operations` permission).

## The command line: `ponzi-client`

The commands are:

- `standards`, `bursts`, `burst`, `burst-summary`;
- `areas`, `area`, `area-create`, `area-update`, `area-delete`, `area-discover`;
- `watch-request`, `watch-requests` (a `user` key asks for tiles; CR-093);
- `tags`, `tag` (what a tag covers);
- `tracts`, `tract ID [--do pause|resume|discover|delete]` (tracts, CR-094);
- `submit`, `request`, `requests`, `jobs`;
- `search`, `item`, `manifest`, `download`;
- `job ID`, `jobs --worker ID`, `workers`: where a job stands, a loop's jobs, the loops and their last reports (CR-097; with `user-admin`, `client:write` or `admin`).
- `serve`, the client loop (with a `worker` key). `--worker-host HOST` runs its worker on that host over one ssh connection it keeps (`--ssh-prompt start|never`), and `--deliver direct|through-client` says who sends the outputs to the server (CR-098; [From another machine](../service/hpc.md#from-another-machine)). With a SLURM worker (`-- --executor slurm ...`) it sweeps every held job each `--step-seconds`, claims every queued job its worker can run unless `--max-jobs N` caps it, and kills a sweep past `--sweep-timeout` (default 600 s); see [Running on SLURM](../service/hpc.md#sweeps).

The commands but `serve` print JSON. The server is `--url`, else `$PONZI_URL`; the key `$PONZI_KEY` (or `--key-env`, or the file `$PONZI_KEY_FILE`). There is no config file (CR-088).

- `area-create --cells C[,C] [--standard S] [--tags T[,T]] [--name N] [--start D] [--end D]` makes an area of 1 or more Major TOM tiles (past 64 the server logs a warning); it watches every burst of both passes meeting them. There is no `--bursts`: an area is its tiles. Without `--standard` the server chooses it ([Watched areas](watched-areas.md)).
- `submit --bursts B[,B] --standard S` runs given bursts once; a run is not an area.
- `search --tags T[,T]` finds the analysis Items of the areas with those tags; `tags [TERMS]` lists the tags and what each covers, and `tag TAG` gives one tag's places and tiles.
- `watch-request --cells C[,C] [--tags T[,T]] [--start D] [--end D]` asks for tiles to be watched (a `user` key); an admin user approves or denies it in the app.
- A tag is one word of letters, digits, `-` and `_`; tags are given comma separated.
- The boundaries and the tile listings are reached from Python and ponzi-visual only.

## TypeScript (in ponzi-visual)

ponzi-visual carries its own client, `src/client`. It is not a separate package. The app uses it to log in, ask for areas, search tags and, for an admin user, decide requests and manage keys ([Using the map](map.md)); it makes no run requests (the client still has `submit`, which its end-to-end test uses). It sends no key: the app's own key is added by whatever serves the app, and a person's session travels in a cookie ([Logging in to the app](../getting-started/authentication.md#logging-in-to-the-app)).

```ts
import { createPonziClient, contentId } from "./client";
const c = createPonziClient({ baseUrl: "https://ponzi.example.org", key });
const cells = await c.search({ collections: ["ponzi-events-cell"] });
const m = await c.manifest(contentId(cells[0]));
```

Its types are generated from ponzi-server's committed `openapi.json` with `pixi run gen` in ponzi-visual, and `pixi run check-gen` fails when they are stale.
