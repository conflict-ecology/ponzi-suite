# Panels

A panel is the pinned, stratified, label-free set of pixels PONZI is trained and calibrated on. Its cells are split three ways:

| Split | Used for |
| --- | --- |
| `train` | fitting the forecaster |
| `val` | choosing the epoch, the breakdown tables |
| `test` | the null of a calibration: the trained model is run on these cells and their scores become the calibration |

A calibration therefore comes from cells the model never saw. A calibration names the panel it was made on.

## How a panel is made

| Step | What | Command |
| --- | --- | --- |
| spec | `data/panels/<id>-<version>.yaml`: cell source, classifiers, choice per stratum, split, window, coherence config, draw | (versioned data) |
| `panel-cells` | the candidate cells (Major TOM cells over the regions), one class per classifier, the cells chosen per stratum, their split | `ponzi-models panel-cells --spec S --out D` |
| bursts | the bursts covering the cells, through the S1 workflow (coherence store and sidecar each) | the worker |
| `panel-masks` | per cell and burst the processable pixels inside the cell; the quota per pixel stratum shared over the cell's bursts by area; a seeded draw; per burst a mask store with `cell_<split>` and `sample_<split>` layers | `ponzi-models panel-build ...` |
| `panel-assemble` | the panel folder: record, cells, catalogue, draw table, coverage, content id | (same command) |

Defaults (the old Major-TOM panel's rules): settlement and climate classes per cell; two pixel strata, `built` and `land_nonbuilt`, cut from the sidecar's built-up and land layers; 1,000 pixels per stratum per cell. `split.assign` pins cells to a split (held-out cells).

Classifiers are components: a spec names a `kind`, built in (`constant`, `raster_classes`) or registered by a package under the entry point group `ponzi.panel_classifiers`.

## How a panel is used

Everything reads a panel through `ponzi_models.panels.Panel`. A panel run is the production run on one mask layer (`--mask-store`, `--mask sample_test`), so training, calibration and production read the data the same way. A burst over cells of two splits serves both, each through its own layer.

## Identity

A panel's content id comes from its spec and the structural digests of every store it uses. Models and calibrations record the panel id and content id, so a model's manifest traces back to the cells and scenes behind it.
