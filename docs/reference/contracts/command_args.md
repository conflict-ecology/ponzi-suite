# C4b: Command arguments

`ponzi.core.cli` (package `packages/core`). One definition of accepted keys per command, typed, with cross-field validation, from three sources with a fixed precedence, and a `model_dump()` for the meta files.

## Pattern

Each command below defines a `pydantic_settings.BaseSettings` subclass of `ponzi.core.cli.CommandArgs` (`env_prefix="PONZI_"`, `extra="forbid"`). The argparse subparser is generated from the model fields (`add_model_arguments`): one `--flag` per field (underscores as dashes), `BooleanOptionalAction` for booleans (`--x` / `--no-x`), `append` for a list field (the flag repeated), choices from `Literal` annotations, the field's `description` as help, positional arguments where the command names them. Every generated argument defaults to `None`. Each subcommand also takes `--args-file`.

Resolution (`resolve_args`): the `--args-file` yaml mapping is loaded first (a non-mapping is an error, and there is no `extends:` composition), every flag given overrides it, then the model is constructed, so `PONZI_<FIELD>` environment variables (e.g. `PONZI_THREADS`) fill what neither set, and the model defaults fill the rest. Precedence: flags > args file > environment > defaults. A validation error is a usage error.

The scoring spec (C4) is NOT a settings model: it is an identity, not an invocation.

The other `ponzi` subcommands (`pvalues`, `detect`, `detect-path`, `tile`, `validate-store`, dispatched by `ponzi.cli` before `ponzi.core.cli`) and the `ponzi-pipeline` and `ponzi-models` commands are plain argparse. A worker stage takes its arguments as the pydantic models of its `StageSpec` (`identity_params`, `request_params`).

## Commands

| Command | Model |
|---|---|
| `ponzi run` | `ponzi.core.runner.RunRequest` (C4a) |
| `ponzi replay SCORE --out PATH` | `ReplayArgs`: `score`, `out`, optional `alpha`, `delta`, `recovery_steps`, `nms_window`, `noise_floor`, `label` (C8) |
| `ponzi forecasting-summary --stats FILE` | `ForecastingSummaryArgs`: `stats`, `window` (`t_lo,t_hi`, both inclusive), `out` (C10) |

## Invariants

- A field is defined once, in the model; the parser carries no defaults of its own.
- `model_dump()` of the resolved model is what a command records in its meta file (`run_meta.request`, C9, for `ponzi run`).
