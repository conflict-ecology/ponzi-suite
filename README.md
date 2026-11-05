# ponzi-suite

The documentation of PONZI: concepts, guides, the API reference of every distribution, the REST API, the STAC profile and its schemas, and pages written for agents. A MkDocs site.

```
pip install -r requirements.txt -e ../ponzi-core/packages/spec
mkdocs serve
```

Pages are under `docs/`. Content that comes from code is generated at build time (`hooks/ponzi.py`), never copied into pages: the collections table and the extension schema; the API references of every Python distribution, read from their source, and of ponzi-visual, read from its TypeScript; the REST API table, from ponzi-server's `openapi.json`; and ponzi-core's store contracts and change requests. The build reads ponzi-core, ponzi-service and ponzi-visual from checkouts beside the suite (`$PONZI_CORE`, `$PONZI_SERVICE` and `$PONZI_VISUAL` override them), and the docs workflow lays them out the same way.

## Contributing

What is done and what is left is one checklist: [Roadmap](https://conflict-ecology.github.io/ponzi-suite/contributing/roadmap/) (ponzi-suite `docs/contributing/roadmap.md`). Pick an open item there.

## What PONZI runs from

The suite also holds the files PONZI runs from, versioned here because ponzi-core, ponzi-service and ponzi-visual are code only (ponzi-core CR-048). Commands name them by path. Everything computed from them goes into the PONZI home (`~/.ponzi`, or `$PONZI_HOME`), never into a repository.

| Folder | What | Used by |
| --- | --- | --- |
| `panels/<id>/` | panel definitions: `panel.yaml` (version and the files' sha256), `bursts.geojson`, `cells.geojson`. The first is `majortom-global@0.4.0`. | `ponzi-models panel-check ../ponzi-suite/panels/majortom-global`; the rules are `ponzi_spec.panel` |
| `forecasters/<family>/` | what a model is trained as: `tide/weather.yaml` (the forecaster `tide-weather`) and its `candidates/`, named by the convention of `ponzi_spec.naming` | `ponzi-models train --spec ../ponzi-suite/forecasters/tide/candidates/fill-previous.yaml` |
| `run_configs/` | run configs (contract C4) | `ponzi run --config ../ponzi-suite/run_configs/rolling-ols-pyramid.yaml` |
| `testcases/<case>/` | test locations: an area, a recipe, its forecaster. The first is `gaza`. | `ponzi detect ... --recipe ../ponzi-suite/testcases/gaza/recipe.yaml` |
| `standards/` | standard versions, `<id>-<version>.yaml`. The first is the draft `s1-general-1.0.0.yaml`. | `ponzi-models check-standard ../ponzi-suite/standards/s1-general-1.0.0.yaml` |

Forecasters, panels and models are named by one convention, [docs/reference/naming.md](docs/reference/naming.md) (`ponzi_spec.naming`). ponzi-core's tests check these files (`test_panels.py`, `test_testcases.py`, `test_training_missing.py`, `test_suite_names.py`). They find the suite as `$PONZI_SUITE`, else `ponzi-suite/` beside ponzi-core.

The instructions AI coding agents follow in every PONZI repository are in `agents/` (see `agents/README.md`); each repository's `CLAUDE.md` imports its file from there.
