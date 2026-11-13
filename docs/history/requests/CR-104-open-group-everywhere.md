# CR-104: the last three readers open through `open_group`

- **Requested by / date:** owner, 2026-11-13 ("draft the fix and explain why it is necessary", after the review of the 0.1.2 docs and the CR-092 rule)
- **Status:** signed off (2026-11-13, "execute"), implemented (0.2.0)
- **Builds on:** CR-086 (every store is zarr v3), CR-092 (every reader opens through `ponzi.contracts.base.open_group`; every validating opener raises `ContractError`)

## Why
CR-092 made two rules, and the Store formats index ([contracts](../../reference/contracts.md)) now states them as true of all code:

- every reader opens a store through `open_group`, which refuses a zarr format other than v3;
- a store that breaks its contract raises `ContractError` (a `ValueError`), so a caller can catch every contract failure with one type.

CR-092 listed the sites it found. Three were missed. On 2026-11-13 each was tried on a zarr v2 store and on a missing path (ponzi 0.1.2 plus the CR-102 working tree):

| Site | Store | What happens now | Why it matters |
| --- | --- | --- | --- |
| `ponzi.evaluation.labels.open_labels` (`labels.py:212`) | label zarr (C11). Made outside PONZI by whoever draws the labels. | It passes `zarr_format=3` itself, so a v2 store is refused, but with `zarr.errors.GroupNotFoundError: No group found in store`. That error is not a `ContractError`, and the message is wrong: there is a group, in the wrong format. | This store is the one most likely to arrive from elsewhere. The person who made it is told there's no group, not that it must be zarr v3. `ponzi.evaluation.events` (line 408) and any caller catching `ContractError` don't see this failure as a contract failure. |
| `ponzi.contracts.staged.finish_staged_store` (`staged.py:89`) | `staged.zarr` (C23) | It opens `r+` with no format, so it **writes `stages_written` into a v2 store without complaint** and consolidates it. | Today its only caller (`ponzi.core.sinks`, line 364) passes the store that `create_staged_store` has just written as v3, so this can't happen yet. It is a public function (`__all__`), though, and it breaks the rule the index states. |
| `ponzi.contracts.summary.validate_summary_store` (`summary.py:68`) | `summary.zarr` (C24) | It reads the `summaries` attribute with no format before the check that refuses v2. A v2 store with valid names is refused with a `ContractError` one step later. One with bad names is refused with a `ValueError` about the names, not the format. A missing path gives `FileNotFoundError`, not the `store not found` that every other store gives. | Its errors depend on which line fails first. `ponzi.products.detect` (line 65) relies on it. |

None of these gives a wrong number, and every store PONZI writes is v3. So this change is not about results. It brings the code in line with the rule its own documentation states, and gives the one store that comes from outside (labels) an error its maker can act on.

## What changes
In ponzi, no other package:

1. `open_labels` opens with `open_group(path)`. This also replaces its own `FileNotFoundError` for a missing path with `open_group`'s `ContractError("store not found: …")`, as every other opener gives.
2. `finish_staged_store` opens with `open_group(path, mode="r+")`.
3. `validate_summary_store` reads `summaries` from `open_group(path)`.

These places stay as they are: the reopens of a store that was just written (`create_*` returning `zarr.open_group(..., "r+")` in `staged.py`, `summary.py`, `pred.py` and `score.py`) and the writers that pass `zarr_format=3`. Neither reads a store from elsewhere. The test-data builders in ponzi-models (`synthetic.py`, `panels/panel.py`) also stay as they are.

The contract pages need no change. The index already states both rules, and this makes them true.

## Do results change?
No. No store PONZI writes is affected, and no number changes. The only differences are error types and messages: a v2 or missing label store now gives a `ContractError` (still a `ValueError`), not a `GroupNotFoundError` or `FileNotFoundError`. `finish_staged_store` now refuses a v2 store it used to write to.

## Tests
In `packages/core/tests/test_contract_rules.py`, using its `_v2` helper:

- `open_labels`, `finish_staged_store` and `validate_summary_store` are added to the cases of `test_an_opener_refuses_a_zarr_v2_store`. Each raises `ContractError`, and `finish_staged_store` leaves the v2 store's attributes unchanged.
- `open_labels` and `validate_summary_store` raise `ContractError` on a missing path.
- The existing label, staged and summary tests pass unchanged (`test_contract_rules.py`, and the label and summary tests in `ponzi.evaluation` and `ponzi.products`).

## Version
Library: `ponzi` patch. It refuses what was always outside the rules, with the type the rules name. A caller that catches `FileNotFoundError` from `open_labels` would need to catch `ContractError` instead, and no caller in the suite does. Standard: no change, and no standard's key moves.
