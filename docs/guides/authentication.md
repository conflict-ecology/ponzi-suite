# Authentication

What each part of PONZI needs to log in to, and where to put it. A secret is never written in a PONZI config, a standard or a repository: each one is read from the environment or from the file its own tool reads (`ponzi.yaml` refuses a `credentials:` section, CR-059).

## What needs what

| Credential | Needed by | Required for | Where it goes |
| --- | --- | --- | --- |
| **Earthdata Login** (NASA) | the worker, `ponzi-pipeline acquire` | downloading the SLCs and orbit files from ASF | `EARTHDATA_USERNAME` and `EARTHDATA_PASSWORD`, else the netrc file |
| **Earth Data Hub** token (DestinE) | the worker, onboarding with weather source `edh` or `edh_cdsgrid` | ERA5-Land weather for the sidecar | the netrc file |
| **Copernicus CDS** key | the worker, onboarding with weather source `cdsgrid` or `edh_cdsgrid` | ERA5-Land weather newer than the Earth Data Hub store | `~/.cdsapirc` |
| **PONZI server key** | the worker, `ponzi-client`, ponzi-visual | every call to a running server | `PONZI_KEY` (or the variable `server.key_env` names), else the file `$PONZI_KEY_FILE` |
| **wandb** key | `ponzi-models train` with tracking `online` | logging training runs | wandb's own: `WANDB_API_KEY` or `wandb login` |

Needs no login: ASF's burst search (`discover`, and the server's [burst availability](../reference/rest-api.md)), the Copernicus GLO-30 DEM, the GHSL built-up layers and the World Bank boundaries the server downloads.

A machine needs only the credentials of what runs on it. The server needs none to reach out: it holds the hashes of the PONZI keys and calls nothing that needs a login. A worker that runs whole workflows needs Earthdata, the weather source of its onboarding config, and a `worker` key.

## The netrc file

Earthdata and the Earth Data Hub are read from one file: `$NETRC` when that is set, else `~/.netrc`. One line per host:

```
machine urs.earthdata.nasa.gov login YOUR_EARTHDATA_USERNAME password YOUR_EARTHDATA_PASSWORD
machine data.earthdatahub.destine.eu password YOUR_EDH_TOKEN
```

Make it readable by you only:

```
chmod 600 ~/.netrc
```

- **Earthdata.** Register at [urs.earthdata.nasa.gov](https://urs.earthdata.nasa.gov). `login` is the username, not the email address. Downloads from ASF also need the application *Alaska Satellite Facility Data Access* approved under *Applications › Authorized Apps* of the Earthdata profile; without it, the login answers 401. When `EARTHDATA_USERNAME` and `EARTHDATA_PASSWORD` are both set, they win over the netrc file.
- **Earth Data Hub.** Register at [earthdatahub.destine.eu](https://earthdatahub.destine.eu/getting-started) and make a personal access token; the token is the `password`, and the line needs no `login`.

## The CDS file

The Copernicus Climate Data Store reads `~/.cdsapirc`, as its own `cdsapi` client does. Register at [cds.climate.copernicus.eu](https://cds.climate.copernicus.eu), accept the licence of the ERA5-Land dataset on its download page, and copy the key from the profile page:

```
url: https://cds.climate.copernicus.eu/api
key: YOUR_CDS_KEY
```

```
chmod 600 ~/.cdsapirc
```

## PONZI server keys

The server's own keys are made on the server's machine, with the server running or not:

```
ponzi-server keys add --scope worker --name hpc-worker --out ~/hpc-worker.key
ponzi-server keys list
ponzi-server keys revoke hpc-worker
```

| Scope | Can |
| --- | --- |
| `client:read` | read areas, requests, jobs and outputs |
| `client:write` | that, and create areas and submit runs |
| `worker` | claim jobs, heartbeat and deliver outputs: the key of `ponzi-client serve` |
| `admin` | everything |

A key is shown once, when it is made: `--out` writes it to a new file only its owner can read. Move that file to the machine that uses it, then point the client or the worker at it:

```
export PONZI_KEY_FILE=~/hpc-worker.key      # a file keeps the key out of the environment of a shared node
# or
export PONZI_KEY=pz_...
```

The deployment config may name another variable (`server: {url: ..., key_env: PONZI_WORKER_KEY}`); the file `$PONZI_KEY_FILE` is read when that variable is unset. ponzi-visual asks for a key in the browser and sends it as `Authorization: Bearer <key>`, as every client does.

## On the cluster

The worker's SLURM jobs run as you, so they read the same `~/.netrc` and `~/.cdsapirc` from the cluster's home folder: put them there once, mode 600. Prefer the files to `EARTHDATA_PASSWORD` in a job script, which other users may see in the job's environment. A home folder shared between nodes needs nothing else.

## Checking

A failed login names its source, never the secret:

| Message | Means |
| --- | --- |
| `no Earthdata credentials: set EARTHDATA_USERNAME and EARTHDATA_PASSWORD, or add ...` | neither the variables nor a netrc entry for `urs.earthdata.nasa.gov` were found |
| `ASFAuthenticationError ... 401 Unauthorized` | the entry was found and refused: the username or password is wrong, or the ASF application is not approved |
| `<file>: ... (line N)` | the netrc file does not parse |
| `401 a valid key is needed` | the server key is missing, revoked or mistyped |
| `403` | the key is valid but its scope does not allow the call |
