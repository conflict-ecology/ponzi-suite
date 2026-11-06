# CR-018: `ponzi.products`, the single-path detection recipe

- **Requested by / date:** owner, 2026-10-14
- **Status:** signed off 2026-10-14; implemented on branch `dating-recipe` (not merged)

## Why

The Gaza release (v4, `ops/gaza_release` of the monorepo) turns codes into dated damage events with code that lives in a side-analysis folder and reads a release lattice, three paths and the building layers at once. Its per-path stage (flag runs, Et dating, episodes) is general: any burst or path with codes and Et can use it. It becomes the first part of `ponzi.products`, its parameters named (the release's values as a preset), so that a burst's events can be made by a command, compared, and later confirmed across paths by a separate rule.

## What changes

### 1. The recipe (`ponzi.products.recipe`)

`DetectionRecipe`, a frozen pydantic model (unknown fields refused). `load_recipe` takes nothing (the defaults), a preset name, or a yaml file of fields that may start from a preset (`preset: gaza_release_v4` plus overrides).

**Defaults and the preset (owner, 2026-10-14).** By default NO gap is bridged (a run is a maximal sequence of consecutive flagged anchors; one unflagged anchor ends it) and there are NO episodes (every run is its own event). The reason: a later flag after a gap most likely indicates a repeat damage event, so bridging and grouping are left out for now. Both stay parameters, and the release's values are the named preset `gaza_release_v4` (`ponzi.products.PRESETS`), which the HPC check uses so that it compares like with like. Dating is the release's (the anchor of largest Et in the window around the run's first flag), with one owner change: by default the windows of two runs never overlap (item 3).

| Field | Default | Preset `gaza_release_v4` | Where the release value comes from |
|---|---|---|---|
| `calibration_kind` | `ceiling` | `ceiling` | `model.stores` of v2: `mon_b5h5_d38f1p_mean_cc/pcodes.zarr`, the ceiling-conditional codes (`conditional_codes.py`) |
| `code` | 50 | 50 | `flags.code` of `release_config_v2_loose.yaml`, which v3 and v4 inherit (-log10 p 2.5, 1 in 316). release v1 and v2 strict used 55; v4 is the loose build |
| `gap` | 0 | 1 | `common.et_events`: runs one anchor apart are merged (`f2[:, 1:-1] \|= f[:, :-2] & f[:, 2:]`) |
| `dating_pre`, `dating_post` | 1, 4 | 1, 4 | `flags.et_pre`, `flags.et_post`: the window first flag - 1 .. first flag + 4 |
| `windows` | `exclusive` | `overlapping` | the release's windows could overlap (`common.et_events`); see below |
| `episode_days` | none | 60 | `confirmation.repeat_min_days` |
| `start_date` | none | `2023-10-07` | the release's `period.war_start` was `2023-10-07` (the period starts at the first acquisition AFTER it); a dataset choice, so not a default |

The rules, ported from `common.et_events` and `common.episodes`:

1. A flag is an anchor whose code is at or above `code`; no score (255) never flags.
2. Runs: consecutive flags, with gaps of at most `gap` unflagged or unscored anchors bridged. `gap: 0` (the default) bridges nothing; `gap: 1` is the release's rule exactly; larger values bridge longer gaps the same way.
3. Dating: the anchor k in [first flag - `dating_pre`, first flag + `dating_post`], cut to 1 .. T - 1 as the release cut it (index 0 is never a dating anchor; it never has a statistic), with the largest Et; NaN skipped; on a tie the earlier anchor.

   **Exclusive windows (owner, 2026-10-14; the default, `windows: exclusive`).** The dating windows of two runs of a pixel never overlap, so two runs can never pick the same anchor: a run's window is `[first - dating_pre, min(first + dating_post, next_first - 2)]`, where `next_first` is the first flag of the pixel's next run, and it never starts before the previous run's window end + 1. The anchor just before a run's first flag is where that run's break most plausibly sits, so on a conflict it goes to the later run; the earlier run has already had its own start window. Since runs are separated by at least one unflagged anchor (more with `gap`), `next_first - 2 >= first`, so the window is never empty for `first >= 1` and the start clause never acts; the window can be empty only at the series start (a run at index 0 whose next run starts at index 2: `[-1, 0]` holds nothing of 1 .. T - 1). A run with an empty window, and a run whose window holds no finite Et, is dated to its first flag (`event_dated` 0); the first case is counted as `runs_empty_window` in the store's counts, both are in `undated`. With exclusive windows no two runs share an anchor, so `event_n_runs` is always 1.

   `windows: overlapping` is the release's rule: windows may overlap, and two runs dated to the same anchor are one event (the release's bool raster merged them the same way); the event keeps the earliest first flag, the latest last flag and the largest code, and `event_n_runs` says how many runs it holds. **The preset keeps `overlapping`**: the preset exists to reproduce the release, and the HPC check uses it to show that the port gives the release's events exactly; with exclusive windows that comparison would mix porting differences with the rule change. The check counts separately how many runs the exclusive rule re-dates on the release burst.
4. The period: an event dated before the first anchor after `start_date`, or after the last scored anchor (`t_hi` of the p-value store), is dropped, as the release kept `[a0, a1]` with `a1` the path's `t_hi`. The runs themselves are formed and dated on the full record, so a run that starts before the period can be dated inside it. Et exists up to four time indices after `t_hi` (CR-017), and a run near the end can be dated there; such an event is dropped, as in the release.
5. Episodes, only when `episode_days` is set (not by default): per pixel in date order, the first event opens episode 1; a later event at least `episode_days` days after the START of the current episode opens the next one (repeat), a sooner one belongs to the current episode (ongoing). Days are the acquisition dates of the store's time axis.

### 2. The code the recipe reads

The `anomaly` array of the p-value store (C22) `pvalues_<calibration id>.zarr` of the run, under a calibration of kind `ceiling` by default (refused when the store's kind differs from `calibration_kind`). That is the release's code: `pixel_protocol.full_series` read `anomaly` of `runs_v4/<burst>/mon_b5h5_d38f1p_mean_cc/pcodes.zarr`, which `conditional_codes.py` wrote as the global code against the F1p panel null re-expressed against the null of the pixel-anchor's ceiling class (classes by the ceiling code, edges 60 and 80, lookup `cc_lut_mon_b5h5_d38f1p_mean.npz`). In the registry that is the calibration `mt02-ceiling` of `tide_c30_gaza_f1p_mt0.2` (`ponzi-models`, "the ceiling lookup of the Gaza releases"). The ceiling code itself is not read. Et is `Et` of the run's `summary.zarr` (C24, CR-017).

### 3. The burst product: `ponzi detect`

`ponzi.products.detect(run_dir, calibration_id, recipe=None, *, out=None, rows=64, overwrite=False)` and `ponzi detect RUN_DIR --calibration ID [--recipe PRESET|FILE] [--out PATH] [--overwrite]` write `<run_dir>/events_<calibration id>.zarr` (C25, `ponzi.contracts.events`, `docs/contracts/events_store.md`):

- `state` `(time, y, x)` uint8 bits: flag 1, run 2 (bridged anchors have run without flag), event 4 (dating anchor), new episode 8, first 16; what a page needs to draw flags, first damage, repeats (8 without 16) and ongoing events (4 without 8) per anchor.
- per pixel `n_events`, `first_t`, and `n_episodes` with episodes;
- one row per event: `event_y`, `event_x`, `event_t` (dating anchor), `event_first_t`, `event_last_t`, `event_max_code`, `event_et`, `event_dated`, `event_n_runs`, sorted by pixel and date; `event_episode` and `event_new_episode` only with episodes. Without episodes these columns and `n_episodes` are OMITTED (not written as zeros or fill), and the new-episode bit is never set, so a reader cannot mistake "no episodes" for "episode 0"; `first` (bit 16, `first_t`) is the pixel's first event either way;
- attrs: the recipe and its digest, the inputs (paths, structural digests, the calibration record, `t_lo`, `t_hi`), the period, counts, producer and version, `complete` last.

The run is read in blocks of 64 grid rows over every time index; only the pixels with at least one flag go through the recipe.

### 4. The path product: `ponzi detect-path`

`detect_path(run_dirs, calibration_id, out, recipe=None, *, lattice=None, overlap="max", rows=64)` and `ponzi detect-path RUN_DIR ... --calibration ID --out PATH [--recipe PRESET|FILE] [--lattice FILE] [--overlap max|min|first]`.

What the release did where two bursts of a path overlap: `pixel_protocol.full_series` took the LARGER code over the path's bursts (`np.maximum`, -1 for no score), and `flags.et_series` the LARGER Et (NaN skipped), each on its own, and then dated the runs of that combined series. A run's event depends on the whole combined series, so the release's path events are not a combination of events dated burst by burst. `detect_path` therefore combines the recipe's INPUTS on the lattice with `ponzi.grid.mosaic` and the named rule `overlap` (default `max`, the release's: the larger code with 255 as no data, the larger Et with NaN as no data), then applies the same recipe and writes the same store on the lattice. `first` and `min` are the other rules of `mosaic` (`count` is not a value). The lattice is given, or built over the bursts' pixel centres at their step (`Lattice.from_bounds` on the centre bounds, which `ponzi.grid` places exactly when the bursts are on a common lattice; one that is off is refused by `placement`). The bursts must share the time axis and the scored anchors, which the release asserted for the bursts of a path (`scored_range`). Blocks of 64 lattice rows: for each, a block lattice, `placement` for the source slices of each burst, and only those slices are read.

`ponzi.grid` had what was needed. Two things were done by hand and could be offered there: a lattice over several source grids (here `from_bounds` on their centre bounds), and the mosaic of a window of the lattice without reading the whole burst (here a block `Lattice` and `placement`). `mosaic` combines one array at a time, so a rule like "Et of the burst with the larger code" would need a joint reduce; the release did not use one.

### 5. Layering

`ponzi.products` imports `contracts`, `calibration` and `grid` (the allowed graph already declared `products: contracts, core, calibration, grid`); no new exception. Importing it loads neither torch nor the geospatial stack (added to the layering test's import check).

## Release rules left out

By default also the release's one-anchor gap bridging and its 60-day episodes (both in the preset `gaza_release_v4`, above). Beyond that, everything after the per-path events, and everything that is about Gaza rather than about a path:

1. Rule B, the cross-path confirmation (`confirmation.rule: neighbour`): an event counts only when an event of another path in the pixel or one of its 8 neighbours falls within 12 days before or after it (`window_days: 12`); the detection is dated to the pixel's own event.
2. The 12-day absorption inside `common.confirm`: a candidate event no more than 12 days after the pixel's previous detection does not start a new one, and the events used by one detection cannot confirm another. With one path every event is a detection here.
3. Release slots: an 087 acquisition and the 094 acquisition one day later form one slot labelled with the 094 date, 160 acquisitions are their own slots, and detections and episodes are counted on slot dates. Here the dates are the path's own acquisitions.
4. Coverage: `covered` (a pixel scored by at least `min_paths_covered: 2` paths) and decision 43's `require_all_paths` (an error when a product pixel is not scored by all three paths).
5. The product pixels: the release lattice and its mask cells (`lattice_mask.npz`, 502,578 cells), the built-up rule (pre-war footprint cover at least 10 %, `built: builtup_no_greenhouse`), the greenhouse exclusion (`exclude_greenhouse`, OSM `type=greenhouse` more than half the cover), the governorates (COD-AB admin2, centre inside the Strip). Here every processed pixel.
6. The period's start (`period.war_start: 2023-10-07`) as a default: available as `start_date` (default none, `2023-10-07` in the preset). The end (the last scored anchor) is kept.
7. The rain-onset gate (`flags.wet`: a stricter code at anchors after a soil-moisture rise). Not part of v4 (only in the `raingate70` test configs), listed for completeness.
8. The pre-war check (`prewar_check`), the building counts and footprints, the PCBS join, the 12-day and per-slot mosaics, the GIFs and the pages.
9. The Et store's own scope: `estat.py` computed Et on the release lattice cells only; here on every processed pixel (CR-017).

## Do results change?

No: a new subpackage and new stores, nothing existing reads or writes them.

## Tests

`tests/test_products_detect.py` (16). The comparisons with the release use the preset (without its period start). `common.et_events` and `common.episodes` are copied into the test unchanged, with the release's single-path use of them (`flags.apply` without rule B: events of the full record, kept inside the period, every event a detection, `episodes` on them).

- Hand-built code and Et cubes: a run with a one-anchor gap (bridged) dated to the largest Et inside the window while a larger one lies outside; two runs two anchors apart; a tie (the earlier anchor); a run without Et (dated to its first flag, undated); an unscored anchor in a gap (bridged); a code one below the threshold; a run at time index 0 (the window cut to 1 .. T - 1); two runs dated to the same anchor (merged, `n_runs` 2); the state bits. The release's function gives the same events and the same undated count.
- `gap` 0, 1 and 2.
- Episodes: the release's own selftest case on a 6-day axis (ongoing at 24 and 48 days, repeat at 72, ongoing 36 days after a repeat, repeat at 204, exactly 60 days opens one).
- The period: an event before it and one after the last scored anchor dropped, a run that starts before it dated inside it.
- Random cases (three seeds, three recipes, 500 pixels by 48 anchors with unscored anchors, NaN Et, many ties and an uneven time axis): events, first events, repeats and ongoing events with their episode numbers equal the release functions'.
- A real tiny run (`summaries=["et"]`, a ceiling calibration made from its own scores, `write_pvalues`), `detect`: the store against the release functions on the stores' own code and Et, the state bits, the attrs; refuses to overwrite.
- The command line, a recipe file, the preset by name and as the base of a file, the kind check, an unknown recipe field.
- Exclusive windows written out by hand: two runs 1, 2, 3 and 5 unflagged anchors apart, Et rising (each run picks its window end) and falling (its window start): windows [5, 6] and [7, 12], [5, 7] and [8, 13], [5, 8] and [9, 14], [5, 10] and [11, 16]; distinct anchors; with the largest Et on the anchor just before the later run, the overlapping rule merges the two runs into one event where that anchor is in both windows, the exclusive rule gives it to the later run. An empty window at the series start and an all-NaN window are dated to the first flag and counted.
- The defaults: one unflagged anchor ends a run, every run is its own event, no episode columns, no `n_episodes`, no new-episode bit; the same flags under the preset give fewer events with episode marks.
- The path: two overlapping synthetic bursts on a 30 m lattice, `detect_path` with blocks of 4 rows: the larger code in the overlap, the events equal the release functions on `mosaic(..., reduce="max")` of code and Et, a pixel of one burst only gets that burst's own events, another time axis is refused.

## Version

Library: minor (new subpackage, new commands, new store). Standard: the standard's detection recipe is a `DetectionRecipe` plus the calibration id; this request does not make one.

## Not in this request

- Any cross-path rule (rule B and the others listed above), and the product pixels.
- Tiles, merges and status pages (`products` in the README).
