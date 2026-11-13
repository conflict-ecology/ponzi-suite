# Using PONZI (agents)

How to use PONZI to get results and understand them: the two tools you work through, what each can do, the rules that hold whichever you use, and how to read what PONZI makes. For changing the code, see [Changing the code](contributing.md).

## Two tools

| | `ponzi-client` | `ponzi-worker` (and the ponzi-core commands) |
| --- | --- | --- |
| **What it is** | a REST client of a PONZI server | the program that computes: it runs a workflow's stages on this machine or as SLURM batches |
| **Needs** | a running server: its URL (`--url` or `$PONZI_URL`) and a key (`$PONZI_KEY` or `$PONZI_KEY_FILE`; [Logins and keys](../../getting-started/authentication.md)) | PONZI installed here: ponzi-core, and ponzi-service for the worker ([Install](../../getting-started/install.md)); no server |
| **Use it to** | find, watch and fetch what the server holds or will make: bursts, standards, watched areas, published outputs | run a standard or any workflow yourself, on bursts and dates you choose |
| **Results** | on the server, found by search | in this machine's PONZI home (`$PONZI_HOME/cache/`, [Folders and environment variables](../../getting-started/paths.md)), by content id |

The two are independent. You may run workflows with the worker whether or not a server is running, and without anything upstream (no server, no request, no watched area), as long as you keep to the [rules](#rules). Use the client when what you need is the server's: its watched areas, its published outputs, a run its workers should make. `ponzi-client standards` answers when a server is reachable; a connection error, or no `--url` and no `$PONZI_URL`, means there is none.

## The client: asking a server

The client calls the server's API; the server's workers compute. Through it:

| Task | Client call (Python) | Command | Notes |
| --- | --- | --- | --- |
| Find bursts over an area | `c.bursts(bbox=...)` | `ponzi-client bursts --bbox ...` | burst ids look like `t028_058198_iw3` |
| See what can be run | `c.standards()` | `ponzi-client standards` | a standard is named `s1-general@<hash8>`, its version its content hash; its id alone names the one version a server holds |
| Ask for an area to be watched | `c.majortom_cells(bbox=...)`, then `c.request_watch(cells=[...], tags="a,b")` | `ponzi-client watch-request --cells C[,C] --tags T[,T]` | a `user` key; an admin user approves it (a `client:write` key makes it directly: `create_area`, `area-create`); 1 or more tiles over land; tags one word each (letters, digits, `-`, `_`); see [Watched areas](../../using/watched-areas.md) |
| See what a tag covers | `c.tags("q")`, `c.tag("gaza")` | `ponzi-client tags q`, `ponzi-client tag gaza` | its areas, tiles, bursts, outputs and places (admin 0, 1, 2) |
| Pause or change a watched area | `c.update_area(area_id, active=False)` | `ponzi-client area-update ID --active false` | fields left out stay as they are |
| Look at an area now | `c.discover_area(area_id)` | `ponzi-client area-discover ID` | whatever its cadence |
| Run once | `c.submit(burst_ids=[...], standard=...)` | `ponzi-client submit --bursts B[,B] --standard S [--start D] [--end D]` | returns existing results when they exist (`reused: true`) |
| Follow a run | `c.request(request_id)`, `c.jobs(request_id=...)` | `ponzi-client request ID`, `ponzi-client job ID` | a done job lists the Items it made (`items`); a running one its message and SLURM progress |
| Find results | `c.search(collections=["ponzi-events-cell"], bbox=..., datetime=...)`, `c.search(tags=[...])` | `ponzi-client search ...` | Items of the [STAC catalog profile](../../using/stac-profile.md); the tiles (`ponzi-events-cell`) are the delivered output (CR-100) |
| Explain a result | `c.manifest(content_id)` | `ponzi-client manifest CID --yaml` | the provenance, see [Provenance (manifests)](../../using/manifests.md) |
| Fetch a result's file | `c.download(item, "events", "out/")` | `ponzi-client download COLLECTION ID events out/` | a zipped store comes back unpacked |

Through the client you do not read or write the server's storage or a worker's cache: what the server holds you reach by its API.

<a id="local-mode"></a>

## The worker: running workflows yourself

The worker runs a workflow, an ordered list of steps, each a stage with its inputs, params and `${variables}` ([Workflows and the cache](../../service/worker.md#a-workflow)). Every output is cached by content id in the PONZI home, so nothing is computed twice and a second run reuses what exists. Prefer a standard's workflow to calling stages one by one: it is what a server's worker runs, with the same content ids.

| Task | Command | Notes |
| --- | --- | --- |
| See the stages | `ponzi-worker stages` | the stages installed, with their inputs and params |
| Write a standard's server file | `ponzi-models standard-workflow STANDARD.yaml --registry DIR` | the standard must be registered; writes `$PONZI_HOME/standards/<id>@<hash8>.yaml` (`--out` elsewhere); a later build must give the workflow the registry recorded (CR-091) |
| Run a standard on bursts | `ponzi-worker run FILE --each burst=t028_058198_iw3,... --set start_date=... --set end_date=...` | takes the server file as a server's job would: its variables, its `requires` checked, every step the content id a server gives it (CR-090); prints the outputs of its final steps |
| Run any workflow | `ponzi-worker run WORKFLOW.yaml --set NAME=VALUE ...` | a workflow of your own, from stages that exist |
| See what a run would do | `... --dry-run` | the jobs, and which are already cached |
| Run on the cluster | `... --executor slurm [--site NAME] --dry-run`, then without `--dry-run` once approved | one batch per run (`--each`: one array per step); shares what is in flight with the server's loops and records who submitted it (`--by`, default `<user>@<host>`; [Agents on the cluster](../../service/hpc.md#agents)); needs an approval ([Cluster approvals](#cluster-approvals)) |
| Follow a batch | `ponzi-worker batch BATCH` | how far each step got |
| Explain a result | `ponzi-worker manifest CONTENT_ID --json` | the provenance from the local cache |
| Check a store | `ponzi validate-store PATH [--json]` | against its contract ([Reading what PONZI makes](#reading-what-ponzi-makes)) |
| One step of the data chain | `ponzi-pipeline discover`, `acquire`, `dem`, `coherence`, `assemble`, `onboard` | `ponzi-pipeline` with no argument lists them; `acquire` needs Earthdata ([Logins and keys](../../getting-started/authentication.md)) |
| A forecast run on a store | `ponzi run ...` | needs a scoring spec of a registered model (`--scoring-spec`); `ponzi --help` lists the commands |
| Check or rehearse a standard | `ponzi-models check-standard FILE`, `ponzi-models rehearse [--out DIR]` | the rehearsal is synthetic and runs on the CPU in seconds |
| Look up a burst or a boundary | the burst catalog `$PONZI_HOME/catalog/bursts.sqlite3`, the boundaries `$PONZI_HOME/catalog/boundaries.sqlite3` | read only |

A run's outputs are found in the cache by the content ids it prints: `$PONZI_HOME/cache/<collection>/<content id>/`, an `item.json` and the stores beside it. A standard's run makes every store of the chain; its final step is `cells`, the events of each Major TOM tile the burst reaches (`ponzi-events-cell`), and the per-burst events (`ponzi-events`), the run, the p-values and the rest stay beside them.

### Results on the server

A worker you run talks to no server: its outputs stay in this machine's cache, and nothing is published. To have a server hold them, submit the same work through the client (`ponzi-client submit` with the same standard, bursts and dates; check with `ponzi-client standards` that the server holds the standard you ran, with the same key and `workflow_hash`). The server's loop, working from the same PONZI home, finds every step cached, computes nothing, and delivers the outputs; bytes the server already holds are not sent again (CR-101). A run on other variables, another standard or another home is computed again.

### Running the server's loop

`ponzi-client serve` is the loop that connects a worker to a server: it claims the server's jobs, has the worker do them and delivers the outputs ([Workflows and the cache](../../service/worker.md), [Running on the cluster](../../service/hpc.md)). Start or stop it only when the owner asks: it acts for the server, not for you.

## Rules

They hold whichever tool you use.

- **Work in the PONZI home and a scratch folder.** Read and write a server's storage only through its API. Do not edit the files of ponzi-suite (specs, standards, test cases) to make a run go; a run needs a standard or a workflow of existing stages, and specs are not composed by hand for it.
- **The cluster and data transfers need the owner's approval:** `--executor slurm` without `--dry-run`, `sbatch`, `rsync` ([Cluster approvals](#cluster-approvals)). Work a server's worker submits for a watched area or a request needs none (CR-062).
- **Downloads count against the owner's quotas.** `acquire` and the weather are large: say how many acquisitions a run will fetch before starting it, and use `--dry-run` first.
- **The registry is the owner's.** Do not train, export or register models, register standards, or file calibrations unless the owner asks: every later run reads them.
- **Code changes go through a change request** ([Changing the code](contributing.md)). Running PONZI changes no code.
- **Identify results by content id**, not by path: paths differ between installations.
- **Search before submitting.** An identical request costs nothing the second time, but it is still a request.
- **Report a failure** with the job id or the batch id, and the `Problem` body the server returned or the worker's error.

### Cluster approvals

The owner can approve SLURM work and data transfers in bulk: one approval may cover many submissions or `rsync` runs, such as every batch of one workflow over a list of bursts, copying every store of a campaign to the cluster, or the whole of a roadmap item.

- **Ask with a dry run.** Show what the approval would cover: for SLURM, `--dry-run` (the workflow or standard, the bursts or areas, the span, how many jobs and what resources); for a transfer, `rsync --dry-run` (the source, the destination, how many files and how much data).
- **The approval names its scope.** It says what it covers, and any cap (jobs, GPU hours, a partition, data volume). Within that scope, submit or transfer without asking again; anything outside it needs a new approval.
- **It lasts until its work is done**, or until the owner withdraws it. It does not carry over to other work.
- **Report what you did:** the batches, their job ids and how far each got (`ponzi-worker batch`), and what each transfer moved.

## Reading what PONZI makes

Every store PONZI makes has a written contract ([Store formats (contracts)](../../reference/contracts.md)): its arrays or columns, dtypes, fill values, chunks, attrs and invariants, and the functions that open, write and validate it. Read the contract before you read a store's arrays, so you know what a value means and which value means "no data". The code is the authority: where a contract and the code disagree, the code is right, and the contract is the one to fix.

| You have | Read | Open it with |
| --- | --- | --- |
| a delivered output (`ponzi-events-cell`), or a burst's events (`ponzi-events`, in the cache): the `events` asset | [events_store](../../reference/contracts/events_store.md) (C25) | `ponzi.contracts.events.open_events_store`, or any Zarr reader |
| a burst's coherence (`ponzi-coherence`, `coh`, `engine_report`) | [coherence_store](../../reference/contracts/coherence_store.md) (C1), [engine_report](../../reference/contracts/engine_report.md) (C18) | `ponzi.contracts.coherence.open_coherence_store`, `ponzi.contracts.validate.read_engine_report` |
| a burst's covariates or masks (`ponzi-sidecar`, `ponzi-masks`) | [covariates_sidecar](../../reference/contracts/covariates_sidecar.md) (C2), [mask_store](../../reference/contracts/mask_store.md) (C23) | `open_coherence_store(path, sidecar=...)`, `ponzi.contracts.masks.open_mask_store` |
| a run's outputs (`ponzi-run`: `score`, `change`, `run_meta`, ...) | [score_store](../../reference/contracts/score_store.md) (C7), [change_store](../../reference/contracts/change_store.md) (C8), [run_meta](../../reference/contracts/run_meta.md) (C9), and the optional stores C5, C6, C21, C24, C26 | `ponzi.contracts.score.open_score_store`, `ponzi.contracts.change.open_change_store`, `ponzi.contracts.run_meta.read_run_meta` |
| p-values (`ponzi-pvalues`) | [pvalue_store](../../reference/contracts/pvalue_store.md) (C22) | `ponzi.contracts.pvalues.open_pvalue_store` |
| a scoring spec, or a run's request | [scoring_spec](../../reference/contracts/scoring_spec.md) (C4), [run_request](../../reference/contracts/run_request.md) (C4a) | `ponzi.core.scoring_spec.load_scoring_spec` |

The [STAC catalog profile](../../using/stac-profile.md) lists the contract of every Collection. A fetched store is read the same way as one in the cache: the contract describes the file, wherever it came from.
