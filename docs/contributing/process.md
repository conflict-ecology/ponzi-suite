# Change process

## Change requests

Every change to ponzi-core starts as a written request in this suite's `docs/history/requests/` (the template is there, [TEMPLATE.md](../history/requests/TEMPLATE.md)): why, what changes, whether results change, the tests, the version. The owner signs it off before it is implemented. A change ends with its tests green and a `CHANGELOG.md` entry.

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

Each distribution has its own [SemVer](https://semver.org):

- **MAJOR**: a contract or store format changes, or the default behaviour of an existing spec changes.
- **MINOR**: a new opt-in capability; every existing spec gives the same bytes.
- **PATCH**: fixes and speed-ups shown bit-identical by the tests.
- A change that alters numbers for an existing spec is marked **RESULTS-CHANGING** and is a MAJOR (ponzi-core CR-085): the major of the distribution that computes it is what gives its outputs new content ids, as stages have no version of their own. A results-changing fix to one stage is so a major of its distribution: everything that distribution computes is made again, and by CR-020 the calibrations of the old major are refused.
- Below 1.0, `0.y` counts as the major version: a calibration made with another `0.y` of `ponzi` is refused, and every output a distribution computes gets a new content id.
Every distribution takes its version from its own git tags ([Releases: the tags](../reference/versions.md#releases-the-tags)). No other version is raised by hand (ponzi-core CR-085): a stage is named by its code's majors, a spec by its hash, and a store contract or a record file by the hash of its declaration ([Versions](../reference/versions.md)).

## What is locked

- Golden files under `packages/core/tests/data/` lock the numbers of the algorithm: the kernels (rolling fit, scoring, quantile scoring, state machine) and one whole run (`runner_golden.npz`). Never regenerate one to make a test pass unless the change request says results change.
- The hashing rule of content ids is fixed by a test.
- ponzi-core and ponzi-service have layering tests: the import direction between distributions and subpackages, and no heavy import (torch, the geospatial stack) where it does not belong. ponzi-visual has none yet.

## Compatibility

A standard names the versions of the distributions it needs (`requires`, PEP 440 specifiers): `ponzi-models check-standard` checks them against the installed versions, and the worker fails a job whose standard its installed versions do not meet (CR-055). The compatibility matrix (which `ponzi`, `ponzi-pipeline`, `ponzi-models` and API versions work together) is to be kept on this site as distributions are released; there is none yet.

## Style

- READMEs hold only what a repository is and how to start; details live on this site.
- Every function has a concise docstring.
- Paths use `pathlib`; locations that may be remote are URIs (see [Configuration](../service/configuration.md)).
- No em-dashes in prose.
