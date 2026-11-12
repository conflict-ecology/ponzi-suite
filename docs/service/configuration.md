# Configuration

## The PONZI home

Everything an installation keeps lives in one folder, the PONZI home: `$PONZI_HOME`, else `~/.ponzi` (`ponzi_spec.home`, its layout fixed by `Layout`). Nothing else names a folder (CR-088): the server, the worker, the client loop, the SLURM tasks and every command run by hand read and write there, and there is no config file that moves a part of it elsewhere. To run on other storage, set `PONZI_HOME`; on a cluster, set it to storage the login node and the compute nodes share ([Running on the cluster](hpc.md#where-the-client-loop-runs)). The server and the worker make the folders when they start. The layout and every environment variable are in [Paths and environment variables](../getting-started/paths.md).

What is not a folder is set where it is used:

| What | Where |
| --- | --- |
| the server a client or the client loop talks to | `--url`, else `$PONZI_URL` |
| the key | `$PONZI_KEY` (or the variable `--key-env` names), else the file `$PONZI_KEY_FILE` |
| how the server runs (leases, outputs mode, downloads, database server) | its settings file ([The server](server.md#settings)) |
| the SLURM cluster | the site file and the profile in `$PONZI_HOME/cluster/` ([Running on the cluster](hpc.md#the-profile)) |

## Paths

Code never holds a hostname, a cluster path or a user name: every folder is a part of the home (`pathlib.Path`, through `ponzi_spec.home`), so the same code runs on a laptop and a cluster by setting `PONZI_HOME` only.

## Secrets

Keys and credentials are read from the environment or from the files their own tools read, never from a PONZI file. [Authentication](../getting-started/authentication.md) says what each credential is for and where it goes.

## Composition

Every spec (training, scoring, panel, detection, coherence and onboarding) and every standard composes (`ponzi_spec.compose`). `extends:` names a file, or a list of files merged in order, relative to the file that writes it, at the top of a document or opening any mapping inside one. Mappings merge key by key; lists, values and null replace what the base had; the file's own keys win. A spec is validated and hashed as composed, so a composed file and its flat equal have the same hash.

## Specs and other configs

| File | Defines | Hashed |
| --- | --- | --- |
| scoring spec | the forecast, scoring, aggregation and state machine of a run | yes (`spec_hash`) |
| coherence spec | backend, looks, window, grid, DEM | yes (`spec_hash`) |
| onboarding spec | the sidecar's steps and sources | yes (`spec_hash`) |
| detection spec | how codes become events | yes (`spec_hash`) |
| training spec, panel spec | how a model is trained, how a panel is built | yes (`spec_hash`) |
| standard | the bundle a watched area runs: its panel, coherence, onboarding and detection specs by name, the model, its scoring spec by hash, and the calibrations | by version, held to its hash in the registry |
| cluster profile | partitions, environments and resources of one SLURM cluster | by version |

Where the specs live, how they are named and how their hashes are recorded: [Naming](../models/naming.md#spec-folders) and [Standard versions](../models/versions.md#specs-a-name-and-a-hash).
