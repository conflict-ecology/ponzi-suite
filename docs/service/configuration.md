# Configuration

## The deployment config

Each installation (a local machine, a cluster account, a cloud deployment) has one `ponzi.yaml`. Every distribution reads it the same way (`ponzi_spec.config.load_config`).

```yaml
roots:                          # plain paths or URIs: file://, s3://, gs://
  data: /storage/ponzi/data     # default the PONZI home ($PONZI_HOME, else ~/.ponzi)
  cache: /storage/ponzi/cache   # default {data}/cache
  registry: s3://bucket/registry  # default {data}/registry
  scratch: /tmp/ponzi           # default {data}/tmp
server: {url: https://ponzi.example.org, key_env: PONZI_KEY}
cluster_profile: mycluster@2026.11.05  # workers on a SLURM cluster
```

**Where it is read from**: the first file that exists of `--config`, `$PONZI_CONFIG`, `./ponzi.yaml`, `$XDG_CONFIG_HOME/ponzi/config.yaml` (default `~/.config`).

**Precedence**: command-line overrides > environment > file > defaults. Environment names nest with a double underscore:

| Variable | Sets |
| --- | --- |
| `PONZI_ROOTS__DATA`, `PONZI_ROOTS__CACHE`, ... | `roots.*` |
| `PONZI_SERVER__URL`, `PONZI_SERVER__KEY_ENV` | `server.*` |
| `PONZI_CLUSTER_PROFILE` | `cluster_profile` |
| `PONZI_DATA_ROOT`, `PONZI_MODEL_REGISTRY` | older aliases of `roots.data` and `roots.registry`, below the names above |

Other `PONZI_*` variables belong to individual commands (for example the run's arguments) and are not part of this config.

## Paths

Code never holds a hostname, a cluster path or a user name. A location is a `pathlib.Path` when local and a URI string when remote (`ponzi_spec.paths`: `is_local`, `to_path`, `join`), so the same installation works on a local machine, a cluster and object storage by changing the config only.

## Secrets

Keys and credentials (Earthdata, the Copernicus CDS, wandb, the server key) are read from the environment or from the files their own tools read, never from `ponzi.yaml`. Earthdata, for the ASF downloads, comes from `EARTHDATA_USERNAME` and `EARTHDATA_PASSWORD`, or else from the `urs.earthdata.nasa.gov` entry of the netrc file (`$NETRC`, else `~/.netrc`). The CDS reads `~/.cdsapirc`. The config has no credentials section: the former `credentials.file`, which no command read, is refused with this answer (CR-059). [Authentication](../getting-started/authentication.md) says what each credential is for and where it goes.

## The PONZI home

Everything an installation computes lives in one folder, the PONZI home: `$PONZI_HOME`, else `~/.ponzi` (`ponzi_spec.home`). These docs write it `$PONZI_HOME`, the variable that sets it. A worker's home is `roots.data` of its `ponzi.yaml` when that is a local path; `roots.data` itself defaults to the PONZI home, so without a config a worker's home is `$PONZI_HOME` (`~/.ponzi`) too ([The worker](worker.md)). Its full structure and every environment variable are in [Paths and environment variables](../getting-started/paths.md). Its layout is fixed (`Layout`): `server/`, `keys/`, `standards/`, `outputs/`, `catalog/`, `cache/`, `registry/`, `panels/`, `downloads/` (`slc/`, `orbits/`, `dem/`), `cluster/` (the SLURM sites, the profiles a worker makes and their snapshots, CR-061; no cluster is shipped in the repositories, CR-065) and `logs/` (every log written to files: `slurm/<batch>/` the SLURM tasks', `client/` the client loop's when it runs as a SLURM job, CR-064). The server and the worker create it when they start. The repositories hold only code and the files PONZI runs from, so a home copied to another machine runs unchanged with the same repositories.

## Composition

Run configs, fit specs, recipes, standards, panel specs, and coherence and onboarding configs compose (`ponzi_spec.compose`). `extends:` names a file, or a list of files merged in order, relative to the file that writes it, at the top of a document or opening any mapping inside one. Mappings merge key by key; lists, values and null replace what the base had; the file's own keys win. A config is validated and hashed as composed, so a composed file and its flat equal have the same hash.

## Other configs

| Config | Defines | Hashed |
| --- | --- | --- |
| run config | the forecast, scoring, aggregation and state machine of a run | yes (`config_hash`) |
| coherence config | backend, looks, window, grid, DEM | yes |
| onboarding config | the sidecar's steps and sources | recorded |
| detection recipe | how codes become events | yes (`digest`) |
| standard | the bundle a watched area runs: all of the above, the model and the calibrations | by version |
| cluster profile | partitions, environments and resources of one SLURM cluster | by version |
