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
    The forecast step is replaceable. TiDE (Time-series Dense Encoder, [Das et al., 2023](../reference/references.md#forecasting)) is the default today: the draft standard `s1-general@2.0.0` runs a TiDE model, a neural network trained on panels and run as TorchScript. Nothing else in PONZI depends on it. Forecasters are registered by name (`ponzi.core.forecast.registry`): today `tide`, the rolling fit `rolling_ols`, which needs no training, and `stored` and `external`, which read predictions made elsewhere. A new forecaster is one module and one `register` call; the scoring spec, the scoring, the calibration and the detection do not change, and a standard names whichever model it runs ([A new model](../models/new-model.md)).

## The components

```
ponzi-visual, agents
        │
        ▼
ponzi-client  ──── REST ────►  ponzi-server
   │    serve: the only long-running process;
   │    it always asks, the server never calls out
   ▼
ponzi-worker job   (one short call per step of a job)
   │
   └── runs ponzi, ponzi-pipeline, ponzi-models,
       here or as SLURM jobs
```

- **ponzi-server** holds requests, watched areas, jobs and the final outputs, and serves the catalog. It never imports the computing distributions.
- **ponzi-client** (Python, and the `ponzi-client` command) is the only part that talks to a running server: submitting runs, watching areas, reading outputs, and, as `ponzi-client serve`, the one long-running loop that claims jobs, has the worker do them, delivers the final outputs (uploaded, or written into a folder the server also sees) and completes them (CR-063).
- **ponzi-worker** never talks to the server and never stays running. `ponzi-worker job` is one short call on one job: it runs the job's workflow here, or submits and checks its SLURM jobs, and answers with what is done; the client calls it again until the job is finished. It keeps intermediate outputs in its own cache by content id, so each call goes on from where the last stopped. Code can also use PONZI without a server: the ponzi-core libraries and their commands directly (`ponzi run`, `ponzi-pipeline`, `ponzi-models`), or a worker on its own (`ponzi-worker run` runs a workflow on this machine or through SLURM, with its cache, and no server).
- **ponzi-visual** shows the watched areas and their outputs over time on a map, and makes new areas from Major TOM tiles (with their tags) over a span of days, and lists the areas monitored. The server chooses what runs them.

## Dependencies

Which distribution needs which: solid arrows are install dependencies (`pyproject.toml`), dashed ones calls over the REST API at run time, dotted ones files read by path. `ponzi-models` and `ponzi-worker` also declare `ponzi` and `ponzi-spec` directly; the chart draws each dependency once.

<div class="pz-figure" markdown="0">
<svg viewBox="0 0 790 500" role="img" aria-label="The dependencies of the PONZI distributions: ponzi-spec at the base; ponzi, ponzi-pipeline and ponzi-models the computing toolkit; ponzi-worker installs them; ponzi-server and ponzi-client install ponzi-spec only; ponzi-client calls the server over REST and runs ponzi-worker job; ponzi-visual calls the server over REST">
<defs><marker id="pz-dep" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path class="pz-head" d="M0,0 L10,5 L0,10 z"/></marker></defs>
<path class="pz-dep-line" d="M390,90 L390,158"/>
<path class="pz-dep-line" d="M330,90 C330,180 230,190 210,258"/>
<path class="pz-dep-line" d="M480,72 C540,90 560,140 600,158"/>
<path class="pz-dep-line" d="M330,210 C300,230 250,235 230,258"/>
<path class="pz-dep-line" d="M430,210 L430,348"/>
<path class="pz-dep-line" d="M260,310 C280,330 300,330 320,348"/>
<path class="pz-dep-line" d="M390,400 L390,438"/>
<path class="pz-dep-line" d="M675,210 L675,438"/>
<path class="pz-dep-line" d="M760,65 L775,65 L775,438"/>
<path class="pz-dep-rest" d="M640,158 L640,92"/>
<text class="pz-small" x="646" y="130">REST</text>
<path class="pz-dep-rest" d="M588,200 C540,230 530,110 482,80"/>
<text class="pz-small" x="534" y="120" text-anchor="middle">runs</text>
<text class="pz-small" x="534" y="133" text-anchor="middle">job</text>
<path class="pz-dep-rest" d="M100,40 L100,18 L675,18 L675,38"/>
<text class="pz-small" x="390" y="13" text-anchor="middle">REST, typed from the server's openapi.json</text>
<path class="pz-dep-file" d="M300,185 L182,185"/>
<text class="pz-small" x="241" y="179" text-anchor="middle">files by path</text>
<rect class="pz-dep-vis" x="20" y="40" width="160" height="50" rx="7"/>
<text class="pz-title" x="32" y="61">ponzi-visual</text>
<text class="pz-small" x="32" y="78">map front end, TypeScript</text>
<rect class="pz-dep-svc" x="300" y="40" width="180" height="50" rx="7"/>
<text class="pz-title" x="312" y="61">ponzi-worker</text>
<text class="pz-small" x="312" y="78">runs the stages</text>
<rect class="pz-dep-svc" x="590" y="40" width="170" height="50" rx="7"/>
<text class="pz-title" x="602" y="61">ponzi-server</text>
<text class="pz-small" x="602" y="78">REST API, final outputs</text>
<rect class="pz-dep-svc" x="590" y="160" width="170" height="50" rx="7"/>
<text class="pz-title" x="602" y="181">ponzi-client</text>
<text class="pz-small" x="602" y="198">Python client, httpx</text>
<rect class="pz-dep-core" x="300" y="160" width="180" height="50" rx="7"/>
<text class="pz-title" x="312" y="181">ponzi-models</text>
<text class="pz-small" x="312" y="198">panels, training, registry</text>
<rect class="pz-dep-suite" x="20" y="160" width="160" height="50" rx="7"/>
<text class="pz-title" x="32" y="181">ponzi-suite</text>
<text class="pz-small" x="32" y="198">panels, forecasters, configs</text>
<rect class="pz-dep-core" x="110" y="260" width="180" height="50" rx="7"/>
<text class="pz-title" x="122" y="281">ponzi-pipeline</text>
<text class="pz-small" x="122" y="298">acquisition, ISCE3, onboard</text>
<rect class="pz-dep-core" x="300" y="350" width="180" height="50" rx="7"/>
<text class="pz-title" x="312" y="371">ponzi</text>
<text class="pz-small" x="312" y="388">the algorithm</text>
<rect class="pz-dep-core" x="20" y="440" width="757" height="44" rx="7"/>
<text class="pz-title" x="34" y="460">ponzi-spec</text>
<text class="pz-small" x="34" y="476">the shared schemas every Python part installs: REST models, STAC, content ids, manifests, stages, home, naming (pydantic, PyYAML only)</text>
<rect class="pz-dep-core" x="560" y="280" width="16" height="12" rx="3"/>
<text class="pz-small" x="584" y="290">ponzi-core</text>
<rect class="pz-dep-svc" x="560" y="300" width="16" height="12" rx="3"/>
<text class="pz-small" x="584" y="310">ponzi-service</text>
<rect class="pz-dep-vis" x="560" y="320" width="16" height="12" rx="3"/>
<text class="pz-small" x="584" y="330">ponzi-visual</text>
<rect class="pz-dep-suite" x="560" y="340" width="16" height="12" rx="3"/>
<text class="pz-small" x="584" y="350">ponzi-suite</text>
<path class="pz-dep-line" d="M560,366 L576,366"/>
<text class="pz-small" x="584" y="370">installs</text>
<path class="pz-dep-rest" d="M560,386 L576,386"/>
<text class="pz-small" x="584" y="390">calls at run time</text>
<path class="pz-dep-file" d="M560,406 L576,406"/>
<text class="pz-small" x="584" y="410">reads files by path</text>
</svg>
</div>

- `ponzi-spec` is the one distribution every other part depends on, and it holds no computing code, so the server and the clients install it without the scientific stack.
- Only the worker installs the computing distributions; the server never imports `ponzi`, `ponzi-pipeline` or `ponzi-models`.
- ponzi-visual installs nothing of PONZI: its client is generated from the server's committed OpenAPI document (`npm run gen`).
- Optional parts: `ponzi[tide]` and `ponzi-models[train]` add torch (the `ml` environment on the CPU; `ml-gpu`, conda-forge torch in its CUDA 12.9 build); ISCE3 comes from conda-forge only, in the `isce3` environment, as version 0.25.22 in its CUDA 12.9 build ([Install](install.md)).

## What holds it together

- Every artifact that crosses a component boundary is a STAC Item in a known Collection: the [STAC profile](../using/stac-profile.md).
- Every Item has a [content id](../using/content-ids.md) computed before the work runs, so repeated requests reuse what exists.
- Every final output has a [manifest](../using/manifests.md) that traces it back to the satellite scenes.
- Every unit of work is a [stage](../method/stages.md) with declared inputs, params and outputs, so it can be replaced.
