# CR-033: what the worker needed from the Items (a null geometry kept, a scope for any store)

- **Requested by / date:** owner, 2026-10-23 (phase 6 of the overhaul plan: the worker with a local executor, in ponzi-service)
- **Status:** implemented on the owner's instruction (2026-10-23), awaiting review; uncommitted (plan decision D10)

## Why

The worker keeps every Item as `item.json` in its cache and reads it back. Two gaps showed up there:

1. `Item.dump()` left out every None field, `geometry` included. STAC requires the key (null is allowed), and `Item` requires it, so an Item without a footprint (a calibration) did not load back from its own dump.
2. `store_item` named an Item by the store's `burst_id` attr, else the store's file name. An events store has no `burst_id`, so the burst's events were named `events_cc`, and a Major TOM cell's events could not carry the cell id.

## What changes

| Where | Change |
| --- | --- |
| `ponzi_spec.stac.Item.dump` | keeps `geometry`, null or not; every other None field is still left out |
| `ponzi.stac.store_item` | new keyword `scope`: the scope of the Item id (default: the store's burst id, as before) |

## Do results change?

No. No store changes, and an Item with a geometry dumps as before.

## Tests

- `packages/spec/tests/test_stac.py::test_an_item_without_a_footprint_round_trips`.
- `packages/core/tests/test_stac_items.py::test_a_scope_names_an_item_whose_store_has_no_burst`.
- `pixi run test`: 525 passed, 14 skipped.
- `test-spec`: 39 passed.
- `test-pipeline`: 76 passed, 1 skipped.
- `test-models`: 94 passed, 18 skipped.

## Version

`ponzi-spec` PATCH, released with CR-034 as 0.3.0. `ponzi`: MINOR (a keyword), part of 0.3.0.
