# ponzi-suite

The documentation of PONZI: concepts, guides, the API reference of every distribution, the REST API, the STAC profile and its schemas, and pages written for agents. A MkDocs site.

```
pip install -r requirements.txt -e ../ponzi-core/packages/spec
mkdocs serve
```

Pages are under `docs/`. Content that comes from code is generated at build time (`hooks/ponzi.py`), never copied into pages: the collections table and the extension schema; the API references of every Python distribution, read from their source, and of ponzi-visual, read from its TypeScript; the REST API table, from ponzi-server's `openapi.json`; and the index of the change requests, which are kept here with the store contracts (ponzi-core CR-071). The build reads ponzi-core, ponzi-service and ponzi-visual from checkouts beside the suite (`$PONZI_CORE`, `$PONZI_SERVICE` and `$PONZI_VISUAL` override them), and the docs workflow lays them out the same way.

## A development workstation

Linux on x86-64 only, for now: both commands check the machine first and stop on any other system.

For developing and testing PONZI on one machine, not for deploying it, two pixi tasks of this repository set up and start the whole system ([Install](docs/getting-started/install.md#for-development), [Quickstart](docs/getting-started/quickstart.md#development-on-your-own-home)):

```
pixi run dev-install         # clone the missing ponzi-core, ponzi-service, ponzi-visual beside the suite, install them
pixi run dev-up              # the server, the client loop and the front end on the PONZI home, until Ctrl+C
```

The logic is in `scripts/`. The docs build stays on `requirements.txt` above, outside pixi.

## Contributing

What is done and what is left is one checklist: [Roadmap](https://conflict-ecology.github.io/ponzi-suite/contributing/roadmap/) (ponzi-suite `docs/contributing/roadmap.md`). Pick an open item there.

## What PONZI runs from

The suite also holds the files PONZI runs from, versioned here because ponzi-core, ponzi-service and ponzi-visual are code only (ponzi-core CR-048). Commands name them by name or by path. Everything computed from them goes into the PONZI home (`~/.ponzi`, or `$PONZI_HOME`), never into a repository.

| Folder | What | Used by |
| --- | --- | --- |
| `specs/panel_specs/<id>/` | panel specs, how a panel is built: `panel.yaml` (the draw, the coherence spec by name, the files' sha256; no version), `bursts.geojson`, `cells.geojson`. The first is `majortom-global`. | `ponzi-models panel-check majortom-global`, `panel-build --panel-spec majortom-global`; the rules are `ponzi_spec.panel` |
| `specs/training_specs/<family>/` | training specs, how a model is trained: `tide/tide-weather.yaml` and its `candidates/`; every spec is named by its file (a panel spec by its folder), by the convention of `ponzi_spec.naming` | `ponzi-models train --training-spec tide-weather-fill-previous` |
| `specs/scoring_specs/` | scoring specs, how a model is applied to a burst (contract C4) | `ponzi run --scoring-spec rolling-ols-pyramid` |
| `specs/coherence_specs/` | coherence specs, how a burst's coherence store is made: `isce3-gaussian` | a standard's `coherence`, a panel spec's `coherence`; `ponzi-pipeline ... --coherence-spec isce3-gaussian` |
| `specs/onboarding_specs/` | onboarding specs, how a store's sidecar and pixel sample are made: `all-steps` | a standard's `onboarding`; `ponzi-pipeline onboard --onboarding-spec all-steps` |
| `specs/detection_specs/` | detection specs, how the events and cells are made from p-values: `single-path` | a standard's `detection`; `ponzi detect ... --detection-spec single-path` |
| `testcases/<case>/` | test locations: an area (`area.yaml`); their specs are under `specs/`, named after them. The first is `gaza`. | `ponzi detect ... --detection-spec single-path-gaza-release` |
| `standards/` | standard versions, `<id>-<version>.yaml`, the id `<sensor>-<scope>`, naming the specs above. The first is the draft `s1-general-2.0.0.yaml`. | `ponzi-models check-standard ../ponzi-suite/standards/s1-general-2.0.0.yaml`; `new-standard`, `bump-standard`, `register-standard` |

A command takes a spec as `--<kind>-spec NAME|FILE` (ponzi-core CR-070): a name is looked up in the PONZI home's folder of the same name (`$PONZI_HOME/specs/training_specs/`, `specs/scoring_specs/`, `specs/panel_specs/`, `specs/detection_specs/`, `specs/coherence_specs/`, `specs/onboarding_specs/`) first, then in this repository's; a path is always accepted. A spec's version is its content hash, cited `name@<hash8>` (ponzi-core CR-083): a spec is edited in place, and the registry archives every version used. Where a spec is used (a model card, a built panel, a calibration, a registered standard, the server's standard file) its name, hash and the commit of this repository it was read from are recorded; a published standard is registered only from committed files.

Specs, panels and models are named by one convention, [docs/models/naming.md](docs/models/naming.md) (`ponzi_spec.naming`). ponzi-core's tests check these files (`test_panels.py`, `test_testcases.py`, `test_training_missing.py`, `test_suite_names.py`). They find the suite as `$PONZI_SUITE`, else `ponzi-suite/` beside ponzi-core.

The instructions AI coding agents follow in every PONZI repository are in `agents/` (see `agents/README.md`); each repository's `CLAUDE.md` imports its file from there.
