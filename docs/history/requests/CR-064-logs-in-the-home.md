# CR-064: every log in the PONZI home

- **Requested by / date:** owner, 2026-11-05 ("lets make all the logs together in ponzi-home")
- **Status:** implemented on the owner's instruction (2026-11-05)

## Why

The SLURM tasks wrote their output to the site file's `{data}/logs`, a folder set apart from the PONZI home, and the client loop's job wrote wherever it was submitted from. The two met only if the cluster's `ponzi.yaml` and the site file named the same data root.

## What changes

- **`ponzi_spec.home.Layout.logs`**, `$PONZI_HOME/logs/`, made with the home: `slurm/<batch>/` the output of each SLURM task of a batch (`<stage>_<job>_<task>.out`), `client/` the client loop's own log.
- **`ponzi_spec.cluster`:** the profile and the site file lose `logs`; the shipped `ceoas` profile is made again from its snapshot and loses only that line.
- **ponzi-worker:** `prepare` takes the home's `logs/slurm` (`ponzi-worker job` and `run` pass their home's), renders `--output` into `logs/slurm/<batch>/`, makes that folder before submission (SLURM does not), and records it in `batch.json` (`logs`).
- **The cluster guide:** the client loop's job is submitted with `--output="$PONZI_HOME/logs/client/%x_%j.out"`; on the login node its output is sent to the same folder.

## Do results change?

No. Only where the logs are written.

## Tests

ponzi-worker `test_slurm.py`: the rendered scripts write into the given log folder; a submitted batch's folder is `$PONZI_HOME/logs/slurm/<batch>`, made, and named in `batch.json`. ponzi-spec: `Layout.make` makes `logs/`; the shipped profile is still exactly what the command makes.

## Version

- `ponzi-spec`: minor. ponzi-worker: minor.
