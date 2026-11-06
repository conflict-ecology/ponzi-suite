# CR-073: the store contracts for agents, and the code-first rule

- **Requested by / date:** owner, 2026-11-06 ("the contracts may be useful for agents. add them to the agents page. frame them such that the goal is 'how to use the repos'. add an additional agent contract that dictates changes in code must also be reflected in the contracts. But should be code first.")
- **Status:** signed off (2026-11-06), implemented (2026-11-06)

## Why
No code reads the contract pages: the code (`ponzi.contracts` and the config schemas) defines and checks every store, and the pages describe it. They are most useful to whoever reads a store without reading the code, agents included, and they stay useful only if they follow the code. Nothing checked that they do.

## What changes
- **For agents using PONZI** (`contributing/agents/usage.md`, "Using PONZI"): the page is framed as how to use the repositories, and gains "Reading what PONZI makes": read a store's contract before its arrays; a table from what you have (the Collection and asset) to its contract and the function that opens it; `ponzi validate-store`; the code is the authority.
- **For agents changing PONZI** (`contributing/agents/contributing.md`, loaded by every repository through `agents/shared.md`): a section "Changing what a store holds (code first)": the code changes first, with its tests green; then the contract is updated to match, in the same change; where they disagree the code wins unless the change request says the code is wrong; a store format change is a MAJOR version. The Finishing list checks it. `agents/ponzi-core.md` says the same.

## Do results change?
No. Documentation and agent instructions only.

## Tests
The strict docs build.

## Version
None.
