# Watched areas

!!! warning "Under construction"
    Watched areas are still being built; this page and how areas are run will change.

A watched area is one or more Major TOM tiles (cells of the grid at 10 km, [Grids: processing and outputs](../method/grids.md)) that keep being run under one standard. The outputs are made on the same grid, so the tiles of an area are the tiles of its outputs.

- **Who makes one.** In the app, a person asks for an area with a **watch request** (tiles, tags, a first and a last day), and an admin user approves it, which makes the area, or denies it with a reason (CR-093). From Python or the command line, a `user` key asks the same way (`watch-request`), and a `client:write` key makes an area directly (`area-create`).
- **Tracts.** The tiles of all the areas, grouped so that tiles sharing an edge are together, are **tracts** (CR-094): one piece of watched land, however many requests it was asked for in. Tiles meeting only at a corner are in separate tracts. An admin user manages a tract as a whole (pause, resume, look now, delete) on the app's **Tracts** page; a tract is computed from the areas whenever it is asked for, and is named by its first tile, south to north then west to east (`393U_467R +11`), so its name changes when tracts join or split. `GET /v1/tracts` lists them, and a pending watch request says which tracts it would join (`touches`).
- **Tiles only.** An area is 1 or more tiles; past 64 the map and the server warn of a large area, and it is still made (CR-074). A tile must meet land, a level 0 outline of the administrative boundaries: a country or territory, or one of the disputed areas below. The server lists no tile over open sea and refuses one in an area.
- **Every burst.** The server watches every burst, of both passes, whose footprint meets the union of the tiles. There is no burst, pass or track to choose.
- **The standard is the server's.** An area may name its standard; one made without, as the front end makes them, takes the server's setting `default_standard`, else the one standard the server holds. A server holding several standards and no `default_standard` (or none, or a `default_standard` it does not hold) refuses such an area with a 422 that says to set it (ponzi-core CR-068). `cadence_hours` may be left out too: 24 hours.
- **At once.** Making an area makes its jobs, one `workflow` job per burst, so the scenes of its bursts are found and downloaded as soon as a worker claims them. After that the scheduler, every `scheduler_seconds` (default 300), makes each due area's jobs at its cadence.
- **Days.** A job's span starts on the area's `start_date` when it has one, and ends on the day of the tick or on the area's `end_date`, whichever is first. Before its first day an area makes no jobs.
- **Tags.** An area has tags instead of a name to choose (its name defaults to its first tile and how many more, e.g. `393U_467R +3`). A tag is one word of letters, digits, `-` and `_`, at most 40 characters and 20 per area, given comma separated; a leading `#` and spaces are dropped, and a repeat in any case is kept once (CR-093). The server attaches them to the analysis outputs of its tiles as it serves them: see [Tags](#tags).

Land includes the World Bank's 24 disputed areas (non-determined legal status, such as Western Sahara and Jammu and Kashmir), so their tiles can be watched; they belong to no country. Antarctica has no tiles ([The administrative boundaries](../method/data-sources.md#the-administrative-boundaries)).

```
# a user key: an admin user decides
ponzi-client watch-request --cells 393U_467R,393U_468R \
    --tags flood-2024,coast --start 2024-01-01
# yours, and what was decided
ponzi-client watch-requests
# a client:write key
ponzi-client area-create --cells 393U_467R,393U_468R \
    --tags flood-2024,coast --start 2024-01-01 --end 2024-12-31
# a standard of its own (its id, or id@hash8)
ponzi-client area-create --cells 393U_469R --standard s1-general \
    --cadence-hours 12
# pause
ponzi-client area-update AREA_ID --active false
# change its tags
ponzi-client area-update AREA_ID --tags flood-2024
# look now, whatever the cadence
ponzi-client area-discover AREA_ID
# its jobs; a done job lists the Items it made
ponzi-client jobs --area AREA_ID
```

From Python:

```python
# the tiles over land of a box: Tehran's centre
c.majortom_cells(bbox=[51.38, 35.68, 51.42, 35.72])
# the bursts an area of them would watch, both passes
c.majortom_bursts(["397U_465R", "397U_466R"])
# a user key
c.request_watch(cells=["397U_465R", "397U_466R"], tags="tehran, flood-2025",
                start_date="2025-01-01")
# client:write
c.create_area(cells=["397U_465R", "397U_466R"], tags=["tehran"],
              start_date="2025-01-01", end_date="2025-12-31")
```

A tile is named by its bottom-left corner. Until the boundaries are ready (the server builds them on its first start), the tile routes and making an area answer 503, as the boundary routes do.

What an area watches is fixed when it is made: change its days, tags, standard, cadence or whether it is active, or make another area for other tiles.

An area made before areas were made from tiles (from a list of bursts, or from an administrative boundary with an orbit pass and tracks) keeps loading and running as it was. A one-off run (`ponzi-client submit --bursts ...`, from Python or the command line only) is not an area, still takes burst ids and names its standard.

## On the map

ponzi-visual asks for areas the same way, and nothing else: tiles, tags and a span of days, with no standard and no cadence; an admin user approves them on its **Admin** page. How to choose tiles, the monitored tiles (CR-075) and the pages of the front end are in [Using the map](map.md).

## Tags

Outputs are content-addressed and shared between areas: one store may serve several areas. A tag is therefore never part of an Item, its content id or a worker's cache. The server adds it as it serves an Item (`GET /v1/stac/collections/{c}/items/{id}` and `GET /v1/stac/search`), as the property `ponzi:tags` ([STAC catalog profile](stac-profile.md)).

- **Which Items.** Only the analysis outputs: runs, p-values, events and the events of a Major TOM cell. Never the downloads and inputs (scenes, orbits, DEMs, pairs, coherence, sidecars, masks, samples), nor models, calibrations and the registry.
- **Which tags.** The tags, once each, of every area whose bursts hold the Item's burst, or, for an Item of a cell, whose tiles hold that cell. Two areas sharing a tile both tag its outputs, and a change of an area's tags shows at once.
- **Search.** `c.search(tags=["flood-2024"])` (or `ponzi-client search --tags ...`, `?tags=` in the API) returns the analysis Items carrying any of the tags.
- **What a tag covers.** `c.tags("gaza")` (`ponzi-client tags gaza`, `GET /v1/tags?q=`) lists the matching tags with their areas, tiles, bursts, outputs and latest output; `c.tag("gaza")` (`ponzi-client tag gaza`, `GET /v1/tags/{tag}`) gives its places (the admin 0, 1 and 2 boundaries its tiles meet, each once) and one row per tile. The app's **Search** page shows the same ([Using the map](map.md)).

## What a daily look computes

Content ids decide. The worker plans the standard's workflow and runs only what is not in its cache.

- **Nothing new at ASF.** Discovery is named by what it found, not by the day it looked, so every job is cached and nothing runs.
- **A new acquisition.**
    - A new pairs Item.
    - Only the new pairs' coherence, at most one per baseline. A pair's id depends only on its two granules and the coherence spec, never on the rest of the series.
    - A new store, and exactly one new staged run. A monitoring update is a new run; it is never appended to an old one.
    - New events, new p-values and new cells.

`test_watched.py` in ponzi-service holds both cases.
