# Using PONZI (agents)

How to use the PONZI repositories to get results and understand them: which mode you are in, what you can do in each, and how to read what PONZI makes (its stores, described by their contracts). For changing the code, see [Contributing](contributing.md).

## Two modes

Which one applies depends on whether a PONZI server is running for you:

| | Client mode | Local mode |
| --- | --- | --- |
| **When** | a server is running and you have its URL and a key | no server: PONZI is installed on this machine (a checkout of ponzi-core, and of ponzi-service for the worker) |
| **Through** | `ponzi-client`, the Python package or its command line | the commands of ponzi-core (`ponzi`, `ponzi-pipeline`, `ponzi-models`) and `ponzi-worker run` |
| **Results land** | on the server, found by search | in this machine's PONZI home (`$PONZI_HOME/cache`, [Paths](../../getting-started/paths.md)) |

Check first: `ponzi-client standards` answers in client mode; a connection error or no `server.url` means there is no server. When a server is running, use client mode, even on the server's own machine.

## Client mode

`ponzi-client` is a REST client, so it needs a running server: `--url` or `server.url` of `ponzi.yaml`, and a key in `PONZI_KEY` or the file `$PONZI_KEY_FILE` ([Authentication](../../getting-started/authentication.md)). In this mode:

- Do not import `ponzi`, `ponzi_pipeline` or `ponzi_models`; the server's workers compute.
- Do not read or write the server's storage or a worker's cache directly (both are in a PONZI home).
- Do not submit cluster jobs. Those are the worker's job, behind the server.

### What you can do

| Task | Client call (Python) | Command | Notes |
| --- | --- | --- | --- |
| Find bursts over an area | `c.bursts(bbox=...)` | `ponzi-client bursts --bbox ...` | burst ids look like `t028_058198_iw3` |
| See what can be run | `c.standards()` | `ponzi-client standards` | a standard id has a version: `s1-general@2.0.0` |
| Watch an area | `c.majortom_cells(bbox=...)`, then `c.create_area(cells=[...], tags=[...])` | `ponzi-client area-create --cells C[,C] --tags T[,T]` | needs a `client:write` key; 1 to 64 tiles over land; the standard is optional (the server's); see [Watched areas](../../using/watched-areas.md) |
| Pause or change a watched area | `c.update_area(area_id, active=False)` | `ponzi-client area-update ID --active false` | fields left out stay as they are |
| Find the outputs of tagged areas | `c.search(tags=[...])` | `ponzi-client search --tags T[,T]` | analysis Items only ([Tags](../../using/watched-areas.md#tags)) |
| Look at an area now | `c.discover_area(area_id)` | `ponzi-client area-discover ID` | whatever its cadence |
| Run once | `c.submit(burst_ids=[...], standard=...)` | `ponzi-client submit ...` | returns existing results when they exist (`reused: true`) |
| Follow a run | `c.request(request_id)`, `c.jobs(request_id=...)` | `ponzi-client request ID` | a done job lists the Items it made (`items`) |
| Find results | `c.search(collections=["ponzi-events-cell"], bbox=..., datetime=...)` | `ponzi-client search ...` | Items of the [STAC profile](../../using/stac-profile.md) |
| Explain a result | `c.manifest(content_id)` | `ponzi-client manifest CID --yaml` | the provenance, see [Manifests](../../using/manifests.md) |
| Fetch a result's file | `c.download(item, "events", "out/")` | `ponzi-client download COLLECTION ID events out/` | a zipped store comes back unpacked |

## Local mode

With no server, PONZI runs on this machine from its own commands. Use a standard's workflow rather than calling the stages one by one where you can: it computes what a server's worker would, with the same content ids, in the local cache.

| Task | Command | Notes |
| --- | --- | --- |
| See the stages | `ponzi-worker stages` | the stages installed, with their inputs and params |
| Run a workflow on bursts | `ponzi-worker run WORKFLOW.yaml --each burst=t028_058198_iw3,... --set start_date=... --set end_date=...` | locally by default; a standard's workflow comes from `ponzi-models standard-workflow`; outputs are cached by content id, so a second run reuses them |
| Try it without computing | `ponzi-worker run WORKFLOW.yaml ... --dry-run` | the jobs and which are already cached |
| Explain a result | `ponzi-worker manifest CONTENT_ID --json` | the provenance from the local cache |
| One step of the data chain | `ponzi-pipeline discover`, `acquire`, `dem`, `coherence`, `assemble`, `onboard` | `ponzi-pipeline` with no argument lists them; `acquire` needs Earthdata ([Authentication](../../getting-started/authentication.md)) |
| A forecast run on a store | `ponzi run ...` | needs a scoring spec of a registered model (`--scoring-spec`); `ponzi --help` lists the commands |
| Check or rehearse a standard | `ponzi-models check-standard FILE`, `ponzi-models rehearse --out DIR` | the rehearsal is synthetic and runs on the CPU in seconds |
| Look up a burst or a boundary | the burst catalog `$PONZI_HOME/catalog/bursts.sqlite3`, the boundaries `$PONZI_HOME/catalog/boundaries.sqlite3` | read only |

In local mode:

- Work only in this machine's PONZI home and in a scratch folder; do not edit the files of ponzi-suite (specs, standards) to make a run go.
- Do not use `--executor slurm` or `sbatch` yourself: an agent submits cluster work only by asking for it through a server in client mode, or with the owner's approval.
- Do not train, export or register models, or file calibrations, unless the owner asks: they change the registry every later run reads.
- Downloads (`acquire`, the weather) are large and count against the owner's quotas: say how many acquisitions a run will fetch before starting it, and use `--dry-run` first.

## Reading what PONZI makes

Every store PONZI makes has a written contract ([Store contracts](../../reference/contracts.md)): its arrays or columns, dtypes, fill values, chunks, attrs and invariants, and the functions that open, write and validate it. Read the contract before you read a store's arrays, so you know what a value means and which value means "no data". The code is the authority: where a contract and the code disagree, the code is right, and the contract is the one to fix.

| You have | Read | Open it with |
| --- | --- | --- |
| a delivered output (`ponzi-events-cell`, `events` asset) | [events_store](../../reference/contracts/events_store.md) (C25) | `ponzi.contracts.events.open_events_store`, or any Zarr reader |
| a burst's coherence (`ponzi-coherence`, `coh`, `engine_report`) | [coherence_store](../../reference/contracts/coherence_store.md) (C1), [engine_report](../../reference/contracts/engine_report.md) (C18) | `ponzi.contracts.coherence.open_coherence_store`, `ponzi.contracts.validate.read_engine_report` |
| a burst's covariates or masks (`ponzi-sidecar`, `ponzi-masks`) | [covariates_sidecar](../../reference/contracts/covariates_sidecar.md) (C2), [mask_store](../../reference/contracts/mask_store.md) (C23) | `open_coherence_store(path, sidecar=...)`, `ponzi.contracts.masks.open_mask_store` |
| a run's outputs (`ponzi-run`: `score`, `change`, `run_meta`, ...) | [score_store](../../reference/contracts/score_store.md) (C7), [change_store](../../reference/contracts/change_store.md) (C8), [run_meta](../../reference/contracts/run_meta.md) (C9), and the optional stores C5, C6, C21, C24, C26 | `ponzi.contracts.score.open_score_store`, `ponzi.contracts.change.open_change_store`, `ponzi.contracts.run_meta.read_run_meta` |
| p-values (`ponzi-pvalues`) | [pvalue_store](../../reference/contracts/pvalue_store.md) (C22) | `ponzi.contracts.pvalues.open_pvalue_store` |
| a scoring spec, or a run's request | [scoring_spec](../../reference/contracts/scoring_spec.md) (C4), [run_request](../../reference/contracts/run_request.md) (C4a) | `ponzi.core.scoring_spec.load_scoring_spec` |

The [STAC profile](../../using/stac-profile.md) lists the contract of every Collection. To check that a store meets its contract: `ponzi validate-store PATH` (local mode; `--json` for a machine-readable report). In client mode, a fetched store is read the same way: the contract describes the file, wherever it came from.

## Rules of thumb

- Identify results by content id, not by path; paths differ between installations.
- Before submitting, search: an identical request costs nothing the second time, but it is still a request.
- A run needs a standard; do not compose configs yourself (in either mode).
- Report a failure with the job id and the `Problem` body the server returned.
