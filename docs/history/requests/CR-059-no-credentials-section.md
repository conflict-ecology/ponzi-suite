# CR-059: the unused credentials section removed

- **Requested by / date:** owner, 2026-11-05 ("remove it if that is okay").
- **Status:** implemented on the owner's instruction (2026-11-05)

## Why

The deployment config had a `credentials: {file: ...}` section naming a dotenv file for secrets, but no command read it. Secrets come from elsewhere:
- Earthdata from `EARTHDATA_USERNAME` and `EARTHDATA_PASSWORD`, or the netrc file (CR-044);
- the CDS from `~/.cdsapirc`;
- the server key from the variable `server.key_env` names.

The section only invited a wrong expectation.

## What changes

- `ponzi_spec.config.Credentials` and `DeploymentConfig.credentials` are removed, and with them the variable `PONZI_CREDENTIALS__FILE`.
- A config that still has a `credentials` section is refused, and the error says where each secret comes from.
- The configuration page and the roadmap follow.

## Do results change?

No.

## Tests

ponzi-spec `test_config.py`: the section is refused with the answer, and the field is gone.

## Version

`ponzi-spec`: minor. A config file with the section now fails to load; none in these repositories has one.
