# CR-039: a burst's orbit recorded, and one orbit per path

- **Requested by / date:** owner, 2026-10-26 ("lets make fix 1 and two", after the check of how the orbit path is used)
- **Status:** implemented on the owner's instruction (2026-10-26), awaiting review; uncommitted (plan decision D10)

## Why

A path is the bursts of one relative orbit (track), combined into one events store by `detect_path` and `tile`. Nothing checked that.

`detect_path` refused only bursts with different time axes or scored anchors. The time axis holds dates, so an ascending and a descending view of a place (two tracks) whose dates coincide would have been mixed into one path.

The `ponzi` package never read the track, the stores did not record the pass, and the manifest's `sat:relative_orbit` summary key was never set.

## What changes

| Where | Change |
| --- | --- |
| `ponzi.contracts.orbit` (new) | the rule: the track of a burst id (`track_of`), the state in any spelling (`orbit_state_of`), the attrs a store carries (`orbit_attrs`), a store's orbit from its attrs or its id (`orbit_of`), and `one_orbit` (two known tracks or states refused; an unknown one contradicts nothing) |
| `ponzi.products.detect`, `detect_path`, `tile.detect_cell`, `tile_path` | a path is one track seen in one direction; `allow_mixed_tracks` overrides, and then the store records `relative_orbits`, `orbit_states` and `mixed_tracks`. Events stores record `relative_orbit` and `orbit_state`, and each input's orbit is in `inputs`. `ponzi detect-path` and `ponzi tile` take `--allow-mixed-tracks` |
| `ponzi.stac.items` | `sat:relative_orbit` and `sat:orbit_state` (the known ones) on every Item of a store, with the sat extension |
| `ponzi_pipeline` | `Acquisition.orbit_state` (ASF's `flightDirection`); `pairs.orbit_state` (one burst, one direction); `assemble(..., orbit_state=)` writes `relative_orbit` and `orbit_state` into the coherence store; the work folder keeps the state |
| `ponzi-spec` | the manifest summary gains `sat:orbit_state` |
| `tests/test_layering.py` | `ponzi.stac` may import `ponzi.contracts` (it imported no subpackage before), to read a store's orbit by the one rule |

A run copies its coherence store's attrs into its own stores (unchanged), so the orbit reaches `detect_path` and the Items without a change to the runner.

## Do results change?

- No number changes. Stores and events stores gain attrs; Items gain `sat:` properties.
- A path of mixed tracks that used to pass is refused. None of the existing tests had one: their synthetic bursts have no track, which contradicts nothing.
- In ponzi-service, discovery's identity now includes each acquisition's orbit state, so the cached pairs Items of before get new content ids.

## Tests

- `packages/core/tests/test_orbit.py`:
    - the rule;
    - `detect_path` refuses two tracks or two directions, `allow_mixed_tracks` records them, and an unknown burst passes;
    - `tile_path` and the command;
    - `sat:` properties on Items.
- `packages/pipeline/tests/test_orbit_record.py`: ASF's flight direction; one direction per burst; the assembled store's attrs; the work folder.
- In ponzi-service: the chain's Items carry the orbit; the watched-area chain's published events and cells carry it.
- Results:
    - `pixi run test`: 532 passed, 14 skipped;
    - `test-pipeline`: 89 passed, 1 skipped;
    - `test-models`: 94 passed, 18 skipped;
    - `test-spec`: 39 passed;
    - ponzi-service: 80 passed.

## Version

- `ponzi`: MINOR (a check on a combination that was never meant to pass, and new attrs), part of 0.3.0.
- `ponzi-pipeline` 0.2.0 and `ponzi-spec` 0.3.0: not yet released.
