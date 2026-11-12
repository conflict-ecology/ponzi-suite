# CR-047: definitions in git, everything computed in the PONZI home

- **Requested by / date:** owner, 2026-11-04: "I want the specs for the files necessary for a panel defined in core. but no data should live within any of the repos. they should be generated and placed in ~/.ponzi or whatever path is provided"; "coherence stores and sidecars catalog registry and standards should also live in .ponzi"; "If I copy .ponzi to another system, I should be able to run the same code from the repos"; and, on where the panel definitions go, "ponzi-core should have the root panels dir that is git tracked". The Gaza test case stays in `testcases/`.
- **Status:** implemented on the owner's instruction (2026-11-04), awaiting review; uncommitted
- **Superseded in part:** built panels are named by the spec hash, not a semver version (CR-083).

## Why

A panel definition says which bursts and cells a model learns from. It is small, written once, and has to be versioned, so it belongs in git. What is made from it belongs outside every repository, in the PONZI home: the coherence stores, sidecars, masks, the built panel, models, calibrations, standards and the burst catalog. And the home has to be movable. A home copied to another machine has to run with the same repositories and give the same results.

## What changes

**The definition's schema (`ponzi_spec.panel`):**
- `PanelMeta` (`panel.yaml`), `BurstProperties` and `CellProperties`.
- `load_definition` holds a folder to the rules:
  - the folder is named by the id, and the version is semver;
  - exactly the three files, each matching its sha256 in `panel.yaml`;
  - every burst has a footprint, and ids are unique;
  - the cells and the bursts name each other, and a burst's split is its cells' (`mixed` when they differ);
  - the split counts are those of the files, and every window is ordered.
- `ponzi-models panel-check DIR` runs it.

**Definitions in git:** `panels/<id>/` at the repository root, replacing CR-046's `data/panels/`. The first is `panels/majortom-global` (0.4.0), unchanged.

**Everything computed, in the home:**
- The layout gains `registry/` (models and calibrations) and `panels/` (built panels, `<id>@<version>/`). `cache/` holds the coherence stores, sidecars and every stage's output. `catalog/`, `standards/` and `downloads/` stay as in CR-045.
- The model registry defaults to `{home}/registry` when neither `PONZI_MODEL_REGISTRY` nor `PONZI_DATA_ROOT` is set. It used to refuse.
- `ponzi-models panel-build` without `--out` builds into `{home}/panels/<id>@<version>`.

**Portability:**
- A built panel records each store relative to its folder when the store is inside the folder, as before, and now also when both are in the PONZI home (`../../cache/...`).
- A store outside the home is still recorded as an absolute path.
- The worker cache already records its entries' assets relative to each entry. The server's paths come from its settings at runtime.

## Do results change?

No. Content ids never depended on paths, so a copied home has the same ids.

## Tests

- ponzi-spec `test_panel_definition.py`: a good two-cell definition reads, and a changed file without a new digest, a folder not named by its id, an extra file, a burst missing from the bursts, a wrong split, wrong counts, a burst without a footprint, and a bad id are each refused.
- ponzi-core `test_panels.py`: every definition in `panels/` holds to the rules, and `majortom-global` is the upstream v0.4.
- ponzi-models:
  - `test_panel_build.py`: a panel built in a home with its stores in `cache/` records no absolute path into the home, and a copy of the home at another path, the original removed, opens the same panel, with every store found and unchanged.
  - `test_registry_store.py`: the registry defaults to the home.

## Not yet

Building a panel from an imported definition. `majortom-global` gives a window per cell (nine different ones), but a builder spec (`PanelSpec`) has one window, so `panel-build` cannot yet rebuild it as defined. That needs per-cell windows in the builder, a later request.

Done in CR-056 (per-cell panel windows, `panel-build --definition`).

## Version

ponzi-spec: minor (`panel`). ponzi-models: minor (`panel-check`; the registry and `panel-build` defaults).
