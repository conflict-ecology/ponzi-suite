# CR-027: STAC Items for the stores

- **Requested by / date:** owner, 2026-10-23 (phase 2 of the overhaul plan, section 3)
- **Status:** implemented on the owner's instruction (2026-10-23), awaiting review; uncommitted (plan decision D10)

## Why

Every artifact that crosses a component boundary is to be a STAC Item of the profile (`ponzi-spec`, CR-024). The stores know their burst, grid, projection and time span; the stages that write them will describe them with this module.

## What changes

A new subpackage `ponzi.stac`, on nothing else of `ponzi`, needing `ponzi-spec` (the new extra `stac`; pyproj from the extra `grid`, imported inside the function that uses it):

- `describe_store(path)`: burst id and EPSG from the attrs, the pixel-edge bounds from `x` and `y`, the footprint in WGS84 (each edge densified before reprojection) and the time span from `time`.
- `store_item(collection, item_dir, fields, assets, ...)`: an Item of a profile Collection for files under `item_dir`, assets checked against the Collection's roles (unknown or missing required ones refused), hrefs relative to `item_dir`, the projection extension (`proj:code`, `proj:bbox`, `proj:shape`), the caller's `PonziFields` and lineage.
- `run_item(run_dir, fields, inputs=...)` (the stores the run wrote) and `coherence_item(store, fields)` (the store and its engine report, required).
- `write_item(item, path)`.

The identity (content id, stage) is the caller's: it depends on the input Items, which only the caller knows. The run does not write Items by itself; the stages of the worker (phase 6) will.

`ponzi-spec` is not on PyPI, so it is an extra and not a dependency: `pip install ponzi` from git still works without it.

## Do results change?

No. No store is written to; the Items are separate files (tested: the stores' bytes are unchanged after an Item is written beside them).

## Tests

`test_stac_items.py`: the extent of a synthetic store, coherence and run Items validating against the PONZI extension schema with their lineage, the stores untouched, a coherence store without an engine report refused. The layering test knows the new subpackage. A run Item also passed stac-validator against the STAC core and projection schemas (checked by hand; needs the network).

## Version

`ponzi`: MINOR, opt-in. Standard: not affected.
