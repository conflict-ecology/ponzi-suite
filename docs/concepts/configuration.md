# Configuration

## The deployment config

Each installation (a laptop, a cluster account, a cloud deployment) has one `ponzi.yaml`. Every distribution reads it the same way (`ponzi_spec.config.load_config`).

```yaml
roots:                          # plain paths or URIs: file://, s3://, gs://
  data: /storage/ponzi/data     # required
  cache: /storage/ponzi/cache   # default {data}/cache
  registry: s3://bucket/registry  # default {data}/registry
  scratch: /tmp/ponzi           # default {data}/tmp
server: {url: https://ponzi.example.org, key_env: PONZI_KEY}
credentials: {file: ~/.config/ponzi/credentials.env}
cluster_profile: ceoas@2026.11  # workers on a SLURM cluster
```

**Where it is read from**: the first file that exists of `--config`, `$PONZI_CONFIG`, `./ponzi.yaml`, `$XDG_CONFIG_HOME/ponzi/config.yaml` (default `~/.config`).

**Precedence**: command-line overrides > environment > file > defaults. Environment names nest with a double underscore:

| Variable | Sets |
| --- | --- |
| `PONZI_ROOTS__DATA`, `PONZI_ROOTS__CACHE`, ... | `roots.*` |
| `PONZI_SERVER__URL`, `PONZI_SERVER__KEY_ENV` | `server.*` |
| `PONZI_CREDENTIALS__FILE` | `credentials.file` |
| `PONZI_CLUSTER_PROFILE` | `cluster_profile` |
| `PONZI_DATA_ROOT`, `PONZI_MODEL_REGISTRY` | older aliases of `roots.data` and `roots.registry`, below the names above |

Other `PONZI_*` variables belong to individual commands (for example the run's arguments) and are not part of this config.

## Paths

Code never holds a hostname, a cluster path or a user name. A location is a `pathlib.Path` when local and a URI string when remote (`ponzi_spec.paths`: `is_local`, `to_path`, `join`), so the same installation works on a laptop, a cluster and object storage by changing the config only.

## Secrets

Keys and credentials (Earthdata, CDSE, the Copernicus CDS, wandb, the server key) are read from the environment or from the dotenv file `credentials.file` names, never from `ponzi.yaml`.

## Other configs

| Config | Defines | Hashed |
| --- | --- | --- |
| run config | the forecast, scoring, aggregation and state machine of a run | yes (`config_hash`) |
| coherence config | backend, looks, window, grid, DEM | yes |
| onboarding config | the sidecar's steps and sources | recorded |
| detection recipe | how codes become events | yes (`digest`) |
| standard | the bundle a watched area runs: all of the above, the model and the calibrations | by version |
| cluster profile | partitions, environments and resources of one SLURM cluster | by version |
