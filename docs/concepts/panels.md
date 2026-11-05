# Panels

A panel is the pinned, stratified, label-free set of pixels PONZI is trained and calibrated on. Its cells are split three ways:

| Split | Used for |
| --- | --- |
| `train` | fitting the forecaster |
| `val` | choosing the epoch, the breakdown tables |
| `test` | the null of a calibration: the model is run on these cells and their scores become the calibration |

A calibration therefore comes from cells the model never saw. A calibration names the panel it was made on.

## The definition

A panel is defined by a folder kept in git in ponzi-suite, `panels/<id>/` (`panels/majortom-global`), of exactly three files (`ponzi_spec.panel`):

| File | Holds |
| --- | --- |
| `panel.yaml` | the id, the version (MAJOR.MINOR.PATCH), a description, the split counts, the provenance, and the sha256 of the two files below |
| `bursts.geojson` | one feature per burst: its footprint, track, subswath, orbit pass, split, cells and window |
| `cells.geojson` | one feature per cell: its outline, split, sub-panel, stratum, window and bursts |

A panel is cited as `<id>@<version>` (`majortom-global@0.4.0`, [Naming](../reference/naming.md)). `ponzi-models panel-check DIR` holds a folder to the rules: named by its id, the three files matching their sha256, the cells and bursts naming each other, the split counts those of the files. The definition holds no computed data: what is built from it goes into the PONZI home.

## How a panel is built

| Step | What | Command |
| --- | --- | --- |
| spec | the builder's spec: cell source, classifiers, choice per stratum, split, default window, coherence config, draw | (versioned data, with the panel's definition) |
| `panel-cells` | the candidate cells (Major TOM cells over the regions), one class per classifier, the cells chosen per stratum, their split | `ponzi-models panel-cells --spec S --out D` |
| bursts | the bursts covering the cells, through the S1 workflow (coherence store and sidecar each) | the worker |
| `panel-masks` | per cell and burst the processable pixels inside the cell; the quota per pixel stratum shared over the cell's bursts by area; a seeded draw; per burst a mask store with `cell_<split>` and `sample_<split>` layers | `ponzi-models panel-build --spec S --cells C --bursts B` |
| `panel-assemble` | the built panel: record, cells, catalogue, draw table, coverage, content id; by default in `$PONZI_HOME/panels/<id>@<version>` | (same command) |

Each cell has a window: its own (`window_start`, `window_end` in the cells table) or the spec's. A catalogue row's window spans those of the cells it serves, and a burst's spans those of all its cells. A null run uses the burst's window for its split.

`panel-build --definition DIR` builds a panel from its definition (ponzi-core CR-056). The definition gives the cells, their splits, strata, windows and bursts; a cell is drawn only in the bursts it names. The spec still gives the draw and must have the definition's id and version. What the definition does not give is not made up:

- A cell with no outline has no box to draw in. The build refuses it unless `--without-outline drop` leaves it out. In `majortom-global` these are the 24 cells that were never delivered; none of their bursts has a coherence store or serves another cell.
- The draw parameters and the coherence config come from the spec. No spec for `majortom-global` exists yet.
- The stores come from the burst table, as for `--cells`.

Defaults (the old Major-TOM panel's rules): settlement and climate classes per cell; two pixel strata, `built` and `land_nonbuilt`, cut from the sidecar's built-up and land layers; 1,000 pixels per stratum per cell. `split.assign` pins cells to a split (held-out cells).

Classifiers are components: a spec names a `kind`, built in (`constant`, `raster_classes`) or registered by a package under the entry point group `ponzi.panel_classifiers`.

## How a panel is used

Everything reads a built panel through `ponzi_models.panels.panel.Panel`. A panel run is the production run on one mask layer (`--mask-store`, `--mask sample_test`), so training, calibration and production read the data the same way. A burst over cells of two splits serves both, each through its own layer.

## Identity

A panel's content id comes from its spec and the structural digests of every store it uses. When the cells carry their own windows, it also takes the digest of the cells and their windows. Models and calibrations record the panel id and content id, so a model's manifest traces back to the cells and scenes behind it.
