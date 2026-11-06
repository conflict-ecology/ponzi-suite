# The map

!!! warning "Under construction"
    ponzi-visual is still being built; this page and the map itself will change.

ponzi-visual is PONZI's web front end. It shows the administrative boundaries the server serves, lets you choose Major TOM tiles and watch them over a span of days, and lists the areas watched now with their outputs. It makes areas of tiles and nothing else: the server chooses the standard that runs them and how often it looks (ponzi-core CR-068). What an area is and how the server runs it is in [Watched areas](watched-areas.md).

Every call goes through the server's API with your key. To run the front end, see [Install](../getting-started/install.md#ponzi-visual) and, for the whole system on one machine, [Quickstart](../getting-started/quickstart.md#development-on-your-own-home).

## Connecting

The first page asks for an **API key**. **Connect** checks it against the server (`GET /v1/standards`) before keeping it, and shows the server's answer when it is refused. A key needs the scope `client:write` to make, pause or delete areas, `client:read` to look only ([Authentication](../getting-started/authentication.md#ponzi-server-keys)). Under `pixi run dev-up` the key to enter is `dev-browser.key`, printed when the system starts.

The key is kept in the browser tab's `sessionStorage` (`ponzi.key`): it lasts while the tab is open, and a new tab or a new browser session asks again. Where storage is blocked (a private window) it lives in the page's memory only. **Disconnect**, in the drawer, forgets it.

## The drawer

The pages are in a drawer at the left of every page:

- **Map** (`#/`): choose tiles and watch them.
- **Monitored** (`#/monitored`): the areas watched now. An area's page counts as part of it.
- **Settings** (`#/settings`): the skin.
- **Disconnect**: forgets the key and goes back to the key form.

Collapsed, the drawer is a narrow strip with a **Menu** button; open, it lists the pages and marks the current one. Escape closes it. Open or closed is kept in the browser for the next visit (`localStorage`, `ponzi.drawer`). On a phone's width the open drawer covers the page and closes once a page is chosen.

## Moving around the map

The map is a vector map with no base map of its own: what it draws comes from the server. Its controls are at its corners.

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
| **Admin 0 countries** | any zoom; on at first | outlines in the skin's coast colour |
| **Admin 1** | ×6 | thick red outlines |
| **Admin 2** | ×16 | thin yellow outlines over Admin 1, so a red edge shows on both sides of a yellow line along it |

An overlay switched on below its zoom says "(from ×N)" beside its toggle. Each boundary is labelled with its name, at a point inside its largest part; a name is left out when the boundary is too small on screen for it or when it would overlap the name of a larger one. Level 0 includes the World Bank's areas of non-determined legal status (the NDLSA areas, such as Jammu and Kashmir, Western Sahara and Abyei, listed in [Watched areas](watched-areas.md)): they are filled as land and outlined dashed. The toggles are kept in the browser (`ponzi.overlays`).

The boundaries are a view only. They take no hover and no click, and an area is never made from them (ponzi-core CR-067). Until the server has prepared them, the map draws only its graticule and the note says why ([Troubleshooting](../service/troubleshooting.md#the-boundaries-or-the-burst-catalog-are-being-prepared)).

## Choosing tiles

An area is made from Major TOM tiles, the 10 km cells of the grid the outputs are on ([Grids](../method/grids.md)). The tiles are drawn from ×32, where a tile is about 7 pixels across, and only over land: the server lists no tile over open sea. They are drawn above the overlays and are the one layer that takes the pointer. Hovering a tile shows its id.

- **Drag a box** with the left mouse button: every tile it meets is added. Each box adds more to the selection.
- **Hold Shift** while dragging to remove the tiles the box meets.
- **Click** a tile to add it; click a selected tile to remove it. With Shift, a click only removes.
- **At most 64 tiles** make one area. A box that would pass 64 adds only what fits, and the note says "64 tiles is the most one area takes: remove one to add another".
- **Clear**, in the panel, removes them all (so does **clear** beside the count above it).

A box adds only the tiles the map has loaded for the view, so wait for the note to stop saying "Loading tiles…" before drawing one. Selected tiles stay selected, and drawn, when you zoom out or pan away.

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
- **Watch** (**Watch N tiles**) makes the area. No standard and no cadence are sent: the server chooses both ([Watched areas](watched-areas.md)). The area has no name to type; the server names it by its first tile, such as `393U_467R +3`. Once it is made, the panel says "… is monitored: its jobs are queued." with a link to Monitored, and the selection is cleared. A refusal is shown with the server's reason, for example when the server cannot choose a standard ([Troubleshooting](../service/troubleshooting.md#no-standard-given-and-the-server-has-no-default)).

## Monitored

The **Monitored** page (`#/monitored`) lists the areas watched now (`GET /v1/areas`), with how many are active, and **Refresh**. Each area shows:

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

An area's page (`#/areas/<id>`; **← Monitored** goes back) shows its name, its standard and cadence, and its bursts. Under **Cells** are the Major TOM cells its done jobs published, with the latest store of each cell and the day it reaches. The picked cell's events store is drawn on a map over OpenStreetMap tiles, one date at a time: a date slider, play and pause, previous and next, and a legend (first event, later event, flagged, processed with no flag). The page opens at the last date.

- The store is the Item's `events` asset, fetched through the server with the key and read in the browser.
- The raster is drawn over the Item's lon/lat box. The cell's grid is in UTM, so this is close (within about a pixel for a 10 km cell) but not a reprojection.
- **Where this cell came from** shows the steps the cell's Item was made by: stage, Item, config hash and inputs, and its sources outside PONZI ([Manifests](manifests.md)).

An area whose jobs have not finished shows "No outputs yet"; **Look now** on the Monitored page makes its jobs again.

## Settings

**Settings** (`#/settings`) holds the **Skin**, the colourway of the whole page, applied at once:

- **Field** (the default): light, or dark when the system is in dark mode.
- **Board**: dark, with a cyan accent and monospaced type.
- **Portal**: light, with one blue and Roboto.

The choice is kept in the browser (`localStorage`, `ponzi.skin`). **← Map** goes back.
