# CR-056: per-cell panel windows, and a panel built from its definition

- **Requested by / date:** owner, 2026-11-05 (approved the open item of CR-047).
- **Status:** implemented on the owner's instruction (2026-11-05)

## Why

The definition `majortom-global` (ponzi-suite `panels/majortom-global`) gives each cell its own window. The cells have eight windows and the bursts nine, since a burst's window spans its cells'. A builder spec (`PanelSpec`) had one `window`. So `panel-build` could not rebuild the panel as defined (CR-047, "Not yet"). It also had no way to read a definition at all: it took only the `cells.parquet` of `panel-cells`.

## What changes

**`PanelSpec.window`** is optional. It is the window of every cell without its own.

**The cells table** (`panels.cells`) may carry:
- `window_start` and `window_end` (ISO dates) per cell;
- `bursts` (burst ids joined by `;`): then the draw uses only those bursts for the cell.

`cell_windows(spec, cells)` gives each cell its own window, else the spec's. It refuses a cell with neither, a cell with only one of the two dates, and a window whose end is not after its start. `draw_panel` and `assemble_panel` call it first, so the draw refuses the table before it reads a store.

**`assemble_panel`:**
- each catalogue row (burst, split) gets the span of the windows of the cells it serves;
- when the cells carry their own windows, each burst record in panel.json gets `window_start` and `window_end`, the span of all its cells;
- when the cells carry their own windows, the content id also takes the digest of the cells (id, split, stratum, box, window, and bursts when named; `cells_digest`), as the input `external_id("cells", ...)`;
- a new keyword `definition` is recorded in panel.json as `definition` (the definition's key and file sha256).

A cells table without window columns gives the same files and the same content id as before. Every column and key is kept.

**`Panel`:**
- `window`: the spec's window when it has one, else the span of every catalogue window.
- `burst_window(burst, split=None)`: the window of the burst's cells of `split` (its catalogue row), or of all its cells.
- `burst_record` returns the burst's own window.

**`null-runs`** runs a burst over `burst_window(burst, split)`, not the panel's window. Training (`prepare`) and `export-pixels` read no window, so they do not change.

**`panels.definition`** (new):
- `cells_from_definition(definition, without_outline="refuse")` turns a definition (`ponzi_spec.panel.load_definition`) into the cells table: `cell_id`, the outline's lon/lat box (`left`, `bottom`, `right`, `top`), `epsg` (the UTM zone of the box's centre, a record only), `stratum`, `split`, `window_start`, `window_end`, `bursts`.
- `definition_record(definition)`: what the panel records of it.

**`panel-build --definition DIR`** takes the place of `--cells`, with `--without-outline refuse|drop`. It refuses:
- a spec whose `<id>@<version>` is not the definition's;
- a burst of the burst table that the definition does not name;
- a cell with no outline, unless `--without-outline drop`;
- a cell with no `stratum` property.

What a definition cannot give, and the build does not make up:
- **Boxes for cells without an outline.** `majortom-global` has 24. Their outline is the delivered tile, which is not a plain scaling of the grid cell, so the grid cell's box is not used. All 24 were never delivered: none of their 52 bursts has a coherence store, and none serves another cell. Leaving them out with `--without-outline drop` loses no pixel.
- **The draw parameters and the coherence config.** They come from the spec. No builder spec for `majortom-global` exists yet; one must be written (id `majortom-global`, version `0.4.0`, `draw`, `coherence`; no `window` needed). Its `cells`, `classifiers`, `selection` and `split` are not used.
- **The stores.** The burst table gives them, as for `--cells`. 396 of the 487 bursts have a store upstream.

A burst's window in the built panel spans the cells it serves there. That is the definition's burst window unless one of its cells is left out or draws no pixel in it.

## Do results change?

No. A spec with a window and a cells table without windows give the same panel: the same files, spec digest and content id (checked against the code before this change on the synthetic world). Panels built with per-cell windows are new. Null runs on them use each burst's own window.

## Tests

- ponzi-models `test_panel_windows.py`:
  - a single-window panel is unchanged: the spec digest, the catalogue windows, no window keys in the records, the content id without a cells input;
  - per-cell windows reach the catalogue rows, the burst records and `burst_window`;
  - without a spec window the panel's window spans its cells';
  - a cell without a window is refused, in the draw, the assembly and `cell_windows`;
  - `null_runs.run_burst` runs each burst over its own window;
  - a small definition written in the test (checked by `load_definition`) becomes the cells table; a cell with no outline or no stratum is refused;
  - `panel-build --definition` builds it, draws a cell only in its named bursts, records the definition, and refuses another spec version and an unknown burst.
- The models and core suites.

## Version

- `ponzi-models`: minor (an optional spec field, new columns, functions and a command option).
- A standard: none forced. Existing panels and their content ids do not change.
