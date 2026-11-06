# C25: Events store

Status: CR-018 (2026-10-14), CR-030 (the Major TOM cells), `ponzi.contracts.events`, written by `ponzi.products.detect`, `detect_path` and `tile_path` (`detect_cell` per cell) (`ponzi detect`, `ponzi detect-path`, `ponzi tile`).

## Purpose

The dated flag runs of one burst, or of one path on a lattice, under one detection spec (`ponzi.products.DetectionSpec`): per pixel its events (dating anchor, first and last flagged anchor, largest code, Et at the dating anchor, episode), and per anchor a small state raster from which pages draw flags, events, first events and episode openers.

A detection spec is a yaml file of its fields, any subset, which may build on another file with `extends` (`ponzi.products.load_detection_spec`, `--detection-spec NAME|FILE`; named presets are gone, CR-043, and a `preset` field is refused); without one the default spec. The fields and their defaults: `calibration_kind` `ceiling` (the kind of p-value store read; another is refused), `code` 50, `gap` 0, `dating_pre` 1, `dating_post` 4, `windows` `exclusive` (or `overlapping`), `episode_days` None (no episodes), `start_date` None, `provisional` false (left out of the fields and the hash when false). The Gaza release's values are a detection spec file, ponzi-suite `testcases/gaza/detection.yaml`.

## Producer and consumers

Producer: `ponzi.products`, run by the commands above or by the ponzi-worker stages `detect` (one burst, collection `ponzi-events`) and `tile` (one path, one store per Major TOM cell, collection `ponzi-events-cell`), whose `detection` param holds the detection spec's fields. Consumers: ponzi-visual (`src/events.ts`: `state` one date at a time, `time`, `y`, `process_pixels` and the attrs, from the zipped store the server serves for an Item's `events` asset).

Location: `<run folder>/events_<calibration id>.zarr` for a burst (`events_store_name`; or `--out`); a path product wherever `--out` says; a cell `<out>/<cell id>/events_<calibration id>.zarr`. Under the worker `{PONZI home}/cache/ponzi-events/<content id>/events_<calibration id>.zarr` and `{PONZI home}/cache/ponzi-events-cell/<output id>/events_<calibration id>.zarr`.

## Arrays

| Name | Dims | dtype | Fill | Notes |
|---|---|---|---|---|
| `state` | `(time, y, x)` | uint8 | 0 | bit field, below; attr `bits` (name to value); chunks `(T, rows, X)`, `rows` 64 by default (`ponzi.products.detect.ROWS`, the blocks the producer writes) |
| `n_events` | `(y, x)` | uint16 | 0 | events of the pixel |
| `n_episodes` | `(y, x)` | uint16 | 0 | episodes of the pixel; only when the detection spec has episodes |
| `first_t` | `(y, x)` | int16 | -1 | time index of the pixel's first event, -1 none |
| `event_y`, `event_x` | `(event,)` | int32 | | row and column of the event's pixel on this store's grid |
| `event_t` | `(event,)` | int16 | | time index of the dating anchor (the event's date is `time[event_t]`) |
| `event_first_t`, `event_last_t` | `(event,)` | int16 | | first and last flagged anchor of the run (of the merged runs) |
| `event_max_code` | `(event,)` | uint8 | | the largest code of the run(s), `round(20 * -log10 p)` |
| `event_et` | `(event,)` | float32 | | Et at the dating anchor (the float16 of C24), NaN when undated |
| `event_dated` | `(event,)` | uint8 | | 1: dated by Et; 0: no finite Et in the window, dated to the first flag |
| `event_episode` | `(event,)` | uint16 | | 1, 2, ...: the episode the event belongs to; only with episodes |
| `event_new_episode` | `(event,)` | uint8 | | 1: the event opens its episode (the first event, or a repeat); only with episodes |
| `event_n_runs` | `(event,)` | uint8 | | flag runs dated to the same anchor, merged into this event; always 1 with exclusive windows (the default) |
| `event_provisional` | `(event,)` | uint8 | | a provisional detection spec only (CR-021): 1 when the event's first flag has no final score yet; it is then dated to that flag (`event_dated` 0) |
| `time`, `y`, `x`, `process_pixels` | | int64; float64; float64; uint8 | | the inputs' grid (a path: the lattice's centres and the mosaic of the bursts' process masks, `max`); `time` in nanoseconds since 1970-01-01 (attrs `units`, `calendar`) |

The table is sorted by pixel (row-major) and, within a pixel, by date. Bits of `state`:

| Bit | Name | Set where |
|---|---|---|
| 1 | `flag` | the code is at or above the detection spec's `code` |
| 2 | `run` | the anchor is inside a flag run once gaps of up to `gap` anchors are bridged (a bridged anchor has `run` without `flag`) |
| 4 | `event` | the dating anchor of a kept event |
| 8 | `new_episode` | that event opens an episode (never set without episodes) |
| 16 | `first` | that event is the pixel's first |
| 32 | `provisional` | a provisional detection spec only (CR-021): the anchor's code was at or above `code` at a stage before the final one |
| 64 | `withdrawn` | a provisional detection spec only: provisional, and the anchor's final code is below `code` (withdrawn at the final stage; a confirmed one has `flag`) |

So a page's "first damage" raster is `state & 16`, every later event is `(state & 4) and not (state & 16)`; with episodes, "repeat" is `(state & 8) and not (state & 16)`, "ongoing" is `(state & 4) and not (state & 8)`, and the colour by episode comes from the table. Without episodes (the default detection spec) the episode columns and `n_episodes` are omitted, not filled.

A provisional detection spec (`DetectionSpec.provisional`, CR-021, owner decision D4; off by default, when the bits 32 and 64 and the column `event_provisional` do not exist and the store is that of before, byte for byte) reads the stage codes of a staged run (C22 `anomaly_staged`): the anchors after `t_hi` up to `staged_t_hi` flag by their latest stage code, at the same `code` as the final ones; at the final stage the final code confirms (`flag` and `provisional`) or withdraws (`provisional` and `withdrawn`) a flag. Withdrawn flags make no events. Dating stays final only: an event whose first flag has no final score is dated to that flag.

## Attrs

| Attr | Meaning |
|---|---|
| `detection_spec`, `detection_spec_hash` | the detection spec's fields and its hash (`DetectionSpec.spec_hash`, `ponzi_spec.identity.spec_hash`; named `recipe` and `recipe_digest`, a sha256 digest, before CR-070) |
| `inputs` | per burst: `run`, `relative_orbit`, `orbit_state`, `pvalues` (path, structural digest, calibration record, `t_lo`, `t_hi`), `summary` (path, structural digest) |
| `t_lo`, `t_hi` | the scored anchors of the inputs |
| `period` | `[first, last]` time index an event may be dated to: the first anchor after the detection spec's `start_date` (0 without one) and `t_hi` |
| `counts` | `events`, `pixels_with_events`, `undated` (dated to the first flag: no finite Et or an empty window), `runs`, `runs_empty_window` (exclusive windows, CR-018), and `episodes` with episodes |
| `producer`, `ponzi_version`, `epsg` | `ponzi.products.detect`, the library version, the grid's EPSG (a path: the lattice's) |
| `relative_orbit`, `orbit_state` | the inputs' orbit, where known (`ponzi.contracts.orbit`); a path combined with `--allow-mixed-tracks` over several has `relative_orbits`, `orbit_states` and `mixed_tracks` instead |
| `lattice`, `overlap` | a path product: the lattice (`Lattice.to_dict`) and the rule that combined the bursts (`max`, `min`, `first`) |
| `resample`, `majortom_cell`, `majortom_dist_km` | a Major TOM cell (CR-030): `nearest` (each lattice pixel reads the burst pixel holding its centre, in the burst's projection), the cell id and the grid distance |
| `staged_t_hi` | a provisional detection spec only (CR-021): the last anchor with a stage code; `period` then ends there |
| `complete` | set last; `open_events_store` refuses a store without it |

## Invariants

- One detection spec and one calibration per store; the p-value store's calibration kind is the detection spec's `calibration_kind`; the summary store validates and holds `et`; the p-value store and the summary store of each burst are of the same run (equal `time`, `y`, `x`). A provisional detection spec needs a p-value store with stage codes.
- An existing store is written again only with `overwrite`.
- Every flag run of the full record gives one event, unless its dating anchor is outside `period`; runs dated to the same anchor are one event.
- For a path, the bursts share the time axis, the scored anchors and `staged_t_hi`, and are of one relative orbit seen in one direction (a burst whose orbit is unknown contradicts nothing) unless `allow_mixed_tracks`. Without `--lattice` they must share one `epsg`; with a lattice of another EPSG they must be resampled (a cell). A cell no processed pixel reaches gets no store.
