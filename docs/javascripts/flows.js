// The change map of "How PONZI works": pick a kind of work to see its path through the system, which pieces it
// makes new, computes again, reuses or reads, and its steps. Drawn as SVG into every `.pz-flows` element, from SPEC.
// Everything here follows the code as it stands; "gap" marks what should be computed again but is reused today,
// "todo" what is not yet a command.
(function () {
  "use strict";

  const HEADS = ["Data sources", "Training", "Registry", "Area runs", "Results"];
  const NODES = [
    { id: "asf", col: 0, y: 40, label: "Sentinel-1 scenes", sub: "ASF: SLCs, orbits", kind: "data" },
    { id: "wx", col: 0, y: 118, label: "Weather, built-up", sub: "EDH or CDS grid, GHSL", kind: "data" },
    { id: "pan_tr", col: 0, y: 210, label: "Panel: train, val cells", sub: "majortom-global@0.4.0", kind: "data" },
    { id: "pan_te", col: 0, y: 296, label: "Panel: test cells", sub: "the calibration null", kind: "data" },
    { id: "aoi_pre", col: 0, y: 382, label: "Area pre-event data", sub: "e.g. Gaza before Oct 2023", kind: "data" },
    { id: "labels", col: 0, y: 482, label: "Labels, known events", sub: "BRIGHT, UNOSAT", kind: "data" },
    { id: "train", col: 1, y: 250, label: "Training", sub: "prepare, train, export", kind: "piece" },
    { id: "model", col: 2, y: 168, label: "Model + run config", sub: "registry, immutable", kind: "piece" },
    { id: "cal", col: 2, y: 296, label: "Calibration", sub: "under the model", kind: "piece" },
    { id: "recipe", col: 2, y: 410, label: "Recipe", sub: "threshold, dating rules", kind: "piece" },
    { id: "coh", col: 3, y: 40, label: "Coherence stores", sub: "ISCE3, one per burst", kind: "piece" },
    { id: "onb", col: 3, y: 118, label: "Onboarding", sub: "sidecar per burst", kind: "piece" },
    { id: "runs", col: 3, y: 210, label: "Forecast runs", sub: "scores, Et, staged", kind: "piece" },
    { id: "pv", col: 3, y: 296, label: "p-values", sub: "codes per anchor", kind: "piece" },
    { id: "ev", col: 3, y: 410, label: "Events", sub: "detect, tile", kind: "piece" },
    { id: "std", col: 4, y: 168, label: "Standard", sub: "id@version, immutable", kind: "piece" },
    { id: "prod", col: 4, y: 410, label: "Outputs", sub: "per Major TOM cell", kind: "piece" },
    { id: "checks", col: 4, y: 500, label: "Benchmark checks", sub: "not yet a command", kind: "piece" },
  ];
  const EDGES = [
    { id: "asf-coh", from: "asf", to: "coh", label: "scenes, pairs" },
    { id: "coh-onb", from: "coh", to: "onb", label: "store", route: "v" },
    { id: "wx-onb", from: "wx", to: "onb", label: "covariates" },
    { id: "pantr-train", from: "pan_tr", to: "train", label: "train, val" },
    { id: "aoi-train", from: "aoi_pre", to: "train", label: "fine-tune" },
    { id: "train-model", from: "train", to: "model", label: "register" },
    { id: "model-cal", from: "model", to: "cal", label: "null runs", route: "v" },
    { id: "pante-cal", from: "pan_te", to: "cal", label: "test cells" },
    { id: "model-runs", from: "model", to: "runs", label: "model" },
    { id: "onb-runs", from: "onb", to: "runs", label: "sidecar", route: "v" },
    { id: "coh-runs", from: "coh", to: "runs", label: "C1", route: "right" },
    { id: "runs-pv", from: "runs", to: "pv", label: "scores", route: "v" },
    { id: "cal-pv", from: "cal", to: "pv", label: "maps" },
    { id: "pv-ev", from: "pv", to: "ev", label: "codes", route: "v" },
    { id: "runs-ev", from: "runs", to: "ev", label: "Et", route: "right" },
    { id: "recipe-ev", from: "recipe", to: "ev", label: "rules" },
    { id: "ev-prod", from: "ev", to: "prod", label: "" },
    { id: "ev-checks", from: "ev", to: "checks", label: "on test areas", dashed: true },
    { id: "labels-checks", from: "labels", to: "checks", label: "known events", route: "under", dashed: true },
    { id: "checks-std", from: "checks", to: "std", label: "promote", route: "outer", dashed: true },
  ];
  // the states: data (read), comp (computed again), new (a new version made), reused, gap (should be computed
  // again, reused today), todo (not yet in the code); a piece not named is not involved
  const FLOWS = [
    { id: "area", name: "New area", freq: "most common", std: "same standard",
      example: "Gaza: 40 Major TOM tiles over the Strip, tagged gaza-2023, 7 Oct 2023 to 31 Jan 2024.",
      nodes: { asf: "data", wx: "data", coh: "comp", onb: "comp", runs: "comp", pv: "comp", ev: "comp", prod: "new",
               model: "reused", cal: "reused", recipe: "reused", std: "reused" },
      steps: ["In ponzi-visual, click or paint Major TOM tiles (up to 64), add tags and the days. The server watches every burst of both passes that meets the tiles.",
              "On creation, then at the area's cadence, the server makes one job per burst: the standard's workflow with the area's days.",
              "A worker finds the acquisitions (ASF), downloads the scenes and makes the burst's coherence store with ISCE3.",
              "Onboard the store: weather and built-up covariates into its sidecar.",
              "Run the standard's model (staged, with Et), code p-values with its calibration, detect with its recipe, and tile into Major TOM cells.",
              "The worker delivers the final Items to the server. Anything already computed is reused by content id; nothing new is registered."] },
    { id: "mon", name: "Monitoring update", freq: "every acquisition", std: "same standard",
      example: "New Sentinel-1 acquisitions over an area that is already watched.",
      nodes: { asf: "data", wx: "data", coh: "comp", onb: "comp", runs: "comp", pv: "comp", ev: "comp", prod: "new",
               model: "reused", cal: "reused", recipe: "reused", std: "reused" },
      steps: ["At each cadence the server makes the area's jobs again, ending today or on the area's last day.",
              "Discovery lists the acquisitions; an unchanged list gives the same pairs Item, and nothing after it runs again.",
              "Only the new pairs' coherence is computed; the store is assembled again with them, and so is its sidecar.",
              "A new staged run scores the window, the new anchors at every stage (CR-021). A run is never appended to.",
              "New p-values and events: early flags are provisional, confirmed or withdrawn at the final stage."] },
    { id: "tune", name: "Fine-tune for an area", freq: "per conflict area", std: "a standard of its own",
      example: "Gaza: tide-weather-gaza-finetune, from the general model on pre-war Gaza windows.",
      nodes: { aoi_pre: "data", pan_te: "data", labels: "data", train: "new", model: "new", cal: "new", std: "new",
               coh: "reused", onb: "reused", recipe: "reused", runs: "comp", pv: "comp", ev: "comp", prod: "new",
               checks: "todo" },
      steps: ["The test case's fit spec (testcases/<case>/forecaster.yaml) builds on the base forecaster, starting from its weights.",
              "Train and export it; register the child model with its run config.",
              "Calibrate it on the panel's test cells (null-runs, null-rows, calibrate), as the general model was.",
              "Check it against the area's labels: not yet a command (ponzi.evaluation has the metrics).",
              "Publish a standard of its own (check-standard, standard-workflow). The code does not record that it branches from the general one.",
              "Point the area at it: its runs, p-values and events are made again."] },
    { id: "general", name: "Better general model", freq: "a few times a year", std: "new standard, major",
      example: "majortom-global@0.5.0, or a new fit spec such as tide-weather-fill-previous-augmented.",
      nodes: { pan_tr: "new", pan_te: "new", labels: "data", train: "new", model: "new", cal: "new", std: "new",
               coh: "reused", onb: "reused", recipe: "reused", runs: "comp", pv: "comp", ev: "comp", prod: "new",
               checks: "todo" },
      steps: ["A new panel version in ponzi-suite panels/ (panel-check), built into the home with its stores and masks (panel-build).",
              "Train with the fit spec (prepare, train, export).",
              "Register the model: its id carries the panel version, tide-weather--majortom-global-0.5.0.",
              "Calibrate it on the new panel's test cells.",
              "Benchmark it against the current standard: not yet a command.",
              "Publish a new major standard version; the previous one stays as it is.",
              "Areas run it once their standard is changed to it; older outputs keep theirs."] },
    { id: "cal", name: "Better calibration", freq: "occasionally", std: "new standard, minor",
      example: "More test cells, or a staged (format 3) calibration with calibrate-staged.",
      nodes: { pan_te: "new", labels: "data", model: "reused", cal: "new", std: "new", runs: "reused", pv: "comp",
               ev: "comp", prod: "new", recipe: "reused", checks: "todo" },
      steps: ["Extend the test cells. Nothing checks yet that they stay out of training.",
              "Run the registered model on them (null-runs; --staged for a staged calibration).",
              "Build and file it under the same model: null-rows, calibrate (or calibrate-staged), register-calibration.",
              "A new standard version names it.",
              "The runs are reused from the cache; only p-values and events are computed again."] },
    { id: "recipe", name: "New recipe", freq: "while rules settle", std: "new standard, minor",
      example: "Threshold code 55 instead of 50, or episodes on.",
      nodes: { recipe: "new", std: "new", labels: "data", model: "reused", cal: "reused", runs: "reused",
               pv: "reused", ev: "comp", prod: "new", checks: "todo" },
      steps: ["Change the recipe's fields (a recipe yaml, such as testcases/gaza/recipe.yaml).",
              "A new standard version holds it.",
              "detect and tile run again; runs and p-values are reused from the cache."] },
    { id: "lib", name: "Library major change", freq: "rarely", std: "should be major",
      example: "A results-changing fix, such as the Et early-anchor fix.",
      nodes: { lib: "new", cal: "new", std: "new", model: "reused", coh: "reused", onb: "reused", recipe: "reused",
               runs: "comp", pv: "comp", ev: "comp", prod: "comp" },
      steps: ["Release the library with a new major (0.y while below 1.0).",
              "Rebuild the calibration under it: a calibration refuses runs of another major (CR-020).",
              "The major is part of the content id of every stage whose code it is (CR-054), so the runs and everything after them are made again."] },
    { id: "engine", name: "Coherence engine change", freq: "per engine release", std: "same, or major",
      example: "A new ISCE3 or ponzi-pipeline release, or a new coherence config.",
      nodes: { lib: "new", asf: "data", coh: "gap", onb: "gap", runs: "gap", pv: "gap", ev: "gap", prod: "gap",
               model: "reused", cal: "reused", recipe: "reused" },
      steps: ["With a new coherence config in the standard, the stores and everything after them get new content ids and are made again.",
              "A new ponzi-pipeline major is part of the coherence stages' content ids (CR-054), so the stores are made again.",
              "Today: a minor or patch release of ponzi-pipeline, or a new ISCE3, with the same config keeps the stores' content ids, and they are reused; a stage version raise makes them again."] },
  ];
  const LEGEND = [["new", "new version made"], ["comp", "computed again"], ["reused", "reused as is"],
                  ["data", "data read"], ["gap", "should rerun, reused today"], ["todo", "not yet in the code"],
                  ["idle", "not involved"]];
  const LIBRARY = "Library: ponzi 0.2.4, ponzi-pipeline 0.2.0, ponzi-models 0.3.0. Their majors are in the content ids (CR-054).";

  const NS = "http://www.w3.org/2000/svg";
  const NW = 172, NH = 48, COLX = [16, 236, 456, 676, 896], W = COLX[4] + NW + 90, H = 600;
  const X = (n) => COLX[n.col], Y = (n) => n.y;
  const byId = Object.fromEntries(NODES.map((n) => [n.id, n]));

  function draw(root) {
    root.innerHTML = `
      <div class="pz-tabs" role="tablist" aria-label="Kinds of work"></div>
      <div class="pz-board">
        <div class="pz-mapbox"><svg class="pz-map" viewBox="0 0 ${W} ${H}" role="img"
             aria-label="The pieces of PONZI and the data they read, highlighted for the selected kind of work"></svg></div>
        <aside class="pz-side" aria-live="polite"><span class="pz-std"></span><h4 class="pz-fname"></h4>
          <p class="pz-ex"></p><ol class="pz-steps"></ol></aside>
      </div>
      <div class="pz-legend">${LEGEND.map(([k, t]) => `<span><i class="pz-sw pz-${k}"></i>${t}</span>`).join("")}
        <span><i class="pz-sw pz-path"></i>path of this work</span></div>`;
    const svg = root.querySelector("svg");
    const el = (tag, attrs, parent) => {
      const x = document.createElementNS(NS, tag);
      for (const k in attrs) x.setAttribute(k, attrs[k]);
      (parent || svg).appendChild(x);
      return x;
    };
    const txt = (s, attrs, parent) => { const t = el("text", attrs, parent); t.textContent = s; return t; };
    const defs = el("defs", {});
    for (const [id, cls] of [["pz-ah", "pz-ah-on"], ["pz-ahm", "pz-ah-off"]]) {
      const m = el("marker", { id, viewBox: "0 0 10 10", refX: 9, refY: 5, markerWidth: 7, markerHeight: 7,
                               orient: "auto-start-reverse" }, defs);
      el("path", { d: "M0,0 L10,5 L0,10 z", class: cls }, m);
    }
    HEADS.forEach((h, i) => txt(h, { x: COLX[i], y: 22, class: "pz-head-text" }));
    const lib = el("g", { class: "pz-node pz-band" });
    el("rect", { x: COLX[1], y: 560, width: COLX[4] + NW - COLX[1], height: 26, rx: 5 }, lib);
    txt(LIBRARY, { x: COLX[1] + 10, y: 577, class: "pz-sub" }, lib);

    function pts(e) {
      const a = byId[e.from], b = byId[e.to];
      const ax = X(a), ay = Y(a), bx = X(b), by = Y(b);
      if (e.route === "v") return [[ax + NW / 2, ay + NH], [bx + NW / 2, by]];
      if (e.route === "right") return [[ax + NW, ay + NH / 2 + 8], [ax + NW + 16, ay + NH / 2 + 8],
                                       [bx + NW + 16, by + NH / 2 - 8], [bx + NW, by + NH / 2 - 8]];
      if (e.route === "under") return [[ax + NW, ay + NH / 2 + 10], [bx - 20, ay + NH / 2 + 10], [bx - 20, by + NH - 8], [bx, by + NH - 8]];
      if (e.route === "outer") return [[ax + NW, ay + NH / 2], [ax + NW + 18, ay + NH / 2], [bx + NW + 18, by + NH / 2], [bx + NW, by + NH / 2]];
      return [[ax + NW, ay + NH / 2], [bx, by + NH / 2]];
    }
    const EDG = {};
    for (const e of EDGES) {
      const g = el("g", { class: "pz-edge" });
      const p = pts(e);
      const path = el("path", { d: "M" + p.map((q) => q.join(",")).join(" L"), fill: "none" }, g);
      if (e.dashed) path.setAttribute("stroke-dasharray", "5 4");
      let best = 0, mx = 0, my = 0, vert = false;
      for (let i = 0; i < p.length - 1; i++) {
        const d = Math.hypot(p[i + 1][0] - p[i][0], p[i + 1][1] - p[i][1]);
        if (d > best) { best = d; mx = (p[i][0] + p[i + 1][0]) / 2; my = (p[i][1] + p[i + 1][1]) / 2; vert = p[i][0] === p[i + 1][0]; }
      }
      const t = txt(e.label, { x: vert ? mx + 6 : mx, y: vert ? my + 4 : my - 5, "text-anchor": vert ? "start" : "middle" }, g);
      EDG[e.id] = { g, path, t, e };
    }
    const NOD = {};
    for (const n of NODES) {
      const g = el("g", { class: "pz-node" });
      el("rect", { x: X(n), y: Y(n), width: NW, height: NH, rx: n.kind === "data" ? 14 : 7 }, g);
      txt(n.label, { x: X(n) + 12, y: Y(n) + 20, class: "pz-label" }, g);
      txt(n.sub, { x: X(n) + 12, y: Y(n) + 37, class: "pz-sub" }, g);
      NOD[n.id] = g;
    }
    NOD.lib = lib;

    const tabs = root.querySelector(".pz-tabs");
    const show = (f) => {
      for (const b of tabs.children) b.setAttribute("aria-selected", String(b.dataset.flow === f.id));
      for (const k in NOD) NOD[k].setAttribute("class", `pz-node ${k === "lib" ? "pz-band " : ""}pz-${f.nodes[k] || "idle"}`);
      const live = (s) => s && s !== "reused" && s !== "idle";
      for (const k in EDG) {
        const { e } = EDG[k];
        const on = f.nodes[e.from] && f.nodes[e.from] !== "idle" && live(f.nodes[e.to]);
        EDG[k].g.setAttribute("class", on ? "pz-edge pz-on" : "pz-edge");
        EDG[k].path.setAttribute("marker-end", on ? "url(#pz-ah)" : "url(#pz-ahm)");
      }
      root.querySelector(".pz-std").textContent = f.std;
      root.querySelector(".pz-fname").textContent = f.name;
      root.querySelector(".pz-ex").textContent = f.example;
      const ol = root.querySelector(".pz-steps");
      ol.replaceChildren(...f.steps.map((s) => { const li = document.createElement("li"); li.textContent = s; return li; }));
    };
    for (const f of FLOWS) {
      const b = document.createElement("button");
      b.type = "button";
      b.setAttribute("role", "tab");
      b.dataset.flow = f.id;
      b.innerHTML = `<span class="pz-tname">${f.name}</span><span class="pz-tfreq">${f.freq}</span>`;
      b.addEventListener("click", () => show(f));
      tabs.appendChild(b);
    }
    // a link may name the work to open on: #flow-<id> (e.g. #flow-lib)
    const want = location.hash.startsWith("#flow-") ? location.hash.slice(6) : null;
    show(FLOWS.find((f) => f.id === want) || FLOWS[0]);
  }

  const run = () => document.querySelectorAll(".pz-flows").forEach(draw);
  if (window.document$ && typeof window.document$.subscribe === "function") window.document$.subscribe(run);
  else if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", run);
  else run();
})();
