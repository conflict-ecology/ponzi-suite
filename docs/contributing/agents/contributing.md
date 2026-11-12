# Contributing (agents)

Checklists for agents that change PONZI's code. People follow the same rules in [Contributing](../index.md).

## Before any change

- [ ] A change request exists in ponzi-suite `docs/history/requests/` and the owner has signed it off.
- [ ] You know whether the change alters results for an existing spec. If it does, it is RESULTS-CHANGING.
- [ ] You do not commit, tag or push unless the owner asks; leave changes in the working tree for review.
- [ ] You do not access a cluster, submit a job or move data without the owner's approval for that action.

## While changing

- [ ] Imports follow the layering: `ponzi-spec` imports no ponzi distribution; `ponzi` does not import `ponzi_pipeline` or `ponzi_models`; the service and the front end import no computing distribution.
- [ ] No hostnames, cluster paths or user names in code; paths through `pathlib` and `ponzi_spec.paths`.
- [ ] No data in a code repository: the files PONZI runs from (specs, standards, test cases) go in ponzi-suite, and everything computed goes in the PONZI home (`~/.ponzi`, or `$PONZI_HOME`).
- [ ] Every new function has a concise docstring.
- [ ] Identity params (hashed) and request params (not hashed) are kept apart.
- [ ] Golden files are never regenerated to make a test pass.

## Changing what a store holds (code first)

A store's format is defined by the code (`ponzi.contracts`, and `ponzi.core.scoring_spec`, `ponzi.core.runner`, the onboarding spec for the spec contracts); its [contract](../../reference/contracts.md) describes it. Keep them in step, in this order:

- [ ] **Code first.** Change the schema, the writer and the checks in the code, with their tests, until they are green. Never write a contract for behaviour the code does not have yet.
- [ ] **Then the contract, in the same change.** Update the contract page in ponzi-suite `docs/reference/contracts/` to say what the code now does: arrays or columns, dtypes, fills, chunks, attrs, invariants, the producer and the readers. A new store gets a new contract and a row in the index.
- [ ] **The code wins.** Where a contract and the code disagree, the contract is fixed to match the code, not the other way round, unless the change request says the code is wrong.
- [ ] A change to a store format is a MAJOR version of the distribution that writes it; say so in the change request and the `CHANGELOG.md` entry.

## Adding a stage

- [ ] `StageSpec` with known Collections, identity params, resources, fan-out.
- [ ] Entry point under `ponzi.stages`.
- [ ] Synthetic tests: outputs validate against the PONZI extension schema; the content id is stable.
- [ ] A docs page and a line in the stages table.

See [A new stage](../new-stage.md) for the full steps.

## Adding a model

- [ ] Training spec, panel spec, prepare, train, export, register, null, calibrate, benchmark, standard, in that order.
- [ ] The model is referenced by registry id and digest, never by path.

See [A new model](../../models/new-model.md).

## Finishing

- [ ] The distribution's tests are green.
- [ ] `CHANGELOG.md` has an entry.
- [ ] The docs pages that describe the changed behaviour are updated.
- [ ] Every store whose format changed has its contract updated to match the code.
