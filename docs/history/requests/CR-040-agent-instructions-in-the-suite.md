# CR-040: the agent instructions move to ponzi-suite

- **Requested by / date:** owner, 2026-11-03 ("in the suite, I want all the agent mds as well", then "yes" to the one-line `CLAUDE.md` and this request)
- **Status:** implemented on the owner's instruction (2026-11-03), awaiting review; uncommitted (plan decision D10)

## Why

The suite is the hub of PONZI's documentation, organized like PyTorch's: each repository documents its own domain, and the suite holds what spans them. The instructions for AI agents span every repository. Until now they lived only in this repository's `CLAUDE.md`. ponzi-service and ponzi-visual had none, and the rules they share (no commits, HPC approval, prose style) would otherwise be copied into each one and drift apart.

## What changes

| Where | Change |
| --- | --- |
| `CLAUDE.md` | one line, `@../ponzi-suite/agents/ponzi-core.md`, which imports this repository's instructions from the suite checked out beside it |
| ponzi-suite `agents/ponzi-core.md` | the former content of `CLAUDE.md`, word for word, apart from the lines now in `shared.md` |
| ponzi-suite `agents/shared.md` | the rules for every repository: no commits unless the owner asks, the HPC rule (moved from `CLAUDE.md`, unchanged), the prose style (moved, unchanged), and the published checklist `docs/agents/contributing.md` imported, so it is written once |
| ponzi-suite `plugins/ponzi-dev/` | the agent skills, as a Claude Code plugin with the suite's marketplace; first skill `ux` |

ponzi-service and ponzi-visual get the same one-line `CLAUDE.md`, importing `agents/ponzi-service.md` and `agents/ponzi-visual.md`.

A change to `agents/ponzi-core.md` changes this repository's rules, so it still needs a request here; `agents/README.md` in the suite says so.

Without a suite checkout beside this repository the import loads nothing. The docs CI already assumes that layout.

## Do results change?

No. No code, contract or store changes.

## Tests

`pixi run test` (unchanged, no test reads `CLAUDE.md`).

## Version

None: no distribution changes.
