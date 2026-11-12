# CR-080: what the commands make lands in the PONZI home by default

- **Requested by / date:** owner, 2026-11-12 ("double check all files generated exist in ponzi home", then "all of it")
- **Status:** signed off (2026-11-12), implemented (unreleased)
- **Superseded in part:** scratch is the home's `tmp/`, no longer `roots.scratch` of a deployment config (CR-088).

## Why
An audit of where PONZI writes found everything a server or a worker makes inside the home (the database, keys, standards, outputs, catalog, cache with its job scratch and SLURM batches, logs, registry, built panels, specs and, since CR-079, every download). What was not: the commands that make a model or a coherence store by hand required an output folder and had no place in the home (`prepare`/`train --out`, `export --models-root`, `ponzi-pipeline --work`), `standard-workflow` required `--out` though the server reads its standards from the home, ISCE3's geocoding scratch went to the system `/tmp` though the deployment config names a scratch root, `train --preflight` let wandb write its own folders under `~/.config` and `~/.cache`, and the help texts of five `ponzi-models` commands named `~/.ponzi/registry` where the code uses `$PONZI_HOME`.

## What changes
- `ponzi_spec.home.Layout` gains `training/`, `models/`, `work/` and `tmp/`, made with the rest.
- `ponzi-models prepare --out` and `train --out` default to the home's `training/` (`train --prepared` still defaults to `--out`); `export --models-root` to the home's `models/`.
- `ponzi-models standard-workflow --out` defaults to `<home>/standards/<id>-<version>.yaml`, `<home>` being `--home` or the PONZI home: where that home's server reads its standards.
- `ponzi-pipeline`'s coherence commands' `--work` defaults to the home's `work/`.
- `ponzi_spec.config.local_scratch`: `roots.scratch` (default `{data}/tmp`) as a local folder, made, or None for a remote one. ISCE3's geocoding scratch is made there (the system's temporary folder when None), and still removed after use.
- `train --preflight` sets wandb's folders to the training root's `wandb/`, as a fit already sets them to its own `wandb/`.
- The five help texts say the PONZI home's `registry/`.
- The models tests each get their own PONZI home, as the other suites' do.

## Do results change?
No. Where a command writes is never part of an identity: the prepared files' tag, a fit, an artifact's digest and every content id are the same wherever they are written.

## Tests
`test_home_catalog.py`: the four folders. `test_config.py`: `local_scratch` is the home's `tmp/`, a given local root, or None for a remote one. `test_commands.py`: `--work` defaults to the home's `work/`. `test_home_defaults.py`: `prepare` and `train` default to the home's `training/`, `export` to its `models/`, `standard-workflow` to `<home>/standards/<id>-<version>.yaml`. The ISCE3 tests in the `isce3` environment.

## Version
Library: `ponzi-spec`, `ponzi-pipeline` and `ponzi-models` minor (optional arguments that were required; new defaults). Standard: no change.
