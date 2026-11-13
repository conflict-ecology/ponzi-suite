# CR-101: one growing series per tile, each acquisition sent as an update, and series a loop offers the server

- **Requested by / date:** owner, 2026-11-13 ("say for a tile derived from a set of bursts, each new acquisition should not reupload the entire time series. it should add in the next step in the analysis"; "draft as 101. fold in ability for client to search current final output tile store to offer to server with required meta data for server to create job"; earlier: "can a sweep by client-worker also find outputs and send that to the server?")
- **Status:** draft
- **Builds on:** CR-021 (staged runs; its decision D6: "B is the target: one growing store per burst, appended per update, where a superseded value is marked as such ... B gets its own change request": this is that request), CR-030 (the Major TOM grid, `detect_path`), CR-090 (a standard run locally has a server job's content ids), CR-096 (the sweep), CR-098 (outputs straight to the server), CR-100 (the tiles are the only upload).
- **Replaces:** the earlier draft of CR-101 (offer records written by `ponzi-worker run`): a series store carries what an offer needs, so no separate record is kept.

## Why
A watched area's job is one burst with `end_date` = the day of the tick. Each new acquisition (every 12 days per track):

| step | today |
|---|---|
| coherence pairs | incremental: only the new pairs |
| coherence store, sidecar | made again over the whole span |
| `run` | the whole span scored again (the standard's `run` step names no dates, so every anchor from `start_date`) |
| p-values, events, cells | made again in full, new content ids |
| delivery | every cell's whole `(T, Y, X)` events store, zipped, uploaded |

The cost grows with the series. Yet one acquisition changes only the tail: the newest anchor at stage 1, the one before at stage 2, up to anchor T - H at its final stage; Et and the dating reach four anchors further back; detection can only extend, merge, date or withdraw the flag runs at the end. Every older anchor is final. Nothing in the chain is a statistic over the whole series (checked 2026-11-13: the weather sidecar is a spatial mean per acquisition, `onboard.weather.cell_mean`; the model's input scaling is fitted at training, `forecast.model_inputs`; the context length C is fixed), so appending the tail gives the full run's numbers.

Three more things follow from the same layout:
- A job is named by the tick's day, so the jobs of days without a new acquisition are distinct jobs whose outputs are identical; each is packaged and uploaded again, and the server drops the duplicate Items (`jobs.complete`).
- The delivered output is one Item per burst per cell: where a path's bursts overlap in a tile, a tile has several Items and no product of the path. `detect_path` mosaics bursts, but no job has more than one burst.
- A run made without the server (an agent's, a person's `ponzi-worker run`) reaches it only if someone submits a request with exactly its dates; a cache entry cannot say which job it was, because one output is the output of every job between two acquisitions.

## What changes

### 1. The burst series (CR-021 D6, option B)
- **Updates are cache entries; the series is their sum.** A burst's run is a chain of updates. Update k is a cache entry (`ponzi-series-update`) whose content id is that of (update k - 1, the new acquisitions, the run params): the same chain gives the same ids, so the cache, eviction and manifests work as today. It holds only what update k writes: the anchors scored at a new stage, the anchors made final, the Et summary of its anchors, and the carried state (below).
- **The series store** is the chain applied in order, kept at `$PONZI_HOME/series/<standard key>/burst/<burst id>.zarr` (warm tier, CR-099). It can be made again from the chain at any time; it is never a cache entry. Its attrs: the standard key and `workflow_hash`, the burst, `start_date`, the chain (each update's content id and its newest acquisition), `updates`.
- **`run --append`** (ponzi): scores only the anchors the new acquisitions reach (a trailing window of H anchors plus the context, CR-021 item 5), against the series' existing anchors. A staged value is never overwritten in place: the store keeps per anchor the stage it holds and the update that wrote it, and a replaced value's stage and update (`replaced_by`), as D6 asked. `--write-all-stages` keeps every stage (analysis).
- **The coherence store and sidecar** are appended the same way: the new acquisition's pairs and its weather rows.

### 2. Detection with carried state
- `detect --append` and `detect_path --append`: detect over the tail only, starting from the carried state of the update before: open flag runs and their gaps, the episode counter, `first_t`, `n_events`, the Et of the anchors the dating window reads. The state is written into the update.
- Event rows: an event whose run ends inside the tail may change (extended, merged, re-dated, withdrawn). Each row gets `event_update` (the update that last wrote it); a replaced row is kept with `replaced_by`. Older rows never change.

### 3. The tile series
- **One product per tile and track.** `ponzi-tile-series`: the events of one Major TOM cell for one relative orbit and direction, the path's bursts mosaicked on the cell's lattice (`detect_path`, the `overlap` rule, `max` by default), kept as a series like a burst's, at `$PONZI_HOME/series/<standard key>/tile/<cell>_<orbit><A|D>.zarr`. Its attrs: the standard key and `workflow_hash`, the cell, orbit and direction, the bursts, `start_date`, the chain of tile updates (each naming the burst updates it read), the newest acquisition.
- **A tile update** is a cache entry (`ponzi-tile-update`) made from the burst updates of one acquisition date of the track; its content id is that of (the previous tile update, those burst updates, the detection params).

### 4. Store layout (contract changes)
- **C25 (events store)**: `state` is chunked `(16, rows, X)` (time chunks) instead of `(T, rows, X)`, so an update touches only the chunks of its tail. Adds `event_update`, `replaced_by` and the series attrs. Contract version changes.
- **C27 (new, the update)**: the arrays an update writes (its anchors only), the carried state, the chain link, and `chunks`: the store chunks it changes and each chunk's sha256.
- **C26 (staged store), C7, C22**: the per-anchor stage and update, for the burst series.

### 5. Jobs named by acquisition, and the server's series
- **A job is named by what it delivers.** A watched area's tick asks the worker for the burst's newest acquisition (`discover`, as today); the burst job's payload names `acquired` (the newest acquisition's date) in place of `end_date`. A tick with nothing new finds the job of that acquisition done and makes nothing. The tile job of (cell, track, acquired) is made when the burst jobs of that track and date are done.
- **The server keeps one series per tile and track and standard**: an Item `ponzi-tile-series` (a stable id: cell, track, standard key) whose `events` asset is the server's copy of the series store, and one Item `ponzi-tile-update` per update (its manifest, its chunk list). The series Item's `ponzi:update` and `datetime` say how far it reaches.
- **Delivery sends the changed chunks only.** Completing a tile job, the loop asks for tickets for the update's chunk list; the server answers `held` for every chunk whose sha256 its copy already has and gives tickets for the rest. It writes the received chunks into a new version of its copy, swaps it in at completion (readers see the old version until then) and keeps the chunks each update replaced, so every earlier version can be read (`GET /v1/series/{id}?update=k`). The same `held` answer applies to any upload: an Item whose content id the server holds is never sent again.

### 6. Offers: a loop sends the server the series made without it
- **The worker lists its tile series.** `ponzi-worker offers -` reads `$PONZI_HOME/series/*/tile/*.zarr` (the current final output) and answers, per series, what the server needs to make its job: the standard key and `workflow_hash`, the cell, orbit and direction, the bursts, `start_date`, the newest acquisition (`acquired`), and the chain (each update's content id). A series made from a workflow that is not a standard's (no standard key in its attrs) is not listed. It computes nothing.
- **The loop offers** (`ponzi-client serve --offer`): each tick, before claiming, it calls `offers -` (through its ssh connection when the worker is remote, CR-098) and posts each series to `POST /v1/offers` with its own key (scope `worker`). Offers and claims together stay within `--max-jobs`; a worker without `offers` is logged once and the loop goes on without offering.
- **The server makes the job from its own standard.** It refuses an offer whose standard it does not hold or whose `workflow_hash` is not its file's (CR-091), or whose cell, track or bursts are not in its catalog. Otherwise it builds the tile job's payload as its scheduler would for (cell, track, `acquired`), from its own standard file, so the job id is the one an area would make, and answers:
  - `known`: the job is done (the server's series already reaches `acquired`);
  - `leased`: the job is new or queued; it is leased to the offering loop at once, with the server's `Outputs`, and delivered as any job: the sweep finds it cached and answers `ready`, `package` lists the chain's updates after the server's newest, and only their changed chunks are sent. A series the server does not hold is sent whole once;
  - `held`: another loop holds it; offered again next tick;
  - `diverged`: the server's series has an update for that cell and track whose content id is not in the offered chain (made from other acquisitions); refused, and logged with both chains.
- The job records `origin: "offer"` (else `request` or `area`), and the loop and the `--by` of the run that made the series. Tags come as for every analysis Item (CR-067).
- **Opt-in on both sides**: the server's settings `offers: {accept: true}` (else 403) and the loop's `--offer`.

### 7. What stays
- `ponzi-events-cell` and `detect`/`tile` of a whole run stay for detection mode, for one-off requests and for analysis; CR-100 holds for them.
- The cache, content ids, manifests and eviction work as today: an update is an entry like any other.

### Docs
Contracts C25, C26, C27 (new), C7, C22; `method/workflows.md` (series and updates); `service/worker.md` (series, `offers`); `service/server.md` (series, updates, held chunks, offers, the setting); `using/clients.md` (`--offer`); the API reference; ponzi-visual reads `ponzi-tile-series` (its own change).

## Do results change?
Not if the parity holds, and the parity is the condition of this change: a series appended update by update, from any start, must equal, bit for bit, the full run of the same span (the same scores, p-values, events and per-pixel arrays at every anchor, final and staged), and a tile series must equal `detect_path` of the burst runs on the cell's lattice. A difference found is RESULTS-CHANGING and stops the change.

## Tests
- **Parity** (ponzi): a synthetic series appended one acquisition at a time, from three starting lengths, against the full run; with gaps, with an event crossing an update boundary, with a provisional flag withdrawn at the final stage, with episodes. The same for `detect_path --append` against `detect_path`.
- **The chain** (ponzi-worker): the same acquisitions give the same update ids; the series store made again from the chain equals the one kept; eviction of an update leaves the series readable and the update reproducible.
- **Jobs** (ponzi-server): a tick with no new acquisition makes no job; a new one makes one burst job per burst and one tile job per (cell, track) when the track's burst jobs are done.
- **Delivery**: a second update sends only its tail chunks (counted); `held` chunks are not sent; the server's previous version is readable during and after; `?update=k` returns version k.
- **Offers**: `offers -` lists only standard series; an offer makes the job an area would (same id); `known`, `leased`, `held`, `diverged`; refused for an unknown standard, another `workflow_hash`, an unknown cell, and when `offers.accept` is false. End to end on the rehearsal: a local run of the server's standard, then `serve --offer --once` against the same home: the job is made and leased, completes with nothing computed, the server's series reaches `acquired`; offered again: `known`, nothing sent.
- **Watched areas** (`test_watched.py`): a new acquisition computes its new pairs, one update per burst and per tile, and sends only the tail chunks.

## Decisions for the owner
- **D1. Opt-in for offers on both sides** (`offers.accept`, `--offer`), off by default? Recommended: yes.
- **D2. Jobs named by acquisition** (`acquired`) instead of the tick's day? Recommended: yes; it removes the duplicate jobs and is what lets an offer name its job.
- **D3. Time chunk of C25**: 16 anchors (recommended: about H + 8, so an update touches one or two chunks), or 1.
- **D4. The server keeps every version** of a series (the replaced chunks), or the latest only plus the update manifests? Recommended: every version; the replaced chunks are small.
- **D5. What happens to the existing outputs**: series start at the next standard and today's `ponzi-events-cell` Items stay as they are (recommended), or a series is seeded from the newest full run.
- **D6. The standard's workflow changes** (append steps, the tile series step): CR-091 records one workflow per standard key and refuses another. A new key (re-register the standard; recommended, the products change) or a recorded second workflow?
- **D7. Order of work**: (a) `held` uploads and jobs by acquisition (section 5, small, useful at once), (b) the burst series and parity, (c) carried detection and the tile series, (d) chunk delivery and the server's series, (e) offers. Recommended: in that order, each implemented and reviewed on its own.

## Version
`ponzi` major (C25, C26, C7 and C22 change; C27 new; append modes). `ponzi-spec` major (new collections `ponzi-series-update`, `ponzi-tile-update`, `ponzi-tile-series`; `Offer`, `OfferResult`; the job payload's `acquired`; `Job.origin`). `ponzi-pipeline` minor (appended coherence store and sidecar). `ponzi-models` minor (the workflow with series steps). ponzi-server, ponzi-client and ponzi-worker major. Standard: a new key (D6).
