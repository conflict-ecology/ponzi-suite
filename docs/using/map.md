# Using the map

!!! warning "Under construction"
    ponzi-visual is still being built; this page and the map itself will change.

ponzi-visual is PONZI's web front end. It shows the administrative boundaries the server serves, lets you choose Major TOM tiles and watch them over a span of days, and shows on the map the tiles monitored now and those with outputs that nothing monitors. It makes areas of tiles and nothing else: the server chooses the standard that runs them and how often it looks (ponzi-core CR-068). What an area is and how the server runs it is in [Watched areas](watched-areas.md).

Every call goes through the server's API with your key. To run the front end, see [Install](../getting-started/install.md#ponzi-visual) and, for the whole system on one machine, [Quickstart](../getting-started/quickstart.md#development-setup).

## Connecting

The first page asks for an **API key**. **Connect** checks it against the server (`GET /v1/standards`) before keeping it, and shows the server's answer when it is refused. A key needs the scope `client:write` to make, pause or delete areas, `client:read` to look only ([Logins and keys](../getting-started/authentication.md#ponzi-server-keys)). Under `pixi run dev-up` the key to enter is `dev-browser.key`, printed when the system starts.

The key is kept in the browser tab's `sessionStorage` (`ponzi.key`): it lasts while the tab is open, and a new tab or a new browser session asks again. Where storage is blocked (a private window) it lives in the page's memory only. **Disconnect**, in the drawer, forgets it.

## The drawer

The pages are in a drawer at the left of every page:

- **Map** (`#/`): choose tiles and watch them, and the tiles monitored or with outputs (`#/monitored`, the old Monitored page, opens it too). An area's page counts as part of it.
- **Settings** (`#/settings`): the skin.
- **Disconnect**: forgets the key and goes back to the key form.

Collapsed, the drawer is a narrow strip with a **Menu** button; open, it lists the pages and marks the current one. Escape closes it. Its foot names the app's version, from the git tag it was built from ([Versions](../reference/versions.md)). Open or closed is kept in the browser for the next visit (`localStorage`, `ponzi.drawer`). On a phone's width the open drawer covers the page and closes once a page is chosen.

## Moving around the map

The map is a vector map with no base map of its own: what it draws comes from the server. Its controls are at its corners.

- **The legend.** The box at the bottom left, **Legend**, lists the projection, then under **Boundaries**, **Tiles** and **Bursts** one item per line: the overlays, the tile colours and the burst passes. Its title folds it into a small box and opens it again, as **How to choose tiles** does; open or folded is kept in the browser (`ponzi.legend`). Resting the pointer on an item says what it is.
- **Satellite.** The legend's **Satellite** draws Sentinel-2 cloudless imagery of 2016 under the map: EOxCloudless by EOX IT Services GmbH (contains modified Copernicus Sentinel data 2016), under CC BY 4.0, the one global edition free for any use with credit (2017 is free too but covers Europe and North Africa only; the editions from 2018 on are non-commercial). Its credit shows at the bottom of the map while it is drawn. Its tiles are Web Mercator, so it is drawn in the **Mercator** projection only (in the others the toggle says "(in Mercator only)"), and it shows through instead of the land's fill. It is about 10 m at its finest: closer in, the imagery is enlarged. The choice is kept in the browser (`ponzi.satellite`), shared with an area's page.
- **Projection.** The **Projection** menu offers Equal Earth (the default), Natural Earth, Robinson, Mollweide, Eckert IV, Mercator, a globe and the Arctic and Antarctic seen from above the pole. On the globe, a drag turns it instead of panning. The choice is kept in the browser (`ponzi.projection`).
- **Zoom.** The wheel, or the **+** and **−** buttons, zoom; the reset button (⤢) shows the whole map again. The zoom is shown beside them as ×N. The layers below are gated on it: Admin 1 from ×6, Admin 2 from ×16, the tiles from ×32.
- **Pan.** Drag with the right mouse button, anywhere (the browser's menu does not open over the map). Below ×32 a left drag pans too; from ×32 a left drag draws a box to choose tiles instead. The middle button always pans.
- **The note.** The line at the top of the map says what to do next: the zoom the tiles need, how many tiles are in view and selected, and how many bursts of each pass meet the selection. It also says when a layer could not be loaded, with the server's answer.
- **How to choose tiles**, a collapsed list on the map, repeats the gestures below.

The watched areas are drawn on the map as their tiles (an area made before tiles, as its bursts or its boundary). While no tiles are selected, a click on one opens its page.

### The land and the boundaries

The land is always drawn under everything, filled in the skin's land colour. It is the level 0 boundaries, from the same query as the Admin 0 overlay, so the land and the country outlines always match (ponzi-core CR-069).

Over it, three overlays show the World Bank Official Boundaries the server serves, each toggled on the map (with a swatch of its colour):

| Overlay | Drawn from | Drawn as |
| --- | --- | --- |
| **Admin 0** (countries) | any zoom; on at first | the thickest outlines, in the skin's coast colour |
| **Admin 1** | ×6 | red outlines, thinner |
| **Admin 2** | ×16 | the thinnest yellow outlines, over Admin 1, so a red edge shows on both sides of a yellow line along it |

An overlay's tooltip says from which zoom it is drawn. Each boundary is labelled with its name, at a point inside its largest part; a name is left out when the boundary is too small on screen for it or when it would overlap the name of a larger one. Level 0 includes the World Bank's areas of non-determined legal status (the NDLSA areas, such as Jammu and Kashmir, Western Sahara and Abyei, listed in [Data sources and catalogs](../method/data-sources.md#the-administrative-boundaries)): they are filled as land and outlined dashed. The toggles are kept in the browser (`ponzi.overlays`).

The boundaries are a view only. They take no hover and no click, and an area is never made from them (ponzi-core CR-067). Until the server has prepared them, the map draws only its graticule and the note says why ([Troubleshooting](../service/troubleshooting.md#the-boundaries-or-the-burst-catalog-are-being-prepared)).

## Choosing tiles

An area is made from Major TOM tiles, the 10 km cells of the grid the outputs are on ([Grids: processing and outputs](../method/grids.md)). The tiles are drawn from ×32, where a tile is about 7 pixels across, and only over land: the server lists no tile over open sea. They are drawn above the overlays and are the one layer that takes the pointer. Hovering a tile shows its id.

- **Drag a box** with the left mouse button: every tile it meets is added. Each box adds more to the selection.
- **Hold Shift** while dragging to remove the tiles the box meets.
- **Click** a tile to add it; click a selected tile to remove it. With Shift, a click only removes.
- **Past 64 tiles** the map warns, and adds them all: the note says "More than 64 tiles: a large area, with many bursts to fetch", and the panel warns too. The area is still made (CR-074). The bursts of more than 64 tiles are asked for 64 tiles at a time.
- **Clear**, in the panel, removes them all (so does **clear** beside the count above it).

A box adds only the tiles the map has loaded for the view, so wait for the note to stop saying "Loading tiles…" before drawing one. Selected tiles stay selected, and drawn, when you zoom out or pan away.

### Selecting by a boundary

**Select by**, at the top of the panel, chooses what a click on the map selects: **Tile** (at first: the tiles one by one or by a box, as above), or **Admin 1** or **Admin 2** (ponzi-core CR-076). A whole country (Admin 0) cannot be selected.

- With a level chosen, its boundaries are drawn from their zoom (×6, ×16) whatever the legend's toggle, which shows on and cannot be switched off. The note says "Click an Admin 1 boundary to add the tiles that meet it (Shift to remove)", or to zoom in first.
- **Click** a boundary: every tile over land that meets its outline is added (`GET /v1/boundaries/{level}/{code}/cells`, the outline at about 100 m). Hovering names it, with its country.
- **Shift-click** removes those tiles.
- A boundary meeting more than 5000 tiles is refused, and the note gives the server's reason: choose a lower level, or its parts one by one.
- A left drag pans; the tiles and the coloured tiles let the pointer through to the boundaries. Switch back to **Tile** to add or remove single tiles.

### The bursts of the tiles

The map draws the footprints of the bursts that meet the selected tiles (`GET /v1/majortom/bursts`), for the pass chosen under **Bursts**:

- **Ascending**: blue, with long dashes.
- **Descending**: magenta, dotted.
- **Both** (at first): the two together, kept apart by their lines.
- **Off**: none.

Each chip shows its line. This is a view only: an area always watches every burst of both passes, whatever is shown, and the footprints let the pointer through to the tiles. The note counts the bursts of each pass.

## Watch tiles

The panel beside the map makes the area.

- **The tiles.** How many are selected and the first six ids (with how many more), and **Clear**.
- **The bursts.** How many bursts meet them, on how many tracks and which passes, from `GET /v1/majortom/tracks`. Their scenes are fetched as soon as the area is made. When no burst of the server's catalog meets the tiles, the panel says so and **Watch** is off.
- **Tags.** Type one and press Enter or a comma; × removes one, and Backspace in the empty field removes the last. At most 20 tags of up to 40 characters; a tag given twice (in any case) is kept once. The tags go on the analysis outputs of these tiles, not on their downloads ([Tags](watched-areas.md#tags)).
- **First day** and **Last day.** The span to monitor, both empty at first, from 2014. A first day after the last is refused in the form ("The first day is after the last."). They are sent as `start_date` and `end_date`:
    - An empty first day leaves the start to the server (the standard's).
    - An empty last day leaves the end open: the area is watched until it is paused.
    - What was acquired in the span so far is processed at once, and each new acquisition as it arrives, to the last day. A span that has already ended is processed whole at once.

    A line under the dates says what the span chosen means.
- **Watch** (**Watch N tiles**) makes the area. No standard and no cadence are sent: the server chooses both ([Watched areas](watched-areas.md)). The area has no name to type; the server names it by its first tile, such as `393U_467R +3`. Once it is made, the panel says "… is monitored: its jobs are queued. Its tiles are green on the map.", and the selection is cleared. A refusal is shown with the server's reason, for example when the server cannot choose a standard ([Troubleshooting](../service/troubleshooting.md#no-standard-given-and-the-server-has-no-default)).

## Monitored tiles

The map colours the tiles the server holds something of (`GET /v1/majortom/states`, ponzi-core CR-075), at every zoom; their colours are in the **Legend**:

- **Monitored** (green): an active area holds the tile and is not past its last day. An area waiting for its first day counts.
- **Outputs, not monitored** (amber): analysis outputs meet the tile (its own, or a run, p-values or events of a burst meeting it) and no area monitors it: its areas are paused or past their last day, or were deleted. The server checks that no area monitors the tile before it says so.

A tile with neither is not coloured. Areas made before tiles (from bursts or a boundary) hold no tile: they are drawn by their outline instead.

With no tiles selected, a click on a coloured tile (or an older area's outline) opens it in the side panel, in place of the form; **Close** goes back to the form. While tiles are being chosen a click adds or removes a tile, coloured or not, and the colours fade. Above the panel, the count of areas watched and active, and **Refresh**, which reads the areas and the tiles again.

The panel names the tile, its state and how many analysis outputs meet it, then a card for each area holding it. A tile whose area was deleted has no card: **Select it to watch again** adds it to the selection. Each card shows:

- **Its name**, a link to its page, and whether it is **active** or **paused**.
- **Tiles**: how many and their ids (behind "show the ids" past eight). An area made before tiles is labelled as made from bursts or from a boundary, and lists its bursts.
- **Tags**, or none.
- **Span**: "Monitoring year 2025" for a whole year, else its first and last day, or "Monitored with no end".
- **Jobs**: how many are queued, running (leased jobs count as running), done and failed, from its latest 1000 (`GET /v1/jobs?area_id=`).
- **Last looked at**: when the server last made its jobs, in UTC, or "not yet".

And its actions:

- **Open its outputs** opens its page.
- **Pause** and **Resume** switch it off and on.
- **Look now** makes its jobs now, whatever its cadence.
- **Delete** asks once more (**Delete** *name* or **Keep it**) and deletes it.

## An area's page

An area's page (`#/areas/<id>`; **← Map** goes back) shows its name, its standard and cadence, and its bursts. Under **Cells** are the Major TOM cells its done jobs published, with the latest store of each cell and the day it reaches. The picked cell's events store is drawn on a map over OpenStreetMap tiles, or the same 2016 satellite imagery (**Map** and **Satellite**, top right of the map, with its credit in the corner), one date at a time: a date slider, play and pause, previous and next, and a legend (first event, later event, flagged, processed with no flag). The page opens at the last date.

- The store is the Item's `events` asset, fetched through the server with the key and read in the browser.
- The raster is drawn over the Item's lon/lat box. The cell's grid is in UTM, so this is close (within about a pixel for a 10 km cell) but not a reprojection.
- **Where this cell came from** shows the steps the cell's Item was made by: stage, Item, spec hash and inputs, and its sources outside PONZI ([Provenance (manifests)](manifests.md)).

An area whose jobs have not finished shows "No outputs yet"; **Look now**, in its panel on the map, makes its jobs again.

## Settings

**Settings** (`#/settings`) holds the **Skin**, the colourway of the whole page, applied at once:

- **Conflict ecology** (the default): light, or dark when the system is in dark mode.
- **Retro**: dark, with a cyan accent and monospaced type.
- **UN**: light, with one blue and Roboto.

A skin kept under its former name (Field, Board, Portal) opens as its new one.

The choice is kept in the browser (`localStorage`, `ponzi.skin`). **← Map** goes back.
