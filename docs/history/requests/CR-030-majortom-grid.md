# CR-030: the Major TOM grid, and events delivered per cell

- **Requested by / date:** owner, 2026-10-23 (phase 5b of the overhaul plan; plan decision D18: bursts stay on their native grid, delivered outputs are on the Major TOM grid)
- **Status:** implemented on the owner's instruction (2026-10-23), awaiting review; uncommitted (plan decision D10)

## Why

Processing stays on each burst's native grid; what PONZI delivers, and the cells of its panels, are on one global grid of fixed cells, so outputs of different bursts, paths and dates line up and a cell never moves. The grid is ESA's Major TOM grid (open, Apache-2.0).

## What changes

**`ponzi.grid.majortom`** (numpy only at import):

- `MajorTomGrid(dist=10, latitude_range=(-85, 85))`: a numpy port of `MajorTOM/grid.py` of github.com/ESA-PhiLab/Major-TOM (read 2026-10-23), the same arithmetic step for step: rows over [-90, 90) at `ceil(pi R / dist)` latitudes, columns per row at `ceil(2 pi R cos(lat) / dist)` longitudes, cells named by their bottom-left corner (`433U_621R`), a point in the cell whose corner is the last strictly below it (the reference's `searchsorted - 1`), the footprint bounded by the next row and column (extrapolated at the edges), the UTM zone of the bottom-left corner with the Norway and Svalbard exceptions.
- `cell_id`, `cell_ids`, `parse`, `bounds`, `footprint`, `epsg`, `cells_in(bbox)`, `n_cells`, `utm_epsg`.
- `cell_lattice(cell, step)` (PONZI's own, needs pyproj): the `Lattice` over the cell's footprint in its UTM zone, edges on multiples of `step`.

**`detect_path(..., resample="nearest")`**: the bursts need not lie on the lattice; every lattice pixel reads each burst's code, Et and process flag at the source pixel holding its centre, in the burst's own projection (codes stay codes). The default places the bursts by offset, as before; `extra_attrs` join the store's attrs.

**`ponzi.products.tile`**: `cells_of(run_dirs, calibration)` (the cells a path's processed pixels reach), `detect_cell(run_dirs, calibration, cell, out, recipe, step=, dist_km=, overlap=)` (the path's events store on the cell's lattice, attrs `majortom_cell`, `majortom_dist_km`), `tile_path` (every such cell, `{out}/{cell}/events_{calibration}.zarr`), and the command `ponzi tile RUN_DIR... --calibration ID --out DIR [--step M] [--dist-km 10] [--recipe] [--overlap]`.

`ponzi-spec` 0.2.0: the Collection `ponzi-events-cell` (and `ponzi-panel-cells`, CR-031).

## Do results change?

No. `detect` and `detect_path` without `resample` are unchanged.

## Tests

`test_majortom.py` against golden values written by the reference implementation itself (`tests/data/majortom_10km_golden.json`, 2026-10-23: the row and cell counts, 1,893 rows and 5,094,350 cells at 10 km, and for 412 points over the globe and at the edge cases the cell id, footprint and UTM zone; all equal, footprints to 1e-9 degrees); parsing, covering a box, the cell lattice. `test_products_tile.py`: nearest resampling on an aligned lattice gives the store of the placement on the bytes; on a lattice in another UTM zone the events are the recipe applied to the library's `reproject_to` of the codes and Et; `tile_path` writes one store per cell reached; the command.

## Version

`ponzi`: MINOR, opt-in (part of the `0.3.0` release with CR-028 and CR-029). `ponzi-spec` 0.2.0. Standard: a standard names the output posting (`step`) and grid distance.
