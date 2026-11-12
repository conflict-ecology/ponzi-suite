# Grids: processing and outputs

- **Processing** stays on each burst's native grid: the fixed grid its coherence store was assembled on. Onboarding, runs, p-values and per-burst events are computed there; nothing is resampled except where coregistration needs it.
- **Delivered outputs** are on the [Major TOM](https://github.com/ESA-PhiLab/Major-TOM) grid: fixed, near-equal-area cells of about 10 km over the globe, named by their bottom-left corner (`433U_621R`). The cells of panels are Major TOM cells too.

`ponzi.grid.MajorTomGrid` is a port of the reference grid, equal to it cell for cell (tested against golden values the reference wrote). `cell_lattice(cell, step)` is the cell's own grid: its UTM zone, pixel edges on multiples of `step`. `ponzi_spec.majortom.MajorTomGrid` is the same grid in plain Python, with no numpy, for ponzi-server, which makes watched areas from cells (CR-066); a parity test holds the two equal, float for float.

`ponzi tile RUN_DIR... --calibration ID [--out DIR]` writes the events of one path on every Major TOM cell its bursts reach, one store per cell (`<out>/<cell>/events_<calibration>.zarr`; without `--out`, `tiles_<calibration>/` in the runs' common parent folder, CR-088), the bursts read at the pixel holding each cell pixel's centre and overlapping bursts combined by a named rule.
