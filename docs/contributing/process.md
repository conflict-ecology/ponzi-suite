# Change process

## Change requests

Every change to ponzi-core starts as a written request in this suite's `docs/history/requests/` (the template is there, [TEMPLATE.md](../history/requests/TEMPLATE.md)): why, what changes, whether results change, the tests, the version. The owner signs it off before it is implemented. A change ends with its tests green and a `CHANGELOG.md` entry.

## Tests

The `test` tasks of ponzi-core and ponzi-service run light (CR-072): at low priority (`nice -n 10`) and with the thread pools at 4 (`OMP_NUM_THREADS` and the BLAS settings, which `ponzi.core.parallel`, torch and the BLAS libraries read; unset, they take every core). The cap changes only the speed, never a result. During a change, run the test files it touches; run the whole suites before a commit, one at a time. On a shared machine, also bound a run from outside: `systemd-run --user --scope -p CPUQuota=400% -p MemoryMax=24G pixi run test`.

## Versions

Each distribution has its own [SemVer](https://semver.org):

- **MAJOR**: a contract or store format changes, or the default behaviour of an existing config changes.
- **MINOR**: a new opt-in capability; every existing config gives the same bytes.
- **PATCH**: fixes and speed-ups shown bit-identical by the tests.
- A change that alters numbers for an existing config is marked **RESULTS-CHANGING** and is at least MINOR.
- Below 1.0, `0.y` counts as the major version: a calibration made with another `0.y` of `ponzi` is refused, and every output a distribution computes gets a new content id.
- Each distribution of ponzi-core takes its version from its own git tags: `vX.Y.Z` for `ponzi`, `spec-vX.Y.Z`, `pipeline-vX.Y.Z` and `models-vX.Y.Z` for the others (hatch-vcs, CR-054). An untagged commit carries the distance from the last tag and the commit, such as `0.2.5.dev3+gabc1234`.

A stage's identity version (in its content ids) is separate: it is raised whenever the stage's output bytes may change, see [Content ids](../using/content-ids.md).

## What is locked

- Golden files under `packages/core/tests/data/` lock the numbers of the algorithm. Never regenerate one to make a test pass unless the change request says results change.
- The hashing rule of content ids is fixed by a test.
- ponzi-core and ponzi-service have layering tests: the import direction between distributions and subpackages, and no heavy import (torch, the geospatial stack) where it does not belong. ponzi-visual has none yet.

## Compatibility

A standard names the versions of the distributions it needs (`requires`, PEP 440 specifiers): `ponzi-models check-standard` checks them against the installed versions, and the worker fails a job whose standard its installed versions do not meet (CR-055). The compatibility matrix (which `ponzi`, `ponzi-pipeline`, `ponzi-models` and API versions work together) is to be kept on this site as distributions are released; there is none yet.

## Style

- READMEs hold only what a repository is and how to start; details live on this site.
- Every function has a concise docstring.
- Paths use `pathlib`; locations that may be remote are URIs (see [Configuration](../service/configuration.md)).
- No em-dashes in prose.
