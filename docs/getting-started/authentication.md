# Logins and keys

What each part of PONZI needs to log in to, and where to put it. A secret is never written in a PONZI file, a standard or a repository: each one is read from the environment or from the file its own tool reads.

## What needs what

| Credential | Needed by | Required for | Where it goes |
| --- | --- | --- | --- |
| **Earthdata Login** (NASA) | the worker, `ponzi-pipeline acquire` | downloading the SLCs and orbit files from ASF | `EARTHDATA_USERNAME` and `EARTHDATA_PASSWORD`, else `~/.netrc` |
| **Earth Data Hub** token (DestinE) | the worker, onboarding with weather source `edh` or `edh_cdsgrid` | ERA5-Land weather for the sidecar | `~/.netrc` |
| **Copernicus CDS** key | the worker, onboarding with weather source `cdsgrid` or `edh_cdsgrid` | ERA5-Land weather newer than the Earth Data Hub store | `~/.cdsapirc` |
| **PONZI server key** | `ponzi-client` (and its loop, `ponzi-client serve`), a person logging in to ponzi-visual, the app itself | every call to a running server | `PONZI_KEY` (or the variable `--key-env` names), else the file `$PONZI_KEY_FILE`; a person types theirs into the app's login form; the app's own key in `PONZI_VISUAL_KEY_FILE` |
| **wandb** key | `ponzi-models train` with `--wandb online` (its default) | logging training runs | wandb's own: `WANDB_API_KEY` or `wandb login` |

Needs no login: ASF's burst search (`discover`, and the server's [burst availability](../service/rest-api.md)), the Copernicus GLO-30 DEM, the GHSL built-up layers and the World Bank boundaries the server downloads.

A machine needs only the credentials of what runs on it. The server needs none to reach out: it holds the hashes of the PONZI keys and calls nothing that needs a login. A machine that carries out jobs needs Earthdata and the weather source of its onboarding spec for the worker, and a `worker` key for its client loop (the worker itself talks to no server).

## The `~/.netrc` file

Earthdata and the Earth Data Hub are read from one file: `$NETRC` when that is set, else `~/.netrc`. One line per host:

```
machine urs.earthdata.nasa.gov login YOUR_EARTHDATA_USERNAME password YOUR_EARTHDATA_PASSWORD
machine data.earthdatahub.destine.eu password YOUR_EDH_TOKEN
```

Make it readable by you only:

```
chmod 600 ~/.netrc
```

- **Earthdata.** Register at [urs.earthdata.nasa.gov](https://urs.earthdata.nasa.gov). `login` is the username, not the email address. Downloads from ASF also need the application *Alaska Satellite Facility Data Access* approved under *Applications › Authorized Apps* of the Earthdata profile; without it, the login answers 401. When `EARTHDATA_USERNAME` and `EARTHDATA_PASSWORD` are both set, they win over `~/.netrc`.
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

Keys are made on the server's machine, with the server running or not. An admin user can also make people's keys in the app (below).

```
ponzi-server keys add --scope worker --name hpc-worker --out ~/hpc-worker.key
ponzi-server keys list
ponzi-server keys revoke hpc-worker
```

| Scope | Can | For |
| --- | --- | --- |
| `user` | read areas, jobs and outputs; ask for areas to be watched | a person using the app (or Python, or the command line) |
| `user-admin` | that, and approve or deny watch requests; pause, resume, look now at and delete areas and tracts; make and revoke `user` and `user-admin` keys | a person who runs the lab's PONZI |
| `visual` | log a person in and pass their session on; nothing else | the app itself: its dev server or the deployment's reverse proxy |
| `client:read` | read areas, requests, jobs and outputs | scripts and agents |
| `client:write` | that, and create, change and delete areas directly, and submit runs | scripts and agents |
| `worker` | claim jobs, heartbeat and deliver outputs: the key of `ponzi-client serve` | the client loop |
| `admin` | everything | the server's operator |

Make the first `user-admin` key on the server's machine (`ponzi-server keys add --scope user-admin --name YOUR_NAME --out ...`); that person then makes everyone else's in the app.

A key is shown once, when it is made: `--out` writes it to a new file only its owner can read. Move that file to the machine that uses it, then point the client at it:

```
export PONZI_KEY_FILE=~/hpc-worker.key      # a file keeps the key out of the environment of a shared node
# or
export PONZI_KEY=pz_...
```

`--key-env` may name another variable (`--key-env PONZI_WORKER_KEY`); the file `$PONZI_KEY_FILE` is read when that variable is unset.

## Logging in to the app

ponzi-visual never keeps a key in the browser (ponzi-core CR-093):

- **The app's own key** (scope `visual`) is added to every call by whatever serves the app: Vite's dev server reads it from `PONZI_VISUAL_KEY`, else the file `PONZI_VISUAL_KEY_FILE`, else the demo's `keys.json`; in a deployment, the reverse proxy adds it. The browser never sees it.
- **A person logs in with their own key** (`user` or `user-admin`). The server swaps it for a session cookie the page cannot read (`HttpOnly`), kept 14 days (the server setting `session_days`); the server keeps only the hash of the session's token. Every call through the app then acts as that person, and the access log names them.
- **Log out** ends the session on the server. Revoking a key ends all of its sessions.
- Python, the command line and agents keep sending a key as `Authorization: Bearer <key>`; a `user` key works there too.

## On the cluster

The worker's SLURM jobs run as you, so they read the same `~/.netrc` and `~/.cdsapirc` from the cluster's home folder: put them there once, mode 600. Prefer the files to `EARTHDATA_PASSWORD` in a job script, which other users may see in the job's environment. A home folder shared between nodes needs nothing else.

## Checking

A failed login names its source, never the secret:

| Message | Means |
| --- | --- |
| `no Earthdata credentials: set EARTHDATA_USERNAME and EARTHDATA_PASSWORD, or add ...` | neither the variables nor an entry in `~/.netrc` for `urs.earthdata.nasa.gov` were found |
| `ASFAuthenticationError ... 401 Unauthorized` | the entry was found and refused: the username or password is wrong, or the ASF application is not approved |
| `<file>: ... (line N)` | `~/.netrc` does not parse |
| `401 a valid key is needed` | the server key is missing, revoked or mistyped |
| `401 log in first` | the app's own key came without a person's session: log in to the app again |
| `403` | the key is valid but its scope does not allow the call |
