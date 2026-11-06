# ponzi-suite

The documentation of PONZI: concepts, guides, the API reference of every distribution, the REST API, the STAC profile and its schemas, and pages written for agents. A MkDocs site.

```
pip install -r requirements.txt -e ../ponzi-core/packages/spec
mkdocs serve
```

Pages are under `docs/`. Content that comes from code is generated at build time (`hooks/ponzi.py`), never copied into pages: the collections table and the extension schema; the API references of every Python distribution, read from their source, and of ponzi-visual, read from its TypeScript; the REST API table, from ponzi-server's `openapi.json`; and ponzi-core's store contracts and change requests. The build reads ponzi-core, ponzi-service and ponzi-visual from checkouts beside the suite (`$PONZI_CORE`, `$PONZI_SERVICE` and `$PONZI_VISUAL` override them), and the docs workflow lays them out the same way.

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

The suite also holds the files PONZI runs from, versioned here because ponzi-core, ponzi-service and ponzi-visual are code only (ponzi-core CR-048). Commands name them by path. Everything computed from them goes into the PONZI home (`~/.ponzi`, or `$PONZI_HOME`), never into a repository.

| Folder | What | Used by |
| --- | --- | --- |
| `panel_specs/<id>/` | panel specs, how a panel is built: `panel.yaml` (the draw, the coherence spec by name, the files' sha256; no version), `bursts.geojson`, `cells.geojson`. The first is `majortom-global`. | `ponzi-models panel-check majortom-global`, `panel-build --panel-spec majortom-global`; the rules are `ponzi_spec.panel` |
| `training_specs/<family>/` | training specs, how a model is trained: `tide/weather.yaml` (`tide-weather`) and its `candidates/`, named by the convention of `ponzi_spec.naming` | `ponzi-models train --training-spec tide-weather-fill-previous` |
| `scoring_specs/` | scoring specs, how a model is applied to a burst (contract C4) | `ponzi run --scoring-spec rolling-ols-pyramid` |
| `coherence_specs/` | coherence specs, how a burst's coherence store is made: `isce3-gaussian` | a standard's `coherence`, a panel spec's `coherence`; `ponzi-pipeline ... --coherence-spec isce3-gaussian` |
| `onboarding_specs/` | onboarding specs, how a store's sidecar and pixel sample are made: `all-steps` | a standard's `onboarding`; `ponzi-pipeline onboard --onboarding-spec all-steps` |
| `detection_specs/` | detection specs, how the events and cells are made from p-values: `single-path` | a standard's `detection`; `ponzi detect ... --detection-spec single-path` |
| `testcases/<case>/` | test locations: an area, a detection spec (`detection.yaml`), its training spec (`training.yaml`). The first is `gaza`. | `ponzi detect ... --detection-spec ../ponzi-suite/testcases/gaza/detection.yaml` |
| `standards/` | standard versions, `<id>-<version>.yaml`, the id `<sensor>-<scope>`, naming the specs above. The first is the draft `s1-general-2.0.0.yaml`. | `ponzi-models check-standard ../ponzi-suite/standards/s1-general-2.0.0.yaml`; `new-standard`, `bump-standard`, `register-standard` |

A command takes a spec as `--<kind>-spec NAME|FILE` (ponzi-core CR-070): a name is looked up in the PONZI home's folder of the same name (`$PONZI_HOME/training_specs/`, `scoring_specs/`, `panel_specs/`, `detection_specs/`, `coherence_specs/`, `onboarding_specs/`) first, then in this repository's; a path is always accepted. A spec has no version: it is known by its name and its content hash, and a changed spec is a new name. Where a spec is used (a model card, a built panel, a calibration, a registered standard, the server's standard file) its name, hash and the commit of this repository it was read from are recorded; a published standard is registered only from committed files.

Specs, panels and models are named by one convention, [docs/models/naming.md](docs/models/naming.md) (`ponzi_spec.naming`). ponzi-core's tests check these files (`test_panels.py`, `test_testcases.py`, `test_training_missing.py`, `test_suite_names.py`). They find the suite as `$PONZI_SUITE`, else `ponzi-suite/` beside ponzi-core.

The instructions AI coding agents follow in every PONZI repository are in `agents/` (see `agents/README.md`); each repository's `CLAUDE.md` imports its file from there.
