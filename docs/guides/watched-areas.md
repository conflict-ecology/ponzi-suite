# Watched areas

A watched area is one or more Major TOM tiles (cells of the grid at 10 km, [Grids](../concepts/grids.md)) that keep being run under one standard. The outputs are made on the same grid, so the tiles of an area are the tiles of its outputs.

- **Tiles only.** An area is 1 to 64 tiles. A tile must meet land (a country outline of the administrative boundaries): the server lists no tile over open sea and refuses one in an area.
- **Every burst.** The server watches every burst, of both passes, whose footprint meets the union of the tiles. There is no burst, pass or track to choose.
- **At once.** Making an area makes its jobs, one `workflow` job per burst, so the scenes of its bursts are found and downloaded as soon as a worker claims them. After that the scheduler, every `scheduler_seconds` (default 300), makes each due area's jobs at its cadence.
- **Days.** A job's span starts on the area's `start_date` when it has one, and ends on the day of the tick or on the area's `end_date`, whichever is first. Before its first day an area makes no jobs.
- **Tags.** An area has free-text tags instead of a name to choose (its name defaults to its first tile and how many more, e.g. `393U_467R +3`). The server attaches them to the analysis outputs of its tiles as it serves them: see [Tags](#tags).

```
ponzi-client area-create --cells 393U_467R,393U_468R --tags "flood 2024,coast" --start 2024-01-01 \
    --standard s1-general@1.0.0 --cadence-hours 24
ponzi-client area-update AREA_ID --active false      # pause
ponzi-client area-update AREA_ID --tags "flood 2024" # change its tags
ponzi-client area-discover AREA_ID                   # look now, whatever the cadence
ponzi-client jobs --area AREA_ID                     # its jobs; a done job lists the Items it made
```

From Python:

```python
c.majortom_cells(bbox=[51.38, 35.68, 51.42, 35.72])      # the tiles over land of a box: Tehran's centre
c.majortom_bursts(["397U_465R", "397U_466R"])            # the bursts an area of them would watch, both passes
c.create_area(cells=["397U_465R", "397U_466R"], tags=["Tehran"], standard="s1-general@1.0.0")
```

A tile is named by its bottom-left corner. Until the boundaries are ready (the server builds them on its first start), the tile routes and making an area answer 503, as the boundary routes do.

What an area watches is fixed when it is made: change its days, tags, standard, cadence or whether it is active, or make another area for other tiles.

An area made before areas were made from tiles (from a list of bursts, or from an administrative boundary with an orbit pass and tracks) keeps loading and running as it was. A one-off run (`ponzi-client submit --bursts ...`) is not an area and still takes burst ids.

## On the map

ponzi-visual makes areas the same way.

- **Tiles.** Zoom in to ×64 to see the tiles. A click on a tile adds it, or removes it when selected. Pressing on a tile and dragging paints: from an unselected tile the drag adds every tile it passes over, from a selected one it removes them. The map stops at 64 tiles and says so.
- **Panning.** Drag with the right mouse button, anywhere; a left drag where there is no tile (or anywhere below ×64) and the middle button pan too. The wheel and the + and - buttons zoom.
- **Looking.** The administrative boundaries are three overlays toggled on the map (Admin 0 countries, on at first; Admin 1 from ×6; Admin 2 from ×16), outlines with their names. The footprints of the bursts meeting the selected tiles are drawn for one pass at a time (Ascending, Descending or Both). Neither can be clicked, and neither decides what the area watches.
- **Watch.** Add tags, the first and last day, the standard and the cadence in the Areas panel, then **Watch**.

## Tags

Outputs are content-addressed and shared between areas: one store may serve several areas. A tag is therefore never part of an Item, its content id or a worker's cache. The server adds it as it serves an Item (`GET /v1/stac/collections/{c}/items/{id}` and `GET /v1/stac/search`), as the property `ponzi:tags` ([STAC profile](../concepts/stac-profile.md)).

- **Which Items.** Only the analysis outputs: runs, p-values, events and the events of a Major TOM cell. Never the downloads and inputs (scenes, orbits, DEMs, pairs, coherence, sidecars, masks, samples), nor models, calibrations and the registry.
- **Which tags.** The tags, once each, of every area whose bursts hold the Item's burst, or, for an Item of a cell, whose tiles hold that cell. Two areas sharing a tile both tag its outputs, and a change of an area's tags shows at once.
- **Search.** `c.search(tags=["flood 2024"])` (or `ponzi-client search --tags ...`, `?tags=` in the API) returns the analysis Items carrying any of the tags.

## What a daily look computes

Content ids decide. The worker plans the standard's workflow and runs only what is not in its cache.

- **Nothing new at ASF.** Discovery is named by what it found, not by the day it looked, so every job is cached and nothing runs.
- **A new acquisition.**
    - A new pairs Item.
    - Only the new pairs' coherence, at most one per baseline. A pair's id depends only on its two granules and the coherence config, never on the rest of the series.
    - A new store, and exactly one new staged run. A monitoring update is a new run; it is never appended to an old one.
    - New events, new p-values and new cells.

`test_watched.py` in ponzi-service holds both cases.
