# CR-009: `ponzi.grid`, one way to put bursts, paths, points and outlines on a grid

- **Requested by / date:** owner, 2026-10-12
- **Status:** signed off 2026-10-12 and implemented, awaiting owner review

## Why
Every project rewrites the same geometry and gets slightly different answers. In the monorepo the lattice index formula is written inline 16 times, there are four lattice builders (Gaza, Gaza release, Tehran, the pipeline's mosaic), five variants of the rule for overlapping bursts, three routes from UNOSAT points to pixels, and two ways of counting a building. A changed overlap or snapping rule moves results, so these rules belong in one tested place under the change process. The module is useful by itself (owner): it holds mechanics only, no detection rule.

## Scope: what the module settles

| Part | Functions | The one rule it fixes |
| --- | --- | --- |
| Lattice | `Lattice(epsg, x0, y0, step, nx, ny)`; `Lattice.from_bounds`, `Lattice.from_polygon(geometry, buffer=0)`; `save` and `load` (one JSON form); `xy()` of pixel centres; `transform` (affine) | pixel EDGES sit on multiples of `step` in the projected system (centres at half a step), so two lattices of the same projection and step always align; the origin is the centre of the top-left pixel |
| Placement | `placement(lattice, x, y) -> Placement or None` (slices into the lattice and into the source); `aligned(lattice, x, y)` | a source grid on the lattice is placed by offset, never resampled; a source that is off the lattice by more than a tolerance is refused, not shifted |
| Reprojection | `reproject_to(lattice, array, src_epsg, src_x, src_y, method="nearest")` | the one way to bring a grid from another UTM zone or another step (NISAR at 20 m) onto a lattice; nearest by default so codes and flags stay codes and flags; behind the optional extra (needs pyproj) |
| Burst mosaic | `mosaic(lattice, bursts, *, reduce, nodata=None)` where each burst is (array, x, y) | overlapping bursts of ONE path combine by a named rule: `max`, `min`, `first`, `count`; there is no default (owner's answer 2), a call without `reduce` is an error |
| Path stack | `PathStack`: per path the mosaicked arrays with that path's own dates, plus `observed` (which paths have a valid value at each pixel) | paths are never put on a common time axis here; each keeps its dates |
| Points to pixels | `point_index(lattice, x, y)` (flat index, -1 outside); `points_in_pixels(lattice, lon, lat)` from geographic coordinates | point in pixel by floor on the pixel edges: a point on an edge belongs to the pixel to its right and below |
| Outlines to pixels | `outline_cells(lattice, geometries) -> (outline index, flat pixel index, intersection area)`; `cover(lattice, geometries)` (share of each pixel covered); `share_in(cells, mask)` (share of each outline lying in masked pixels) | exact outline-pixel intersection areas; the 50 % rule and the per-pixel cover both come from the same table |
| Tile grid | `TileGrid(epsg, step, tile_size)`: `tile_of`, `tile_id`, `parse_id`, `lattice(row, col)`, `tiles(lattice or bounds)` | plain square tiles with edges on multiples of `tile_size * step`; the tile size is a parameter (owner's answer 4) |
| Display index | `display_index(lattice, bounds, step=None)`: for a Web Mercator display raster the flat index of the lattice pixel under each display pixel centre | the one mapping pages use, so a page never resamples data |

## Not in scope
Confirmation across paths, events, episodes, status, tiles and any threshold: these are detection rules and go to `ponzi.products`, which will use this module. Admin boundaries, basemaps and page code stay in `ponzi-apps`.

## Sources in the monorepo
`ops/gaza_release/common.py` (`release_lattice`, `pad_lattice`, `display_grid`, `display_index`), `ops/side_analyses/unosat_audit/flagmap/build_combined.py`, `ops/tehran_summary/build.py` (`grid_geometry`, `placement`, `display_index`), `ops/gaza_release/building_footprints.py` (`building_cells`), `sweep/buildings_lattice.py` (cover), `packages/ponzi_pipeline/aggregate.py` (`_mosaic_one`, the grid from a polygon and the nearest warp).

## Dependencies and layering
numpy only for lattice, placement, mosaic, path stack and `point_index`. `shapely` for outlines and polygons, `pyproj` for geographic points, reprojection and the display index: an optional extra `grid`, imported inside the functions that need them. `ponzi.grid` imports nothing from the other subpackages; `ponzi.products` and `ponzi.evaluation` may import it.

## Do results change?
Nothing existing changes: no current code uses the module. When Gaza and Tehran move onto it, the checks are: the Gaza lattice from `Lattice.from_polygon` equals the stored release lattice; `placement` gives the offsets the release uses; `outline_cells` reproduces the stored building counts.

## Tests
Unit tests on small synthetic grids and shapes: snapping and alignment of two lattices; placement inside, partly outside and off the lattice; each mosaic rule on two overlapping arrays; a point on a pixel edge; a square outline with known intersection areas; cover of a pixel half covered; the display index on a tiny lattice; a round trip of `save` and `load`.

## Open points: the owner's answers (2026-10-12)
1. **Name:** `ponzi.grid`.
2. **Overlap rule:** no default. The caller names `max`, `min`, `first` or `count`; a call without one is an error (`reduce` is a keyword without a default, an unknown name is a ValueError).
3. **Tolerance for "on the lattice":** exact, 1e-6 of a step (`ponzi.grid.TOL`). A misaligned source is refused with a ValueError that says so and names `reproject_to`; nothing is shifted.
4. **Tile grid:** included here as pure geometry, `TileGrid`: tile size in pixels, tile edges at multiples of `tile_size * step`, an id from the EPSG code and the tile row and column, the `Lattice` of a tile, and the tiles a lattice or bounds touch. MGRS is not implemented; the scheme is not chosen, so the tile size stays a parameter.

## As implemented
`src/ponzi/grid/`: `lattice.py` (Lattice, placement, aligned, point_index, TileGrid; numpy only), `rasters.py` (mosaic, PathStack, reproject_to, display_index), `vectors.py` (points_in_pixels, outline_cells, cover, share_in); about 500 lines. `tests/test_grid.py`: 34 tests in under a second, all on synthetic numbers; two state the equality with the Tehran summary's `grid_geometry` and `placement` through a copy of those formulas, one the equality of the display index with Tehran's.

Rules that the table above leaves open and the code fixes:
- `Lattice.from_bounds` is the Tehran box rule: the first and last pixel CENTRES enclose the bounds (x0 the last centre at or below xmin, y0 the first centre at or above ymax), so the lattice covers the bounds with up to one pixel of margin on each side.
- `nodata` is NaN for floating arrays and must be named for any other dtype (255 for codes); there is no silent 0.
- Tile rows grow to the NORTH (row = floor(y / span), column = floor(x / span)), unlike pixel rows, so a tile index never depends on an area. The id is `<epsg>_r<row>_c<col>`; it does not carry the tile size.

Deviations from the draft:
- `Lattice.from_polygon(geometry, epsg, step, buffer=0, src_epsg=None)`: the projection and the step have to be given; `src_epsg` projects a geometry given in another system (lon, lat) first.
- `share_in(cells, mask, area)` takes the full area of every outline as a third argument. The 50 % rule of the release divides by the whole outline, not by the part on the lattice, and the table of cells alone does not hold that.
- `cover` is exact (areas of the outlines' union per pixel), where `buildings_lattice.py` approximated it by 3 m supersampling and rounded to whole percent. Values can differ from the stored `cover` layer by about a percent; a stored layer is not reproduced bit for bit.
- `display_index` uses the point-in-pixel rule (floor on the pixel edges) where Tehran and Gaza round to the nearest centre. The two differ only for a display centre exactly on a pixel edge. It returns the index as `(H, W)` with the display description (`W`, `H`, `res`, `bounds_3857`, `bounds_lonlat`, Tehran's keys); the Gaza pages' renumbering to mask order stays with the application.
- `reproject_to` also offers `bilinear` for floating arrays (nearest is the default); it takes regularly spaced source coordinates only.
- `PathStack.add_bursts(path, dates, bursts, *, reduce)` mosaics and adds in one call, next to `add(path, dates, array)`.
- Not ported: `pad_lattice` (a larger lattice of the same origin is `placement` of the smaller one's `xy()`), the pipeline's rasterio warp of burst stores (`_mosaic_one`: it reads stores and writes a mosaic store; here bursts on the lattice go on by `placement`, any other grid by `reproject_to`).
