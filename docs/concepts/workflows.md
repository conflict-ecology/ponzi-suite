---
hide:
  - toc
---

# How PONZI works

The method, where it runs, how its registered pieces are made, and what a change to one of them makes new. Every diagram follows the code as it stands; the [terminology](terminology.md) defines the words.

## The method

<div class="pz-figure" markdown="0">
<svg viewBox="0 0 640 470" role="img" aria-label="The PONZI method: the context of 30 acquisitions, the block of 25 pairs ending on t to t+4 with the 15-pair pyramid that spans the gap before t, then forecast, score, calibrate and detect">
<defs><marker id="pz-head" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path class="pz-head" d="M0,0 L10,5 L0,10 z"/></marker></defs>
<text class="pz-title" x="20" y="22">The coherence of one pixel: pairs ending on each acquisition</text>
<rect class="pz-ctx" x="66" y="60" width="118" height="150" rx="4"/>
<text x="125" y="120" text-anchor="middle">context</text>
<text class="pz-small" x="125" y="136" text-anchor="middle">30 acquisitions</text>
<text class="pz-small" x="125" y="150" text-anchor="middle">before t</text>
<text class="pz-small" x="58" y="77" text-anchor="end">12 d</text>
<rect class="pz-pyr" x="196" y="60" width="40" height="26" rx="3"/>
<rect class="pz-cell" x="240" y="60" width="40" height="26" rx="3"/>
<rect class="pz-cell" x="284" y="60" width="40" height="26" rx="3"/>
<rect class="pz-cell" x="328" y="60" width="40" height="26" rx="3"/>
<rect class="pz-cell" x="372" y="60" width="40" height="26" rx="3"/>
<text class="pz-small" x="58" y="108" text-anchor="end">24 d</text>
<rect class="pz-pyr" x="196" y="91" width="40" height="26" rx="3"/>
<rect class="pz-pyr" x="240" y="91" width="40" height="26" rx="3"/>
<rect class="pz-cell" x="284" y="91" width="40" height="26" rx="3"/>
<rect class="pz-cell" x="328" y="91" width="40" height="26" rx="3"/>
<rect class="pz-cell" x="372" y="91" width="40" height="26" rx="3"/>
<text class="pz-small" x="58" y="139" text-anchor="end">36 d</text>
<rect class="pz-pyr" x="196" y="122" width="40" height="26" rx="3"/>
<rect class="pz-pyr" x="240" y="122" width="40" height="26" rx="3"/>
<rect class="pz-pyr" x="284" y="122" width="40" height="26" rx="3"/>
<rect class="pz-cell" x="328" y="122" width="40" height="26" rx="3"/>
<rect class="pz-cell" x="372" y="122" width="40" height="26" rx="3"/>
<text class="pz-small" x="58" y="170" text-anchor="end">48 d</text>
<rect class="pz-pyr" x="196" y="153" width="40" height="26" rx="3"/>
<rect class="pz-pyr" x="240" y="153" width="40" height="26" rx="3"/>
<rect class="pz-pyr" x="284" y="153" width="40" height="26" rx="3"/>
<rect class="pz-pyr" x="328" y="153" width="40" height="26" rx="3"/>
<rect class="pz-cell" x="372" y="153" width="40" height="26" rx="3"/>
<text class="pz-small" x="58" y="201" text-anchor="end">60 d</text>
<rect class="pz-pyr" x="196" y="184" width="40" height="26" rx="3"/>
<rect class="pz-pyr" x="240" y="184" width="40" height="26" rx="3"/>
<rect class="pz-pyr" x="284" y="184" width="40" height="26" rx="3"/>
<rect class="pz-pyr" x="328" y="184" width="40" height="26" rx="3"/>
<rect class="pz-pyr" x="372" y="184" width="40" height="26" rx="3"/>
<text class="pz-small" x="216.0" y="52" text-anchor="middle">t</text>
<text class="pz-small" x="260.0" y="52" text-anchor="middle">t+1</text>
<text class="pz-small" x="304.0" y="52" text-anchor="middle">t+2</text>
<text class="pz-small" x="348.0" y="52" text-anchor="middle">t+3</text>
<text class="pz-small" x="392.0" y="52" text-anchor="middle">t+4</text>
<line class="pz-gap" x1="193.0" y1="56" x2="193.0" y2="214"/>
<text class="pz-small" x="426" y="74">block t to t+4:</text>
<text class="pz-small" x="426" y="89">25 pairs, 5 baselines</text>
<text class="pz-small" x="426" y="104">by 5 acquisitions</text>
<text class="pz-small" x="426" y="119"></text>
<text class="pz-small" x="426" y="134">filled: the pyramid,</text>
<text class="pz-small" x="426" y="149">the 15 pairs that span</text>
<text class="pz-small" x="426" y="164">the gap before t</text>
<text class="pz-small" x="426" y="179">(dashed line)</text>
<line class="pz-arrow" x1="306.0" y1="218" x2="88.0" y2="258"/>
<rect class="pz-box" x="20" y="262" width="136" height="142" rx="6"/>
<text class="pz-title" x="30" y="284">1 Forecast</text>
<text class="pz-small" x="30" y="306">the forecaster (TiDE,</text>
<text class="pz-small" x="30" y="323">or a rolling fit) gives</text>
<text class="pz-small" x="30" y="340">quantiles of the 25</text>
<text class="pz-small" x="30" y="357">pairs from the context</text>
<text class="pz-small" x="30" y="374">and the covariates</text>
<text class="pz-small" x="88.0" y="422" text-anchor="middle">uses: model + run config</text>
<rect class="pz-box" x="176" y="262" width="136" height="142" rx="6"/>
<text class="pz-title" x="186" y="284">2 Score</text>
<text class="pz-small" x="186" y="306">z: each observed pair</text>
<text class="pz-small" x="186" y="323">against its forecast;</text>
<text class="pz-small" x="186" y="340">anomaly score: mean z</text>
<text class="pz-small" x="186" y="357">over the pyramid;</text>
<text class="pz-small" x="186" y="374">ceiling score</text>
<text class="pz-small" x="244.0" y="422" text-anchor="middle">uses: score.zarr, Et</text>
<line class="pz-arrow" x1="158" y1="333.0" x2="173" y2="333.0"/>
<rect class="pz-box" x="332" y="262" width="136" height="142" rx="6"/>
<text class="pz-title" x="342" y="284">3 Calibrate</text>
<text class="pz-small" x="342" y="306">p: share of the panel</text>
<text class="pz-small" x="342" y="323">null at or above the</text>
<text class="pz-small" x="342" y="340">score; code =</text>
<text class="pz-small" x="342" y="357">round(20 x -log10 p)</text>
<text class="pz-small" x="342" y="374">(plain or ceiling)</text>
<text class="pz-small" x="400.0" y="422" text-anchor="middle">uses: calibration</text>
<line class="pz-arrow" x1="314" y1="333.0" x2="329" y2="333.0"/>
<rect class="pz-box" x="488" y="262" width="136" height="142" rx="6"/>
<text class="pz-title" x="498" y="284">4 Detect</text>
<text class="pz-small" x="498" y="306">flag: code at or above</text>
<text class="pz-small" x="498" y="323">the threshold (50);</text>
<text class="pz-small" x="498" y="340">runs of flags per</text>
<text class="pz-small" x="498" y="357">path, dated by Et:</text>
<text class="pz-small" x="498" y="374">disturbance events</text>
<text class="pz-small" x="556.0" y="422" text-anchor="middle">uses: recipe</text>
<line class="pz-arrow" x1="470" y1="333.0" x2="485" y2="333.0"/>
<text class="pz-small" x="20" y="452">In monitoring this repeats at every new acquisition; staged runs score an anchor before its block is complete</text>
<text class="pz-small" x="20" y="466">(stages 1 to 4), and the final stage confirms or withdraws its flags.</text>
</svg>
</div>

From the 30 acquisitions before an anchor `t` and the covariates (weather, built-up), the forecaster predicts the coherence of the 25 pairs ending on `t` to `t + 4` (baselines 12 to 60 days). Each observed pair is scored against its forecast (`z`). The 15 pairs that span the gap before `t`, the **pyramid**, are the ones a change at `t` lowers, and their mean `z` is the anomaly score of `t`. The score is turned into a p-value against the same score on the held-out test cells of the panel (the **null**), stored as a code. The detection recipe flags codes at or above its threshold, joins flags into runs along a path, and dates each change by the break statistic `Et`: the **surface disturbance events**. Labelled damage (BRIGHT, UNOSAT) is used only to evaluate.

## Where it runs

```mermaid
flowchart LR
  suite["ponzi-suite<br/>panels, forecasters,<br/>run configs, test cases"]
  visual["ponzi-visual<br/>map: boundaries, areas,<br/>outputs over time"]
  server[("ponzi-server<br/>areas, jobs, leases,<br/>final outputs")]
  worker["ponzi-worker<br/>runs the stages,<br/>caches by content id"]
  home[("PONZI home<br/>~/.ponzi")]
  data[("ASF, Copernicus DEM,<br/>weather, GHSL")]
  visual -- "areas: boundary, orbit, days" --> server
  server -- "outputs, boundaries" --> visual
  server -- "jobs (lease)" --> worker
  worker -- "final assets: upload or shared path" --> server
  data --> worker
  worker --- home
  server --- home
  suite -. "paths given to the commands" .-> worker
```

The server keeps the watched areas, makes one job per burst at each area's cadence, and stores the final outputs; it computes nothing. The worker claims a job, runs its workflow, and keeps every output in its cache by content id, so the same work is never done twice. Everything computed lives in the PONZI home; the repositories hold code and the files PONZI runs from ([The service](service.md), [The worker](worker.md)).

## One burst under a standard

What a job runs: the workflow of the area's [standard](../guides/standards.md), for one burst and the area's days.

```mermaid
flowchart TB
  subgraph make["the coherence store of the burst"]
    direction LR
    asf[("ASF<br/>SLC scenes, orbits")] --> discover["discover<br/>acquisitions, pairs"]
    discover --> coherence["coherence<br/>ISCE3, one raster<br/>per pair"]
    dem["dem"] --> coherence
    coherence --> assemble["assemble<br/>coherence store C1"]
  end
  subgraph score["scoring and detection"]
    direction LR
    onboard["onboard<br/>sidecar C2"] --> run["run<br/>scores C7, Et C24,<br/>staged C26"]
    model[("registry<br/>model + run config")] --> run
    run --> pvalues["pvalues<br/>codes C22"]
    cal[("registry<br/>calibration")] -- "ingest-calibration" --> pvalues
    pvalues --> detect["detect<br/>events C25"]
    pvalues --> tile["tile<br/>events per<br/>Major TOM cell"]
    recipe["standard's recipe"] --> detect
    recipe --> tile
  end
  assemble --> onboard
  assemble --> run
```

`detect` and `tile` are the final steps whose Items the server keeps. A standard made from existing stores starts at `ingest-coherence` instead of the first four stages.

## How the registered pieces are made

The model, its calibrations and the standard are made with `ponzi-models`, from the files in ponzi-suite, into the PONZI home.

**Training**

```mermaid
flowchart LR
  def["panel definition<br/>panels/majortom-global<br/>(panel-check)"] --> build["panel-build<br/>stores and masks<br/>in home/panels"]
  build --> prep["prepare<br/>train and val windows,<br/>layer sample_train"]
  spec["fit spec<br/>forecasters/tide/..."] --> prep
  prep --> train["train<br/>keeps the best<br/>val epoch"]
  train --> export["export<br/>TorchScript +<br/>meta.json"]
  export --> reg["register-model<br/>model id + ONE run config:<br/>its hash fixed here"]
```

**Calibration**

```mermaid
flowchart LR
  reg[("registered model")] --> runs["null-runs<br/>production runs on the<br/>test split, layer sample_test"]
  runs --> rows["null-rows<br/>the runs' own anomaly<br/>scores where finite"]
  rows --> build["calibrate<br/>plain and ceiling"]
  build --> regcal["register-calibration<br/>under the model; records the<br/>run config hash and library version"]
  runs -. "--staged" .-> staged["calibrate-staged<br/>one mapping per stage<br/>(format 3)"]
  staged -.-> regcal
```

**A standard**

```mermaid
flowchart LR
  std["standard yaml<br/>model, calibrations, recipe,<br/>coherence, onboarding"] --> check["check-standard<br/>against the registry"]
  check --> wf["standard-workflow<br/>the server's standard file"]
  wf --> served[("home/standards<br/>read by the server")]
  bench["benchmark checks<br/>panel null, BRIGHT,<br/>Gaza with UNOSAT, Tehran"] -. "not yet a command" .-> std
```

The fixed checks a candidate standard is compared on are not yet a command: `ponzi.evaluation` has the metrics, and `ponzi-models rehearse` runs the whole lifecycle on synthetic data.

## What a change makes new

Each piece is fixed at a known point, and a change to it gives new content ids to everything downstream of it, which the worker then computes; everything upstream is reused from the cache.

<div class="pz-flows" markdown="0"><p>Pick a kind of work to see its path through the system. (The map needs JavaScript; the matrix below says the same.)</p></div>

Pick a kind of work to see where its data comes in, which registered pieces it makes new, which it computes again and which it reuses. Red dashed pieces should be computed again but are reused as the code stands (the library and engine changes); dotted ones are not yet in the code.

| Piece | Fixed by | A change means |
| --- | --- | --- |
| Library (`ponzi`) | its git tag, `0.y` the major below 1.0 | a calibration refuses runs of another major (CR-020); content ids do not change |
| Coherence config, onboarding config | the standard | new coherence stores and sidecars, and everything after |
| Panel | `id@version` in `panel.yaml`, files by sha256 | a new model and calibration: the model id carries the panel version |
| Fit spec | its file in `forecasters/` | a new fit, a new model |
| Run config | its hash, fixed at `register-model` | new runs; a calibration is made for one hash and refuses others |
| Calibration | its id under the model, the run config hash | new p-values and events; runs reused |
| Recipe | its fields, inside the standard | new events and cells; runs and p-values reused |
| Standard | `id@version`, immutable | any change is a new version; areas name the version they run |
| Area | its bursts, orbit pass and days | its jobs; no new standard |

**The change matrix.** What each kind of work makes new, recomputes or reuses, as the worker behaves today.

| Work | New | Recomputed | Reused | Today |
| --- | --- | --- | --- | --- |
| A. New area | the area | the stages of bursts not yet computed | the registry; any burst already computed | as intended |
| B. Monitoring update | the pairs Item (identified by the acquisitions found) | the new pairs' coherence; then the store, sidecar, a new staged run over the window, p-values, events | the earlier pairs; a day with nothing new reuses everything | a monitoring update is a new run, never an appended one |
| C. Fine-tune for an area | a child model (`init_from`), its calibration, a standard of its own | runs, p-values, events | coherence stores, sidecars | the two standards are not linked in the code |
| D. New panel or fit spec | model, calibration, a new standard major | runs onward | coherence stores of bursts in both | as intended |
| E. Better calibration | calibration, a new standard version | p-values, events | runs | nothing checks that its cells stayed out of training |
| F. New recipe | a new standard version | events, cells | runs, p-values | as intended |
| G. Library major change | the release | should be: runs onward | | **not automatic**: cached runs are reused; `pvalues` refuses them only when the calibration was rebuilt under the new release |
| H. Coherence engine change | new stores when the config changes | stores onward | | **not automatic** when the code changes but the config does not: stores are reused |

Standard versions: a minor version is meant to reuse the runs (a new calibration or recipe), a major one to make new runs (a new model or panel). The code records the version but does not check which kind a change is, and a standard's `requires` (the library versions it expects) is recorded but not enforced.
