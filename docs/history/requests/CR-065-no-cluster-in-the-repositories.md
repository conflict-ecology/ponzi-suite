# CR-065: no cluster in the repositories; the site file and the profile in the home

- **Requested by / date:** owner, 2026-11-05 ("remove all ceoas references including the cluster profile from code and docs. (move that to ~/.ponzi for now) all worker jobs should check for it and run based on the spec and create it if it does not exist.")
- **Status:** implemented on the owner's instruction (2026-11-05)

## Why

One cluster's site file, profile and snapshot (with its node names, paths, accounts and job history) shipped inside ponzi-spec, the worker defaulted to that site, and the tests and docs named it. A cluster's description belongs to the installation that runs on it, not to the code.

## What changes

- **Nothing of a cluster is shipped.** `ponzi_spec.cluster` keeps the models, the snapshot's queries, `create_profile` and `snapshot.sh`; the shipped `sites/`, `profiles/` and `snapshots/` are removed. They were moved, unchanged, to `~/.ponzi/cluster/` on the owner's machine (`sites/`, `profiles/`, `snapshots/`), with the port-reference job files and the lab's former job scripts for reference.
- **Everything is read from the home's cluster folder,** `$PONZI_HOME/cluster/`: `load_site(name)` reads `sites/<name>.yaml`, `load_profile(name)` reads `profiles/<name>.yaml`; a file path still works for both. A missing one says where to write it.
- **Every SLURM job checks for the profile and makes it** (`create.current_profile`): the site's current profile when there is one, else one made from a snapshot of the cluster and the site file, saved in the home. `--site` names the site; with one site file in the home, it is that one (`site_name`); with none, the job fails saying where to write it. `ponzi-worker profile` (no `--snapshot`) makes it again from a new snapshot.
- **The port-reference kit** (`packages/pipeline/reference/phase0`) holds only the resources: the partition, account, nodes to avoid and log file are given to `sbatch` from the site file, and `DR` and `CORE` are required variables. `snapshot.sh` requires `ROOTS` and `RELEASES` and writes into `$PONZI_HOME/cluster/snapshots/`.
- **Tests** use a made-up cluster: ponzi-spec's on a small synthetic snapshot and site file, ponzi-worker's on a made-up profile. The comparison of rendered scripts with the lab's former job files is removed with those files.
- **Docs and examples** name no cluster (`mycluster@2026.11.05` in the config examples).

## Do results change?

No. A profile made from the same snapshot and site file is the same.

## Tests

ponzi-spec `test_profile_create.py`: nothing of a cluster is shipped; a job makes the profile when there is none and reuses it after; a new snapshot keeps the version of an unchanged cluster; the site is named or the only one, and a missing site or profile says where it goes; no SLURM says so; profiles are saved in the home. ponzi-worker `test_slurm.py`: a script is rendered from the profile (partition, account, nodes, GPUs, resources, environment, exports, logs). ponzi-pipeline `test_port_check.py`: the kit's job files hold no cluster.

## Version

- `ponzi-spec`: minor (the shipped profile is gone; `load_site`/`load_profile` read the home). ponzi-worker: minor (`--site` has no default site).
