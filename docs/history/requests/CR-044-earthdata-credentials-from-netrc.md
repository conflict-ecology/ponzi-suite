# CR-044: Earthdata credentials from the netrc file

- **Requested by / date:** owner, 2026-11-04 ("is there a way for it all to go through netrc?", then "yes"), to run the coherence chain for the Gaza suite case on a laptop.
- **Status:** implemented on the owner's instruction (2026-11-04), awaiting review; uncommitted

## Why

The pipeline's two downloads authenticate differently:
- **Weather onboarding** (Earthdata Hub) reads a token from `~/.netrc`.
- **SLC and orbit downloads** from ASF (`acquire.earthdata_session`) accept only `EARTHDATA_USERNAME` and `EARTHDATA_PASSWORD` in the environment.

On a workstation that keeps its Earthdata login in `~/.netrc`, which is the usual place and what NASA's own tools read, the ASF session refuses to start.

## What changes

`ponzi_pipeline.acquire.earthdata_credentials(env)` returns `(user, password, where)`:
1. `EARTHDATA_USERNAME` and `EARTHDATA_PASSWORD`, when both are set. This is unchanged, and it is what the HPC jobs use.
2. Otherwise, the `urs.earthdata.nasa.gov` entry of the netrc file: `$NETRC` if set, else `~/.netrc`. It is read with Python's `netrc` module, which refuses a file that others can read.
3. Otherwise, PermissionError, naming both ways to provide them.

`where` names the source (never the secret), for logs. `earthdata_session` logs in with those credentials, through `ASFSession().auth_with_creds` as before. Credentials still never come from a PONZI config.

## Do results change?

No. Only how the download logs in changes.

## Tests

`test_coherence_chain.py`:
- the netrc entry is used; the environment wins when both variables are set; one variable alone falls back to the netrc;
- without `$NETRC`, the lookup uses `$HOME/.netrc`;
- a netrc without the host, a missing file, and a malformed entry are refused, and the message carries no secret;
- the existing refusal test points `$NETRC` at a missing file, so it never reads the machine's own.

## Version

ponzi-pipeline: minor (a new credential source; the old one unchanged).
