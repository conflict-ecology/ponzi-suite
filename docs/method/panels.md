# Panels

A panel is the pinned, stratified, label-free set of pixels PONZI is trained and calibrated on. Its cells are split three ways:

| Split | Used for |
| --- | --- |
| `train` | fitting the forecaster |
| `val` | choosing the epoch, the breakdown tables |
| `test` | the null of a calibration: the model is run on these cells and their scores become the calibration |

A calibration therefore comes from cells the model never saw. A calibration names the panel spec it was made on.

## The panel spec

A panel is defined by its panel spec: a folder kept in git in ponzi-suite, `panel_specs/<id>/` (`panel_specs/majortom-global`), or a working copy in `$PONZI_HOME/panel_specs/<id>/`, of exactly three files (`ponzi_spec.panel`):

| File | Holds |
| --- | --- |
| `panel.yaml` | the id, a description, the split counts, the build settings (`draw`, the `coherence` spec's name, optionally a default `window` and how `panel-cells` chose the cells), the provenance, and the sha256 of the two files below; no version |
| `bursts.geojson` | one feature per burst: its footprint, track, subswath, orbit pass, split, cells and window |
| `cells.geojson` | one feature per cell: its outline, split, sub-panel, stratum, window and bursts |

A panel is cited by its id (`majortom-global`, [Naming](../models/naming.md)) and pinned by its spec hash, over `panel.yaml` with the code's defaults filled in and the two geojson files ([Specs: a name and a hash](../models/versions.md#specs-a-name-and-a-hash)). A changed panel (other cells, another draw) is a new panel spec under a new name. `ponzi-models panel-check SPEC` (a name or a folder) holds a folder to the rules: named by its id, the three files matching their sha256, no `version`, the cells and bursts naming each other, the split counts those of the files. The panel spec holds no computed data: what is built from it goes into the PONZI home.

## How a panel is built

| Step | What | Command |
| --- | --- | --- |
| spec | `panel.yaml`: cell source, classifiers, choice per stratum, split, default window, coherence spec, draw | the panel spec's folder |
| `panel-cells` | the candidate cells (Major TOM cells over the regions), one class per classifier, the cells chosen per stratum, their split, and the bursts that cover them, written into the panel spec's folder (`cells.geojson`, `bursts.geojson`, the counts and sha256 in `panel.yaml`) | `ponzi-models panel-cells --panel-spec SPEC --burst-map FILE [--out DIR]` |
| bursts | the bursts covering the cells, through the S1 workflow (coherence store and sidecar each) | the worker |
| `panel-masks` | per cell and burst the processable pixels inside the cell; the quota per pixel stratum shared over the cell's bursts by area; a seeded draw; per burst a mask store with `cell_<split>` and `sample_<split>` layers | `ponzi-models panel-build --panel-spec SPEC --bursts B` |
| `panel-assemble` | the built panel: record (`panel.json`, with the `specs:` block of its panel spec), cells, catalogue, draw table, coverage, content id; by default in `$PONZI_HOME/panels/<id>` | (same command) |

Each cell has a window: its own (`window_start`, `window_end` in the cells table) or the panel spec's. A catalogue row's window spans those of the cells it serves, and a burst's spans those of all its cells. A null run uses the burst's window for its split.

`SPEC` is a name or a folder: a name is looked up in `$PONZI_HOME/panel_specs/` first, then in ponzi-suite's `panel_specs/` ([Naming](../models/naming.md#spec-folders)). `panel-build` builds from the folder (ponzi-core CR-056, CR-070): its geojson give the cells, their splits, strata, windows and bursts, and a cell is drawn only in the bursts it names; `panel.yaml` gives the draw. A burst of the table that the spec does not name is refused. The build freezes the panel spec's name to its hash in the registry's `specs.json` (`--registry`): a spec of the same name and another hash is refused. What the folder does not give is not made up:

- A cell with no outline has no box to draw in. The build refuses it unless `--without-outline drop` leaves it out. In `majortom-global` these are the 24 cells that were never delivered; none of their bursts has a coherence store or serves another cell.
- The stores come from the burst table (`--bursts`: `burst_id`, `coherence`, `sidecar`).

Defaults (the old Major-TOM panel's rules): settlement and climate classes per cell; two pixel strata, `built` and `land_nonbuilt`, cut from the sidecar's built-up and land layers; 1,000 pixels per stratum per cell. `split.assign` pins cells to a split (held-out cells).

Classifiers are components: a panel spec names a `kind`, built in (`constant`, `raster_classes`) or registered by a package under the entry point group `ponzi.panel_classifiers`.

## How a panel is used

Everything reads a built panel through `ponzi_models.panels.panel.Panel`. A panel run is the production run on one mask layer (`--mask-store`, `--mask sample_test`), so training, calibration and production read the data the same way. A burst over cells of two splits serves both, each through its own layer.

## Identity

A panel's content id comes from its spec and the structural digests of every store it uses. When the cells carry their own windows, it also takes the digest of the cells and their windows. Models and calibrations record the panel id and content id, and the panel spec's name, hash and suite commit in their `specs:` block, so a model's manifest traces back to the cells and scenes behind it. A model trained on the panel is named `<training spec>--<panel spec>`.
