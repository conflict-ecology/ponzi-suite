# CR-090: `ponzi-worker run` takes a standard's server file

- **Requested by / date:** owner, 2026-11-12 (asked what `WORKFLOW.yaml` is; on the gap below, "yes")
- **Status:** signed off (2026-11-12), implemented (unreleased)

## Why
Local mode ([Using PONZI (agents)](../../contributing/agents/usage.md#local-mode)) says to run a standard's workflow with `ponzi-worker run WORKFLOW.yaml`, the workflow coming from `ponzi-models standard-workflow`. That command writes the server's standard file (`ponzi_server.catalog.Standard`): the workflow under `workflow:`, wrapped with `standard`, `description`, `final`, `requires`, `variables` and `specs`. `ponzi-worker run` reads only a bare workflow (`ponzi_worker.workflow.Workflow`, `extra="forbid"`) and refuses that file. To run a standard without a server, a person or an agent must cut the `workflow:` block out by hand and give the file's `variables` (the registry at least) with `--set`, and nothing checks the standard's `requires`. What runs then can differ from what a server's worker runs for the same standard.

## What changes
`ponzi-worker run FILE` takes either a bare workflow (as now) or a standard's server file, told apart by its top-level `standard:` key (`ponzi_worker.workflow.load_run`):

- **The workflow** is the file's `workflow:`.
- **The variables** are the server's for a job of that standard: the file's `variables`, under the PONZI home's shared inputs (`with_home`: `burst_map`, `slc_dir`, `orbit_dir`, `dem_dir`, `ghsl_dir`, `era5_dir`), with `--set` and `--each` over both. That is the order a server job's payload and the worker give them (`Standard.payload`, `job.answer`), so each step has the same content id as on a server: the same cache entries, reused either way.
- **`requires`** is checked before anything runs (`ponzi_models.standards.standard.unmet_requirements`, as `job.answer` does): a worker whose installed distributions do not meet it refuses, with the reason. ponzi-models is imported only for a standard file, as `job` does.
- **What is printed** names the standard (its key, `<id>@<hash8>`, CR-089) and, after the run, the content ids of the `final` steps' outputs: the Items a server would publish.
- `--dry-run`, `--executor slurm`, `--profile` and `--site` work as for a bare workflow.

A bare workflow is read as before. The worker still talks to no server.

**Docs.** [Using PONZI (agents)](../../contributing/agents/usage.md#local-mode) and [The worker](../../service/worker.md) say to run a standard locally with `ponzi-models standard-workflow STANDARD.yaml --registry DIR --out FILE`, then `ponzi-worker run FILE --each burst=... --set start_date=... --set end_date=...`, and what a workflow file is.

## Do results change?
No. The same steps and parameters run; a standard file run locally gives the content ids a server's worker gives.

## Tests
- ponzi-worker: `run` on a standard's server file plans the same job ids as the server's job of that standard for one burst (`test_standard.py`, the rehearsal's standard); the file's `variables` are used, `--set` overrides one; the home's shared inputs fill what neither gives; `requires` not met is refused before anything runs; `--dry-run` lists the jobs; a bare workflow runs as before (`test_chain.py`).

## Version
Library: ponzi-worker minor (a new kind of input). Standard: no change.
