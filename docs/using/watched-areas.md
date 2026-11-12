# Watched areas

!!! warning "Under construction"
    Watched areas are still being built; this page and how areas are run will change.

A watched area is one or more Major TOM tiles (cells of the grid at 10 km, [Grids](../method/grids.md)) that keep being run under one standard. The outputs are made on the same grid, so the tiles of an area are the tiles of its outputs.

- **Tiles only.** An area is 1 or more tiles; past 64 the map and the server warn of a large area, and it is still made (CR-074). A tile must meet land, a level 0 outline of the administrative boundaries: a country or territory, or one of the disputed areas below. The server lists no tile over open sea and refuses one in an area.
- **Every burst.** The server watches every burst, of both passes, whose footprint meets the union of the tiles. There is no burst, pass or track to choose.
- **The standard is the server's.** An area may name its standard; one made without, as the front end makes them, takes the server's setting `default_standard`, else the one standard the server holds. A server holding several standards and no `default_standard` (or none, or a `default_standard` it does not hold) refuses such an area with a 422 that says to set it (ponzi-core CR-068). `cadence_hours` may be left out too: 24 hours.
- **At once.** Making an area makes its jobs, one `workflow` job per burst, so the scenes of its bursts are found and downloaded as soon as a worker claims them. After that the scheduler, every `scheduler_seconds` (default 300), makes each due area's jobs at its cadence.
- **Days.** A job's span starts on the area's `start_date` when it has one, and ends on the day of the tick or on the area's `end_date`, whichever is first. Before its first day an area makes no jobs.
- **Tags.** An area has free-text tags instead of a name to choose (its name defaults to its first tile and how many more, e.g. `393U_467R +3`). The server attaches them to the analysis outputs of its tiles as it serves them: see [Tags](#tags).

!!! note "Disputed areas"
    The World Bank's Admin 0 file leaves out the areas whose legal status the World Bank has not determined, the NDLSA areas: Jammu and Kashmir (the parts under India and under Pakistan), Aksai Chin and smaller areas along the India and China border, Arunachal Pradesh, Western Sahara, the Golan Heights, the Shebaa Farms, the UN buffer zone in Cyprus, Abyei, the Ilemi Triangle, the Falklands, South Georgia and the British Indian Ocean Territory (24 in all). The server reads level 0 from the World Bank's "Admin 0_all_layers" file, which holds them with the countries, and keeps them beside the countries, with `disputed` true and codes such as `NDLSA-WESTERN-SAHARA` and `NDLSA-JAMMU-AND-KASHMIR-IND` (ponzi-core CR-069). They count as land, so their tiles can be watched, and they belong to no country. Antarctica is in neither file and has no tiles.

```
ponzi-client area-create --cells 393U_467R,393U_468R --tags "flood 2024,coast" --start 2024-01-01 --end 2024-12-31
ponzi-client area-create --cells 393U_469R --standard s1-general@2.0.0 --cadence-hours 12   # a standard of its own
ponzi-client area-update AREA_ID --active false      # pause
ponzi-client area-update AREA_ID --tags "flood 2024" # change its tags
ponzi-client area-discover AREA_ID                   # look now, whatever the cadence
ponzi-client jobs --area AREA_ID                     # its jobs; a done job lists the Items it made
```

From Python:

```python
c.majortom_cells(bbox=[51.38, 35.68, 51.42, 35.72])      # the tiles over land of a box: Tehran's centre
c.majortom_bursts(["397U_465R", "397U_466R"])            # the bursts an area of them would watch, both passes
c.create_area(cells=["397U_465R", "397U_466R"], tags=["Tehran"], start_date="2025-01-01", end_date="2025-12-31")
```

A tile is named by its bottom-left corner. Until the boundaries are ready (the server builds them on its first start), the tile routes and making an area answer 503, as the boundary routes do.

What an area watches is fixed when it is made: change its days, tags, standard, cadence or whether it is active, or make another area for other tiles.

An area made before areas were made from tiles (from a list of bursts, or from an administrative boundary with an orbit pass and tracks) keeps loading and running as it was. A one-off run (`ponzi-client submit --bursts ...`, from Python or the command line only) is not an area, still takes burst ids and names its standard.

## On the map

ponzi-visual makes areas the same way, and makes nothing else: it submits tiles, tags and a span of days (`start_date` and `end_date`, both may be empty), and no standard and no cadence, so the server chooses what runs them. Its map colours the tiles monitored and those with outputs that nothing monitors; a click opens a tile's areas, to pause, resume, look now or delete them (CR-075). How to choose tiles, what the overlays and the burst footprints show, and the pages of the front end are in [The map](map.md).

## Tags

Outputs are content-addressed and shared between areas: one store may serve several areas. A tag is therefore never part of an Item, its content id or a worker's cache. The server adds it as it serves an Item (`GET /v1/stac/collections/{c}/items/{id}` and `GET /v1/stac/search`), as the property `ponzi:tags` ([STAC profile](stac-profile.md)).

- **Which Items.** Only the analysis outputs: runs, p-values, events and the events of a Major TOM cell. Never the downloads and inputs (scenes, orbits, DEMs, pairs, coherence, sidecars, masks, samples), nor models, calibrations and the registry.
- **Which tags.** The tags, once each, of every area whose bursts hold the Item's burst, or, for an Item of a cell, whose tiles hold that cell. Two areas sharing a tile both tag its outputs, and a change of an area's tags shows at once.
- **Search.** `c.search(tags=["flood 2024"])` (or `ponzi-client search --tags ...`, `?tags=` in the API) returns the analysis Items carrying any of the tags.

## What a daily look computes

Content ids decide. The worker plans the standard's workflow and runs only what is not in its cache.

- **Nothing new at ASF.** Discovery is named by what it found, not by the day it looked, so every job is cached and nothing runs.
- **A new acquisition.**
    - A new pairs Item.
    - Only the new pairs' coherence, at most one per baseline. A pair's id depends only on its two granules and the coherence spec, never on the rest of the series.
    - A new store, and exactly one new staged run. A monitoring update is a new run; it is never appended to an old one.
    - New events, new p-values and new cells.

`test_watched.py` in ponzi-service holds both cases.
