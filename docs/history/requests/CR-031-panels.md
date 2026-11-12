# CR-031: panels as components, a builder from scratch

- **Requested by / date:** owner, 2026-10-23 (phase 5b of the overhaul plan; decisions D14, D17, D18, D19)
- **Status:** implemented on the owner's instruction (2026-10-23), awaiting review; uncommitted (plan decision D10)
- **Superseded in part:** panel spec files and artifact names follow the spec hash, not a version (CR-046, CR-052, CR-083).

## Why

A panel is the pinned, stratified, label-free set of pixels PONZI is trained and calibrated on: train and val cells for the fit, test cells for the null of a calibration. The old panels were Major-TOM packages built by the monorepo's `ponzi-paper` (C19), which does not exist any more (D14). The panel is rebuilt as a component of the system: defined by a versioned spec, made by replaceable stages, read through one reader, identified by a content id.

## What changes

New in `ponzi_models.panels`:

| Module | Holds |
| --- | --- |
| `spec` | `PanelSpec` (versioned data, `data/panels/<id>-<version>.yaml`): the cell source (the Major TOM grid over regions, or a list of ids), the cell classifiers, the choice per stratum, the split (fractions by stratum, `assign` pins cells), the window, the coherence config, the draw (quota per stratum and cell, the built and land thresholds, the seed) |
| `classify` | cell classifiers as components: built-in `constant` and `raster_classes` (a raster statistic over the cell, mapped to classes by value ranges), others by the entry point group `ponzi.panel_classifiers` |
| `cells` | stage `panel-cells`: candidates in id order, classes, strata, the choice and the split from their seeds; GeoParquet `cells.parquet` |
| `draw` | stage `panel-masks`: per cell and burst the processable pixels inside the cell, the pixel strata (`built`, `land_nonbuilt`) from the sidecar, the cell's quota per stratum shared over its bursts by processable pixels, the draw from `default_rng([seed, cell, burst, stratum])`; per burst one mask store (C23) with `cell_<split>` and `sample_<split>` layers; the draw table (every drawn pixel with its inclusion weight) and the coverage table |
| `panel` | stage `panel-assemble` (the panel folder: `panel.json` with the spec, the stores and their structural digests and the content id, the cells, the catalogue, the draw, the coverage) and `Panel`, the one reader: bursts per split in cell order, the stores, the window, the sample pixels and their strata, the cell strata of a window, `verify` |
| `build` | the commands `ponzi-models panel-cells` and `ponzi-models panel-build` |

What follows from it:

- A burst serves every split one of its cells has, through that split's layers, so a burst over cells of two splits is no longer lost ("mixed").
- The sample is a mask layer: a panel run is the production run with `--mask-store` and `--mask sample_<split>` (or `cell_<split>`).
- `null-runs` runs on the layer `{mask}_{split}` (default `sample_test`) into `{config}_mask-{layer}`; the sample-store route is gone. `null-rows` reads those runs, rows in the window's row-major order with the panel's strata (cell stratum code * 2 + pixel stratum).
- `prepare` reads `sample_train` and `sample_val` through the reader; the identity records the panel's id, content id, digest and split digest. `export-pixels` writes one sample store per burst and layer, the draw's `stratum_code` and `weight` from the draw table. Artifacts are named `<fit id>_<panel id>` and record the panel.
- Removed: `calibration/panel_files.py` (the reader of the Major-TOM layout) and `panels/masks.py` (the writer of its masks). The contract C19 is retired.

## Do results change?

No number of `ponzi` changes. Panels made by the old builder are not readable (clean slate, D6).

## Tests

`test_panel_build.py` (the spec, the cells and their determinism, GeoParquet, a raster classifier, the draw's rules and determinism, the masks against the draw, the reader, the content id against the spec and the inputs, a panel run through the production path). The tests of the null, the calibration, the export and the trainer run on panels made by the builder (`tests/panel_world.py`), their expectations read from the panel. `test_masks.py` (the old writer) is removed. `pixi run test-models`: all pass; `-e ml`: 111 passed.

## Version

`ponzi-models`: MINOR (0.2.0), within the 0.x series. Standard: the first standard's panel is built with this (phase 8b).
