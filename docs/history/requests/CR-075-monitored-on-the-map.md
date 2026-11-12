# CR-075: the monitored tiles on the map

- **Requested by / date:** owner, 2026-11-11 ("I want to switch monitored to be displayed on the map. tiles which are currently monitored should be one color, tiles with some information but not currentl monitored should be another"; asked which tiles and what of the page: "tiles with outputs but double check that its state is 'not monitored'", "Replace it with the map")
- **Status:** signed off (2026-11-11), implemented (2026-11-11)

## Why
The Monitored page lists areas, but not where they are or what the server holds there. Areas paused, past their last day or deleted leave outputs behind that nothing shows. The map is where tiles are chosen, so it is where what is watched, and what was, should be seen.

## What changes
- **`ponzi-spec`.** `TileState`: `cell_id`, `bbox`, `state` (`monitored` or `outputs`), `area_ids` (the areas whose tiles hold it, active or not) and `outputs` (the analysis Items meeting it).
- **ponzi-server.** `GET /v1/majortom/states[?bbox=]` (`client:read`): every tile over land that is `monitored`, an active area not past its last day holds it (an area before its first day counts), or that has `outputs`, analysis Items (`ponzi-run`, `ponzi-pvalues`, `ponzi-events`, `ponzi-events-cell`) of the tile or of a burst whose footprint meets it, and is not monitored. Monitored comes first: a tile is never both. A tile with neither is not listed. Areas made before tiles hold no tile and mark none. `openapi.json` is regenerated; `Client.majortom_states`.
- **ponzi-visual.** The map colours the tiles at every zoom: monitored green, outputs and not monitored amber, with a legend. With no tiles selected a click on one (or on an older area's outline) opens a side panel in place of the form: the tile's state and outputs, and the cards of its areas from the Monitored page (jobs, Pause, Resume, Look now, Delete, outputs). A tile whose area was deleted can be selected to watch again. The Monitored page and its drawer entry are removed; `#/monitored` opens the map.

## Do results change?
No.

## Tests
`ponzi-spec`: `TileState` takes the two states only. ponzi-server: monitored over outputs, paused, ended and deleted areas, a burst's outputs on the land tiles its footprint meets only, inputs not counted, the box. ponzi-visual: the colours, the legend, a click opening a tile with nothing selected and adding it while choosing, the panel's cards and actions, a deleted area's tile, `#/monitored`.

## Version
`ponzi-spec` minor. ponzi-server and ponzi-client minor (a new route). ponzi-visual minor.
