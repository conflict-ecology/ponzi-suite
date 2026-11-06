# CR-072: the test tasks run light

- **Requested by / date:** owner, 2026-11-06 ("the tests are extremely heavy and almost froze my computer. is there a way to lighten them?", then "lets make those changes.")
- **Status:** signed off (2026-11-06), implemented (2026-11-06)

## Why
A full run of ponzi-core's and ponzi-service's tests nearly froze the owner's laptop. The suites run one test at a time, but the code under test fans out: with `OMP_NUM_THREADS` unset, `ponzi.core.parallel.n_workers` takes every CPU the process may use (32 on the laptop), and torch and the BLAS libraries do the same, so every run-shaped test filled every core.

## What changes
- In ponzi-core's and ponzi-service's `pixi.toml`, each `test*` task runs `nice -n 10 pytest ...` with `OMP_NUM_THREADS`, `OPENBLAS_NUM_THREADS`, `MKL_NUM_THREADS` and `NUMEXPR_MAX_THREADS` at 4. A run is a background job, so it gives way to whatever the person is doing.
- The suite's change process (`contributing/process.md`, section Tests) says so, and how to bound a run from outside on a shared machine (`systemd-run --user --scope -p CPUQuota=400% -p MemoryMax=24G`). During a change, the test files it touches are run; the whole suites run before a commit, one at a time.
- Nothing else reads these settings differently: a production run, the worker and the SLURM scripts (`OMP_NUM_THREADS=$SLURM_CPUS_PER_TASK`) are unchanged.

## Do results change?
No. The number of threads changes only the speed; the tests that set `OMP_NUM_THREADS` themselves (`test_parallel`, `test_runner`) still do.

## Tests
A probe run through `pixi run test-spec` under the `systemd-run` bound: `n_workers()` is 4, `OMP_NUM_THREADS` is 4, the niceness is 10.

## Version
Library: none (tooling only). Standard: no change.
