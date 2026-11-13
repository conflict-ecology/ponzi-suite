# System overview

## The data chain

```
Sentinel-1 SLCs (ASF)
  → pair coherence per burst (ISCE3)            ponzi-pipeline
  → coherence store per burst (Zarr)            ponzi-pipeline
  → covariates sidecar (weather, built-up)      ponzi-pipeline
  → forecast run: scores and changes            ponzi
  → p-values under a calibration                ponzi
  → dated events under a detection spec         ponzi
```

Models and calibrations are made by `ponzi-models` from panels: sets of pixels of many bursts, run through the same chain.

!!! note "TiDE is the default forecaster, not a requirement"
    The forecast step is replaceable. TiDE (Time-series Dense Encoder, [Das et al., 2023](../reference/references.md#forecasting)) is the default today: the draft standard `s1-general` runs a TiDE model, a neural network trained on panels and run as TorchScript. Nothing else in PONZI depends on it. Forecasters are registered by name (`ponzi.core.forecast.registry`): today `tide`, the rolling fit `rolling_ols`, which needs no training, and `stored` and `external`, which read predictions made elsewhere. A new forecaster is one module and one `register` call; the scoring spec, the scoring, the calibration and the detection do not change, and a standard names whichever model it runs ([Training and calibrating a model](../models/new-model.md)).

## The components

Who calls whom while PONZI runs, and which distribution depends on which. Solid arrows are package dependencies (`pyproject.toml`), dashed ones calls at run time, dotted ones files read by path. What a distribution gets through another is not drawn again: `ponzi-models` also declares `ponzi` and `ponzi-spec`, and `ponzi-worker` all of the computing distributions.

<div class="pz-figure" markdown="0">
<svg viewBox="0 0 830 720" role="img" aria-label="The dependencies of the PONZI distributions: ponzi-spec at the base; ponzi on it, ponzi-pipeline on ponzi, ponzi-models on ponzi-pipeline; ponzi-worker depends on ponzi-models; ponzi-server and ponzi-client depend only on ponzi-spec; ponzi-client calls the server over REST and runs ponzi-worker sweep or job; ponzi-visual calls the server over REST; agents and scripts call ponzi-client, or run ponzi-worker directly with no server; ponzi-models reads the specs and standards of ponzi-suite by path">
<defs><marker id="pz-dep" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path class="pz-head" d="M0,0 L10,5 L0,10 z"/></marker></defs>
<rect class="pz-box" x="610" y="6" width="170" height="44" rx="7"/>
<text class="pz-title" x="622" y="25">agents, scripts</text>
<text class="pz-small" x="622" y="41">Python or the command line</text>
<path class="pz-dep-rest" d="M695,50 L695,108"/>
<text class="pz-small" x="705" y="83">call</text>
<path class="pz-dep-rest" d="M610,28 L570,28 L570,245 L608,245"/>
<text class="pz-small" x="562" y="208" text-anchor="end">ponzi-worker run, no server</text>
<text class="pz-small" x="562" y="221" text-anchor="end">(SLURM only with approval)</text>
<g transform="translate(0,70)">
<path class="pz-dep-rest" d="M190,65 L313,65"/>
<text class="pz-small" x="252" y="58" text-anchor="middle">REST</text>
<text class="pz-small" x="252" y="80" text-anchor="middle">openapi.json types</text>
<path class="pz-dep-rest" d="M610,65 L487,65"/>
<text class="pz-small" x="548" y="58" text-anchor="middle">REST</text>
<path class="pz-dep-rest" d="M695,90 L695,148"/>
<text class="pz-small" x="705" y="116">runs</text>
<text class="pz-small" x="705" y="129">ponzi-worker</text>
<text class="pz-small" x="705" y="142">sweep or job</text>
<path class="pz-dep-line" d="M695,200 L695,258"/>
<path class="pz-dep-file" d="M610,285 L572,285"/>
<path class="pz-dep-line" d="M695,310 L695,368"/>
<path class="pz-dep-line" d="M695,420 L695,478"/>
<path class="pz-dep-line" d="M695,530 L695,588"/>
<path class="pz-dep-line" d="M400,90 L400,588"/>
<path class="pz-dep-line" d="M780,65 L805,65 L805,588"/>
<rect class="pz-dep-vis" x="20" y="40" width="170" height="50" rx="7"/>
<text class="pz-title" x="32" y="61">ponzi-visual</text>
<text class="pz-small" x="32" y="78">map front end, TypeScript</text>
<rect class="pz-dep-svc" x="315" y="40" width="170" height="50" rx="7"/>
<text class="pz-title" x="327" y="61">ponzi-server</text>
<text class="pz-small" x="327" y="78">areas, jobs, final outputs</text>
<rect class="pz-dep-svc" x="610" y="40" width="170" height="50" rx="7"/>
<text class="pz-title" x="622" y="61">ponzi-client</text>
<text class="pz-small" x="622" y="78">serve: the long-running loop</text>
<rect class="pz-dep-svc" x="610" y="150" width="170" height="50" rx="7"/>
<text class="pz-title" x="622" y="171">ponzi-worker</text>
<text class="pz-small" x="622" y="188">one short call per step</text>
<rect class="pz-dep-suite" x="420" y="260" width="150" height="50" rx="7"/>
<text class="pz-title" x="432" y="281">ponzi-suite</text>
<text class="pz-small" x="432" y="298">specs, standards</text>
<rect class="pz-dep-core" x="610" y="260" width="170" height="50" rx="7"/>
<text class="pz-title" x="622" y="281">ponzi-models</text>
<text class="pz-small" x="622" y="298">panels, training, registry</text>
<rect class="pz-dep-core" x="610" y="370" width="170" height="50" rx="7"/>
<text class="pz-title" x="622" y="391">ponzi-pipeline</text>
<text class="pz-small" x="622" y="408">coherence chain, onboard</text>
<rect class="pz-dep-core" x="610" y="480" width="170" height="50" rx="7"/>
<text class="pz-title" x="622" y="501">ponzi</text>
<text class="pz-small" x="622" y="518">forecast, score, detect</text>
<rect class="pz-dep-core" x="20" y="590" width="795" height="44" rx="7"/>
<text class="pz-title" x="34" y="610">ponzi-spec</text>
<text class="pz-small" x="34" y="626">the shared schemas every Python part depends on: REST models, STAC, content ids, manifests, stages, the PONZI home, naming (pydantic and PyYAML only)</text>
<rect class="pz-dep-core" x="20" y="260" width="34" height="12" rx="3"/>
<text class="pz-small" x="62" y="270">ponzi-core</text>
<rect class="pz-dep-svc" x="20" y="282" width="34" height="12" rx="3"/>
<text class="pz-small" x="62" y="292">ponzi-service</text>
<rect class="pz-dep-vis" x="20" y="304" width="34" height="12" rx="3"/>
<text class="pz-small" x="62" y="314">ponzi-visual</text>
<rect class="pz-dep-suite" x="20" y="326" width="34" height="12" rx="3"/>
<text class="pz-small" x="62" y="336">ponzi-suite</text>
<path class="pz-dep-line" d="M20,354 L54,354"/>
<text class="pz-small" x="62" y="358">depends on</text>
<path class="pz-dep-rest" d="M20,376 L54,376"/>
<text class="pz-small" x="62" y="380">calls at run time</text>
<path class="pz-dep-file" d="M20,398 L54,398"/>
<text class="pz-small" x="62" y="402">reads files by path</text>
<rect class="pz-box" x="20" y="414" width="34" height="12" rx="3"/>
<text class="pz-small" x="62" y="424">outside PONZI</text>
</g>
</svg>
</div>

- **ponzi-server** holds requests, watched areas, jobs and the final outputs, and serves the catalog. It depends only on `ponzi-spec` and never imports the computing distributions, and it never calls a client or a worker: the clients always ask.
- **ponzi-client** (Python, and the `ponzi-client` command) is the way to a running server: submitting runs, watching areas, reading outputs. As `ponzi-client serve` it is the one long-running process: it claims jobs, has the worker do them and deliver the final outputs (uploaded, or written into a folder the server also sees; CR-098), and completes them (CR-063).
- **ponzi-worker** never stays running, and talks to the server only to upload a job's outputs with the one-time tickets the loop hands it (CR-098). With a SLURM worker the loop calls `ponzi-worker sweep`, one short call over every job it holds that checks the work in flight and submits the new work (CR-096), then `ponzi-worker package` for each job that is ready; with a local worker, `ponzi-worker job` runs one job here to the end. It keeps intermediate outputs in its own cache by content id, so each call goes on from where the last stopped. It is the only part that depends on the computing distributions.
- **ponzi-visual** talks to the server directly over REST and depends on no PONZI package: its TypeScript client is generated from the server's committed `openapi.json` (`npm run gen`). It shows the watched areas and their outputs over time on a map, and makes new areas from Major TOM tiles (with their tags) over a span of days; the server chooses what runs them.
- **ponzi-spec** is the one distribution every Python part depends on. It holds no computing code, so the server and the clients install it without the scientific stack.
- **Without a server**, code uses the ponzi-core libraries and their commands directly (`ponzi run`, `ponzi-pipeline`, `ponzi-models`), or a worker on its own (`ponzi-worker run` runs a workflow on this machine or through SLURM, with its cache). An agent submits to SLURM this way only with the owner's approval ([Using PONZI](../contributing/agents/usage.md#the-worker-running-workflows-yourself)).
- **Optional parts:** `ponzi[tide]` and `ponzi-models[train]` add torch (the `ml` environment on the CPU; `ml-gpu`, conda-forge torch in its CUDA 12.9 build); ISCE3 comes from conda-forge only, in the `isce3` environment, as version 0.25.22 in its CUDA 12.9 build ([Install](install.md)).

## What holds it together

- Every artifact that crosses a component boundary is a STAC Item in a known Collection: the [STAC catalog profile](../using/stac-profile.md).
- Every Item has a [content id](../using/content-ids.md) computed before the work runs, so repeated requests reuse what exists.
- Every final output has a [manifest](../using/manifests.md) that traces it back to the satellite scenes.
- Every unit of work is a [stage](../method/stages.md) with declared inputs, params and outputs, so it can be replaced.
