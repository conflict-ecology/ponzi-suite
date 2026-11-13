# C23: Mask store

`ponzi.contracts.masks`. Named pixel selections on the grid of ONE coherence store. A run restricted by a layer (`RunRequest.mask_store`, `RunRequest.mask`; `ponzi run --mask-store PATH --mask LAYER`, both or neither, C4a) processes its usual process mask AND the layer, and reads and writes only the bounding window of what remains.

## Producer and consumers

Producer: whoever defines the selection, through `write_mask_store`; for a panel, `ponzi_models.panels.draw.draw_panel` (`ponzi-models panel-build`), with the layers `cell_<split>` (the processable pixels of the split's cells) and `sample_<split>` (the drawn pixels) and the attrs `panel` (the panel spec's id), `panel_spec_hash` (its `spec_hash`) and `draw_seed`. Consumers: `ponzi.core.runner.open_input` (`WindowedInput`), and through it `ponzi run`, the panel null runs (`ponzi-models null-runs`) and the masked input of a panel burst (`ponzi_models.panels.masked_input`: training, `ponzi-models export-pixels`).

Location: never inside the sidecar, which stays byte-identical. A panel's are in the panel folder, `<panel>/<burst>/<burst>_masks.zarr` (default panel folder the home's `panels/<id>@<hash8>`, on the warm tier, CR-099), recorded relative to it in the panel record (`Panel.masks_path`).

## Arrays

| Array | Dims | Stored | Content |
| --- | --- | --- | --- |
| `y`, `x` | `(y,)`, `(x,)` | float64, one chunk | the coherence store's coordinates, value for value |
| `<layer>` | `(y, x)` | bool, one chunk, fill false | one named selection; any number of layers; attr `n_pixels` (its true pixels) |

Group attrs: `source_store` (path of the coherence store the masks are for), `source_digest` (its `store_digest`, empty where the writer could not know it), `layers` (sorted names), `producer` (`ponzi.contracts.masks`), `contract_version` (the hash of C23's declaration, ponzi-core CR-085), plus the writer's own.

## Invariants

- At least one layer; every layer is bool of shape `(len(y), len(x))`; no layer is named `y` or `x`; an existing store is replaced only with `overwrite`.
- The reader takes every bool 2-d array other than `y` and `x` as a layer (other arrays are a warning) and fails without `source_store`.
- A mask store is used only with a coherence store of the same grid (`MaskDataset.check_grid`, an error otherwise), never with a pixel sample (refused); another `source_digest` than the store's is a warning; a layer that leaves no pixel of the process mask is refused.
- A layer is a selection of the input and no part of `scoring_spec_hash`; `run_meta.mask` (C9) records the store, its digest, the layer, the window and the pixel counts.

## Functions

`write_mask_store(path, y, x, layers, *, source_store, source_digest="", attrs=None, overwrite=False)`, `open_mask_store` (`MaskDataset`: `layers`, `layer(name)`, `check_grid(y, x)`, `meta`), `validate_mask_store` (checks `opens`, `coordinates`, `layers`, `only_layers`, `source`).
