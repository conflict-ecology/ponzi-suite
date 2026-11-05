# Contributing (agents)

Checklists for agents that change PONZI's code. People follow the same rules in [Contributing](../contributing/index.md).

## Before any change

- [ ] A change request exists in `ponzi-core/docs/requests/` and the owner has signed it off.
- [ ] You know whether the change alters results for an existing config. If it does, it is RESULTS-CHANGING.
- [ ] You do not commit, tag or push unless the owner asks; leave changes in the working tree for review.
- [ ] You do not access a cluster, submit a job or move data without the owner's approval for that action.

## While changing

- [ ] Imports follow the layering: `ponzi-spec` imports no ponzi distribution; `ponzi` does not import `ponzi_pipeline` or `ponzi_models`; the service and the front end import no computing distribution.
- [ ] No hostnames, cluster paths or user names in code; paths through `pathlib` and `ponzi_spec.paths`.
- [ ] No data in a code repository: the files PONZI runs from (panels, forecasters, run configs, test cases) go in ponzi-suite, and everything computed goes in the PONZI home (`~/.ponzi`, or `$PONZI_HOME`).
- [ ] Every new function has a concise docstring.
- [ ] Identity params (hashed) and request params (not hashed) are kept apart.
- [ ] Golden files are never regenerated to make a test pass.

## Adding a stage

- [ ] `StageSpec` with known Collections, identity params, resources, fan-out.
- [ ] Entry point under `ponzi.stages`.
- [ ] Synthetic tests: outputs validate against the PONZI extension schema; the content id is stable.
- [ ] A docs page and a line in the stages table.

See [A new stage](../contributing/new-stage.md) for the full steps.

## Adding a model

- [ ] Fit spec, panel, prepare, train, export, register, null, calibrate, benchmark, standard, in that order.
- [ ] The model is referenced by registry id and digest, never by path.

See [A new model](../contributing/new-model.md).

## Finishing

- [ ] The distribution's tests are green.
- [ ] `CHANGELOG.md` has an entry.
- [ ] The docs pages that describe the changed behaviour are updated.
