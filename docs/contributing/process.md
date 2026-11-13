# Change process

## Change requests

Every change to PONZI (ponzi-core, ponzi-service and ponzi-visual) starts as a written request in this suite's `docs/history/requests/` (the template is there, [TEMPLATE.md](../history/requests/TEMPLATE.md)): why, what changes, whether results change, the tests, the version. The owner signs it off before it is implemented. A change ends with its tests green and a `CHANGELOG.md` entry.

## Tests

The `test` tasks of ponzi-core and ponzi-service run light (CR-072): at low priority (`nice -n 10`) and with the thread pools at 4 (`OMP_NUM_THREADS` and the BLAS settings, which `ponzi.core.parallel`, torch and the BLAS libraries read; unset, they take every core). The cap changes only the speed, never a result. During a change, run the test files it touches; run the whole suites before a commit, one at a time. On a shared machine, also bound a run from outside: `systemd-run --user --scope -p CPUQuota=400% -p MemoryMax=24G pixi run test`.

| Repository | Command | Runs |
| --- | --- | --- |
| ponzi-core | `pixi run test`, `pixi run test-full` | `ponzi` without the tests marked `slow` (about three minutes), and with them |
| | `pixi run test-spec`, `test-pipeline`, `test-models` | the other distributions |
| | `pixi run -e ml pytest packages/core/tests -m ml`, `pixi run -e ml test-models` | the tests marked `ml`, which need torch |
| | `pixi run -e isce3 test-pipeline` | the pipeline with the ISCE3 stack |
| ponzi-service | `pixi run test` | all three distributions; or `test-worker`, `test-server`, `test-client` |
| ponzi-visual | `pixi run test` | the components and the client on the server's own answers (`src/test/fixtures.json`), no server |
| | `pixi run e2e` | the client against a real ponzi-server serving its own demo (`.e2e/ci`) |
| | `pixi run build` | typechecks and builds `dist/` |

Everything the tests need is in the repositories: synthetic stores and small golden files under `packages/core/tests/data/`, and test doubles for the network (GHSL tiles, ERA5-Land). ponzi-core's run on every push in GitHub Actions. The tests that check ponzi-suite's files find it as `$PONZI_SUITE` or `../ponzi-suite`, and are skipped without it. The TiDE tests build their own small TorchScript model.

## Versions

Each distribution has its own [SemVer](https://semver.org) version, `X.Y.Z`, from its own git tags. What raises X, Y or Z and worked examples are in [What X, Y and Z mean](../reference/versions.md#what-x-y-and-z-mean); below 1.0, where every distribution is now, Y is the major part ([Below 1.0](../reference/versions.md#below-10)). In short:

- A change that alters numbers for an existing spec is **RESULTS-CHANGING**: a major of the distribution that computes it (ponzi-core CR-085), so everything it computes is made again and the calibrations of the old major are refused (CR-020). Say so in the change request and the `CHANGELOG.md` entry.
- The change request's **Version** line names the part each distribution raises. No other version is raised by hand (ponzi-core CR-085): a stage is named by its code's majors, a spec and a standard by their hash (CR-083, CR-089), and a store contract or a record file by the hash of its declaration ([Versions](../reference/versions.md)).

## What is locked

- Golden files under `packages/core/tests/data/` lock the numbers of the algorithm: the kernels (rolling fit, scoring, quantile scoring, state machine) and one whole run (`runner_golden.npz`). Never regenerate one to make a test pass unless the change request says results change.
- The hashing rule of content ids is fixed by a test.
- ponzi-core and ponzi-service have layering tests: the import direction between distributions and subpackages, and no heavy import (torch, the geospatial stack) where it does not belong. ponzi-visual has none yet.

## Compatibility

A standard names the versions of the distributions it needs (`requires`, PEP 440 specifiers): `ponzi-models check-standard` checks them against the installed versions, and the worker fails a job whose standard its installed versions do not meet (CR-055). The compatibility matrix (which `ponzi`, `ponzi-pipeline`, `ponzi-models` and API versions work together) is to be kept on this site as distributions are released; there is none yet.

## Style

- READMEs hold only what a repository is and how to start; details live on this site.
- Every function has a concise docstring.
- Paths use `pathlib`.
- No em-dashes in prose.
