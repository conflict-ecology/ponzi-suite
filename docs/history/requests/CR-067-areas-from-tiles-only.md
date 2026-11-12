# CR-067: watched areas from Major TOM tiles only

- **Requested by / date:** owner, 2026-11-05 ("Remove selection by admin level and only by major tom tile (this will make keeping track of data easier as that will be the format of the outputs)"; "Several tiles. limit adding 64 tiles at a time"; "the default to be click to add or remove OR click and hold and drag"; "Only tiles which overlap an admin0 vector should be included"; "Add the admin levels as toggles on the map to view, with labels added. The admins should not be selectable"; "Remove the play bar at the bottom. There should not be a burst selection"; "remove orbit as an option; both will be downloaded and monitored"; "instead of naming the area, add tags to those tiles which will be attached to all analysis for those tiles (not downloads)"; "add a toggle on the map that toggles viewing ascending or descending bursts"; "move the skin to a settings page").
- **Status:** implemented on the owner's instruction (2026-11-05)
- **Superseded in part:** the 64-tile limit is a warning (CR-074), and boundaries can be selected by (CR-076).

## Why

The delivered outputs are on the Major TOM grid at 10 km, so an area that is a set of tiles is an area whose outputs are exactly its tiles. Areas made from an administrative boundary or a hand-picked list of bursts did not line up with the outputs, and the choice of a pass, tracks and bursts made the same place watchable in many partial ways. One way to make an area keeps the data easy to follow: its tiles, every burst meeting them, both passes.

## What changes

- **`ponzi_spec.api`:**
  - `AreaCreate` is `cells` (1 to 64 distinct Major TOM cell ids on the grid, `MAX_AREA_CELLS`), `tags`, an optional `name`, `start_date`, `end_date`, `standard`, `cadence_hours` and `active`. It no longer takes `burst_ids`, `boundary`, `cell` (CR-066), `orbit_pass` or `tracks`: more than 64 cells, or any of those fields, is refused (422 at the server).
  - `tags`: free text, trimmed, repeats (ignoring case) dropped, at most 20 (`MAX_TAGS`) of at most 40 characters (`MAX_TAG_LENGTH`), no comma.
  - `name`: when none is given the server names the area by its first tile and how many more (`cells_name`, e.g. `393U_467R +3`).
  - `AreaUpdate` takes `name`, `tags`, the days, `standard`, `cadence_hours` and `active`, no longer `burst_ids`: what an area watches is fixed.
  - `Area` is its own model, no longer an `AreaCreate`. It holds `burst_ids`, `cells`, `tags` and, for an area made before, the `boundary`, `orbit_pass` and `tracks` it was made with.
  - `Boundary` gains `label`, a point inside its largest part where a map draws its name.
  - `PonziFields` gains `tags` and the extension schema `ponzi:tags`: assigned by the server as it serves an Item, never set by a stage, never part of a content id.
- **ponzi-server:**
  - **Land.** A tile is listed and watched only when its footprint meets a country, a level 0 outline of the boundaries the server holds.
    - Rows of the grid no country's box reaches are skipped, and of the others only the columns under a country's box are made.
    - The rtree finds the countries near the boxes, then each country's prepared outline is tested against all of them at once (`SqliteBoundaries.on_land`). The outlines and each cell's answer are kept in memory.
    - Until the boundaries are ready, the tile routes and making an area answer 503, as the boundary routes do.
  - **Routes**, each `client:read`:
    - `GET /v1/majortom/cells?bbox=` (or `?cells=` with up to 64 ids) lists cells over land only.
    - `GET /v1/majortom/cells/{id}` is a 404 for a cell over open sea.
    - `GET /v1/majortom/bursts?cells=` gives the bursts of both passes meeting a set of tiles, with their footprints.
    - `GET /v1/majortom/tracks?cells=` gives their tracks and passes with burst counts.
    - Removed: the single-cell `/tracks` and `/availability` (CR-066), and the boundaries' `/tracks` and `/availability` (CR-057, CR-060), which chose a boundary's bursts. `/v1/bursts/{id}/availability` stays.
  - **Areas.** `POST /v1/areas` checks every tile is over land, then takes every burst of the catalog, both passes, meeting the union of the tiles. No burst is a 422.
    - The area's jobs are made in the same call, so a worker claiming them downloads the scenes of those bursts at once (the workflow's discover and acquire steps), not at the scheduler's first tick.
    - The database gains `areas.cells` and `areas.tags` (`add_missing_columns`). The CR-066 column `areas.cell`, never released, is no longer read.
  - **Tags on Items** (`ponzi_server.tagging`).
    - **Which Items.** As the server serves an analysis Item (`ponzi-run`, `ponzi-pvalues`, `ponzi-events`, `ponzi-events-cell`), from `GET /v1/stac/collections/{c}/items/{id}` or `GET /v1/stac/search`, it adds `ponzi:tags`.
    - **Which tags.** Those of every area whose bursts hold the Item's burst, or, for a cell's Item, whose tiles hold that cell.
    - **Never tagged:** downloads and inputs (scenes, orbits, DEMs, pairs, coherence, sidecars, masks, samples) and the registry.
    - **Not stored.** The stored Item and its content id never change, so content-addressed outputs shared by several areas carry the tags of all of them.
    - **Search.** `GET /v1/stac/search?tags=` returns the analysis Items carrying any of the tags.
  - **Areas made before** (bursts, or a boundary with a pass and tracks) keep loading and running: the model and the database read their fields, and nothing migrates them. `ponzi_server.testing.LocalServer.add_area` writes such an area for tests and for `ponzi-worker demo`, whose synthetic bursts are on no land.
- **ponzi-client:**
  - The calls: `create_area(cells=..., tags=...)`, `majortom_cells(bbox | cells=...)`, `majortom_bursts`, `majortom_tracks` and `search(tags=...)`.
  - The command: `area-create --cells C[,C] [--tags T[,T]] [--name N] [--start D] [--end D]` (no `--bursts`), `area-update --tags`, `search --tags`.
  - Removed: `boundary_tracks`, `boundary_availability`, `majortom_cell_tracks` and `majortom_cell_availability`.
- **One-off runs are not areas.** `POST /v1/requests` (`submit`, `ponzi-client submit --bursts`) still takes burst ids, unchanged.
- **ponzi-visual:**
  - **Removed:**
    - the **Choose an area from** select;
    - **Pick bursts** and adding a burst by id;
    - the orbit select;
    - track ticking;
    - the time bar and the drawing of burst availability by day.
  - **Tiles.** They are the one selectable layer, from ×64, drawn above the overlays.
    - A click on a tile adds or removes it.
    - Pressing on a tile and dragging paints: the drag adds every tile it passes over when the first was unselected, and removes them when it was selected.
    - Panning is a drag where no tile is under the pointer or below ×64, Shift+drag, or the middle button. The wheel and + and - zoom.
    - The map adds no tile past 64 and says so.
    - The gestures are in the map's **How to choose tiles** help and its note.
  - **Overlays.** Three toggles on the map show the boundaries: Admin 0 countries (on at first), Admin 1 (from ×6) and Admin 2 (from ×16).
    - They are drawn as outlines with names, `pointer-events: none`: no hover, no click.
    - A name goes at the boundary's label point (else its centroid when inside it). It is left out when the boundary is too small on screen for it or when it would overlap a larger boundary's name.
  - **Bursts.** The footprints of the bursts meeting the selected tiles are drawn for the pass chosen on the map: Ascending (at first), Descending or Both. This is a view only, and the pointer passes through them. The note counts the bursts of each pass.
  - **Areas panel.** It lists the selected tiles and how many bursts and tracks they meet, and takes tags (a chip input) instead of a name, then the days, the standard and the cadence. **Watch** posts `cells` and `tags`.
  - **Other.** An area of tiles is drawn as its tiles. The Runs panel takes burst ids typed in. The skin moves to a settings page (`#/settings`, linked from the header).

## Do results change?

No. How a job runs and every content id are unchanged; tags exist only in what the server serves. An area of tiles watches more bursts than one area of a boundary on one pass would (both passes), by the owner's choice.

## Tests

- **ponzi-spec** `test_stages_api.py`:
  - an area of 1 to 64 tiles, and the refusals: 65 tiles, none, a repeat, a pass, tracks, bursts, a boundary, `cell`, ids off the grid, the days reversed;
  - tags trimmed and kept once, and their limits;
  - `ponzi:tags` read as a PONZI field without changing the content id;
  - areas made before still read. The import still loads no numpy.
- **ponzi-server** `test_server_cells.py`:
  - **Listing:** tiles over open sea not listed and a 404 one by one, the coast, `cells=`, a world-sized box, the land cache, and 503 on every tile route and on making an area without boundaries.
  - **Tiles of an area:** their bursts and tracks (the union meets more), an area of 1, 2 and 64 tiles of both passes, and the default name.
  - **On creation:** its jobs are made with it, and none for an area made off.
  - **Refusals:** 65 tiles, a sea tile, a pass, tracks, bursts, a boundary, `cell`, no burst.
  - **Old areas:** areas of bursts and of a boundary still listed, changed, discovered and ticked, and an older database.
- **ponzi-server** `test_server_tags.py`:
  - **Which Items:** analysis Items of a tagged area's burst and tile carry its tags; coherence, a sidecar and a tile of no area do not.
  - **Unchanged:** the content id and the stored Item are unchanged.
  - **Search:** by tag, ignoring case.
  - **Two areas** sharing a tile both tag its outputs, and a change of tags shows at once.
  - **An old area** tags nothing.
- **ponzi-server** `test_server_boundaries.py`:
  - boundaries served with label points inside their largest part;
  - the boundaries' track and availability routes gone, and an area from a boundary refused.
- **ponzi-client** `test_client.py`: the tile calls typed; an area from tiles with tags and its jobs; the command's `area-create --cells --tags`, `area-update --tags`, and no `--bursts`.
- **ponzi-worker** `test_watched.py`: unchanged, on an area of bursts written as one made before.
- **ponzi-visual:**
  - `majortom.test.tsx`: the zoom gate, a click toggling a tile, a drag painting in and out, Shift leaving the pointer to panning, the 64 limit and its message, the burst footprints by pass with the toggle and letting clicks through, Watch posting tiles and tags with no name, pass or tracks, an area drawn as its tiles;
  - `boundaries.test.tsx`: three toggles with Admin 0 on, the gates, names drawn and left out, nothing interactive;
  - `app.test.tsx`: no admin select, Pick bursts, orbit or skin on the map; the skin on the settings page;
  - `panels.test.tsx`: a one-off run of typed burst ids.
- **Browser:** checked in headless Chrome against a server on the real boundaries and burst catalog: click, drag-paint in and out, Shift and middle-button panning, the pass toggle, the overlay names, an area made with tags and its six jobs queued at once, the settings page.

## Version

- `ponzi-spec`: breaking for the API models (`AreaCreate` and `AreaUpdate` lose fields; `Area` gains fields; `Boundary` and `PonziFields` gain optional fields; the extension schema gains `ponzi:tags`). No store format or run config changes.
- ponzi-server and ponzi-client: breaking for the area API (routes removed and added, `POST /v1/areas` changed, new columns, which an older database gains on start).
- ponzi-visual: minor.
