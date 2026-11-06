# CR-071: the store contracts and the change requests move to ponzi-suite

- **Requested by / date:** owner, 2026-11-06 ("within ponzi-core there are docs and contracts which I would prefer to sit in ponzi-suite", then "I want all contracts in suite. approved")
- **Status:** signed off (2026-11-06), implemented (2026-11-06)

## Why
The suite already published both folders, read from the ponzi-core checkout at build time, so readers met them as suite pages while the files sat in ponzi-core. The change requests are no longer ponzi-core's alone: CR-068, CR-069 and CR-070 each changed ponzi-service, ponzi-visual or the suite as well. The contracts are read by the worker, the server and anyone reading a store, most of whom never open ponzi-core. The suite is the one place for the written rules and the history.

## What changes
- ponzi-core `docs/contracts/*.md` move to ponzi-suite `docs/reference/contracts/`; ponzi-core's `docs/contracts/README.md` (the C1 to C26 table) becomes `docs/reference/contracts.md`.
- ponzi-core `docs/requests/` (the CRs and `TEMPLATE.md`) move to ponzi-suite `docs/history/requests/`, this request with them.
- ponzi-core keeps no `docs/` folder. Its README, the package READMEs and the docstrings that named a contract file name the suite's path.
- The links between contracts and requests are rewritten to their new relative paths; none pointed into ponzi-core's code.
- The suite's docs hook no longer reads ponzi-core's docs: the pages are ordinary files, its contracts marker and its link rewriting are removed, and its requests marker lists the suite's own `docs/history/requests/CR-*.md`.
- The change process: a ponzi-core change starts as a request in ponzi-suite `docs/history/requests/`, signed off there. The request and the code are now two commits in two repositories, joined by the CR number in each commit and changelog entry. A change to a store format changes its contract in the suite in the same change (`agents/ponzi-core.md`, `contributing/process.md`, the contributor checklist, `agents/README.md`).

## Do results change?
No. Documentation and a docs build hook only.

## Tests
The strict docs build (`mkdocs build --strict`); ponzi-core's tests (docstrings only change there).

## Version
Library: none needed (no code behaviour changes). Standard: no change.
