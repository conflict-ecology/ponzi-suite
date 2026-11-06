# CR-066: watched areas from Major TOM cells

- **Requested by / date:** owner, 2026-11-05 ("add in major tom tile capability"; chose "Major TOM tiles" beside Admin 0, 1 and 2 in the map's layer drop-down, the 10 km cells drawn when zoomed in, hover naming a cell, click selecting it, and Watch making an area of the bursts meeting that cell).
- **Status:** implemented on the owner's instruction (2026-11-05)

## Why

PONZI's delivered outputs and its panels are on the Major TOM grid at 10 km, but a watched area could only be given as bursts or as an administrative boundary (CR-053). Choosing the cell itself is the natural unit: the bursts that meet it are the ones whose outputs make that cell.

## What changes

- **`ponzi_spec.majortom`:** the Major TOM grid in plain Python, with `math` and `bisect` only, because ponzi-server imports ponzi-spec and never numpy.
  - It is `ponzi.grid.majortom.MajorTomGrid`'s arithmetic step for step: rows, columns, `cell_id`, `parse`, `bounds`, `footprint`, `epsg`, `cells_in` and `iter_cells`, a walk that makes a row's longitudes only when it reaches them, so a page of a large box is cheap.
  - The numpy grid stays as it is (its `cell_lattice` needs numpy).
- **`ponzi_spec.api`:**
  - `MajorTomCell`: a cell id, its box, its footprint and its UTM zone.
  - `AreaCreate.cell`: a cell id with an `orbit_pass`, optionally with `tracks`. An area gives exactly one of `burst_ids`, `boundary` and `cell`. An id that is not on the grid is refused when the model is made. `Area` keeps the `cell` it was made from, as it keeps a boundary.
- **ponzi-server:**
  - **Routes**, each `client:read` (`x-ponzi-scope`):
    - `GET /v1/majortom/cells?bbox=&limit=&offset=` gives the cells meeting a box, south to north and west to east, with their footprints. A page holds at most 5000 (default 2000), and a full page means there may be more, asked for with the next `offset`, as `GET /v1/boundaries` does.
    - `GET /v1/majortom/cells/{cell_id}`, `/tracks?orbit_pass=` and `/availability?orbit_pass=&tracks=&start=&end=&horizon_days=` answer as the boundary routes do (CR-057, CR-060). An id that is not on the grid is a 404.
  - **Areas:** `POST /v1/areas` with `cell` chooses the bursts of the pass meeting the cell's footprint with the burst catalog, as for a boundary (`boundaries.bursts_meeting`, now told what it is choosing for). No burst is a 422. The database gains `areas.cell` (`add_missing_columns`).
  - **No data:** the grid is computed (`ponzi_server.cells`), so nothing is downloaded and the routes answer from the first start.
- **ponzi-client:** `majortom_cells`, `majortom_cell`, `majortom_cell_tracks` and `majortom_cell_availability`, and `create_area(cell=...)`.
- **ponzi-visual:**
  - **The menu:** **Major TOM tiles (10 km)** is added to **Choose an area from…**, beside the admin levels.
  - **The zoom gate:** the cells of the view are fetched from the server and drawn from the map's ×64. There a cell is about 15 pixels across and a view holds about two thousand cells. At admin 2's ×16 a cell would be 4 pixels and a view would hold thirty thousand.
  - **Choosing a cell:** hover names a cell by its id, and click selects and frames it. Its bursts and their availability show as a boundary's do, and **Watch** posts the `cell`. An area made from a cell is drawn as the cell.
  - **Reuse:** the boundary layer draws both. A boundary and a cell are each a `Choice`.

## Do results change?

No. The cells are the grid's; how a job runs is unchanged.

## Tests

- **ponzi-core** `test_majortom_spec.py`: the plain and the numpy grid agree on every row's latitude and every fifth row's longitudes and names, on 3000 random points, the 412 golden points and points exactly on corners (ids, bounds, footprints, zones, parse), on 154 boxes, and on refusing ids off the grid.
- **ponzi-spec** `test_stages_api.py`: an area from a cell, and the refusals: no pass, with bursts, with a boundary, an id off the grid, not an id. The import still loads no numpy.
- **ponzi-server** `test_server_cells.py`:
  - the cells of a box and their pages, one cell, and a world-sized box answered one page at a time;
  - the refusals: a bad box, no box, over the cap, an id off the grid, no key;
  - a cell's tracks, and areas from a cell of each pass and on chosen tracks, with their jobs;
  - the refusals of such an area: a bad id, both a cell and a boundary, both a cell and bursts, no pass, no burst;
  - a cell's availability, and an older database getting `areas.cell`.
- **ponzi-client** `test_client.py`: the cell calls, typed, and an area from a cell.
- **ponzi-visual** `majortom.test.tsx`:
  - the layer and its zoom gate (pixels per cell at ×64 and ×16);
  - the cells of the view asked with its box, hover, click, the selected cell framed with its bursts asked for;
  - Watch posting the cell with its days, orbit and ticked tracks;
  - an area drawn as its cell;
  - the app's menu.

## Version

- `ponzi-spec`: minor (new module and models; `AreaCreate` gains `cell`).
- ponzi-server and ponzi-client: minor (new routes and calls, a new column).
- ponzi-visual: minor.
