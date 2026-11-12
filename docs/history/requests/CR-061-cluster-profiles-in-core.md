# CR-061: cluster profiles in ponzi-core, saved in the home

- **Requested by / date:** owner, 2026-11-05 ("add in ponzi-core modules the worker can use to produce a profile of the slurm system, to be saved in the right spot").
- **Status:** implemented on the owner's instruction (2026-11-05)
- **Superseded in part:** the shipped `ceoas` profile and snapshot were removed (CR-065), and approval with them (CR-062). A site's `roots.data` and the profile's `cache` are gone; `{data}` in a profile means the PONZI home (CR-088).

## Why

The worker made its SLURM profile with code of its own (`ponzi_worker.profiles`) and saved it under `~/.config/ponzi-service/`, outside the PONZI home. The code that plans work belongs in ponzi-core, which the worker uses, and everything an installation makes on a machine belongs in its home.

## What changes

- **`ponzi_spec.cluster`** (moved from `ponzi_worker.profiles`, unchanged in what it makes):
  - `Profile`, `Partition`, `StageResources` and `load_profile`; the shipped profile `profiles/ceoas.yaml`.
  - `ponzi_spec.cluster.create`: the site file (`sites/ceoas.yaml`), the snapshot's read-only SLURM queries (`SNAPSHOT`, `take_snapshot`, and `snapshot.sh` for doing it by hand), `read_snapshot`, `create_profile`, `profile_at_start`, and the command `python -m ponzi_spec.cluster.create`.
  - The snapshot the shipped profile is made from, `snapshots/ceoas/2026-10-27/`, ships beside it (`shipped_snapshot`), so the profile can be checked against its source wherever ponzi-spec is installed.
  - Standard library, pydantic and PyYAML only, as the rest of ponzi-spec.
- **Where it is saved:** `ponzi_spec.home.Layout.cluster`, `{home}/cluster/`, made with the home:
  - `profiles/<site>.yaml` (the current one) and `profiles/<site>-<version>.yaml` (every version made);
  - `snapshots/<site>/<YYYY-MM-DDTHHMMSS>/` (the last 10).
  - The home is the deployment config's `roots.data` (a cluster's shared root), else `$PONZI_HOME`, else `~/.ponzi`. `cluster_folder()` gives it.
- **ponzi-worker** imports the profile from `ponzi_spec.cluster`; `ponzi-worker profile` runs `ponzi_spec.cluster.create`; `serve` and `run` with `--executor slurm` and no `--profile` save into the worker home's `cluster/` folder. `ponzi_worker.profiles` and `packages/worker/reference/clusters/` are removed.

## Do results change?

No. The profiles made are the same, byte for byte (the shipped `ceoas` profile is unchanged and still checked against what the command makes). Profiles saved before under `~/.config/ponzi-service/` are not read: the first start makes a new version in the home, so batches rendered before and still waiting for approval are rendered again with a new id.

## Tests

ponzi-spec `test_profile_create.py` (moved from the worker): the shipped profile is exactly what the command makes; profiles are saved in `{home}/cluster/` under `$PONZI_HOME` or a given home; the shipped snapshot is found where the package is installed; the earlier cases (restarts, changes, refusals, no SLURM, the script's queries). The worker's `test_slurm.py` reads the shipped snapshot through `shipped_snapshot`.

## Version

- `ponzi-spec`: minor (new module).
- ponzi-worker: minor (the profile's folder moves).
