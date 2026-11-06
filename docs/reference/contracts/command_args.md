# C4b: Command arguments

Status: implemented, `ponzi.core.cli` (package `packages/core`).

## Purpose

One definition of accepted keys per command, typed, with cross-field validation, from three sources with a fixed precedence, and a `model_dump()` for stamping into meta files.

## Pattern

Every command of `ponzi.core.cli` (the table below) defines a `pydantic_settings.BaseSettings` subclass (`ponzi.core.cli.CommandArgs` base: `env_prefix="PONZI_"`, `extra="forbid"`). The argparse subparser is generated from the model fields (`add_model_arguments`): one `--flag` per field (underscores as dashes), `BooleanOptionalAction` for booleans (`--x` / `--no-x`), `append` for a list field (the flag repeated), choices from `Literal` annotations, the field's `description` as help, positional arguments where the command names them. Every generated argument defaults to `None`. Each subcommand also takes `--args-file`.

The other `ponzi` subcommands (`pvalues`, `detect`, `detect-path`, `tile`, `validate-store`, dispatched by `ponzi.cli.main` before `ponzi.core.cli`, so `ponzi --help` lists only the three below) and the `ponzi-pipeline` and `ponzi-models` commands are plain argparse and do not follow this pattern; a ponzi-worker stage takes its arguments as pydantic models of its `StageSpec` (`identity_params`, `request_params`).

Resolution (`resolve_args`): the `--args-file` yaml mapping is loaded first (a non-mapping is an error), then every flag that was given overrides it, then the model is constructed, so environment variables (`PONZI_<FIELD>`, e.g. `PONZI_THREADS`) fill what neither flags nor file set, and the model defaults fill the rest. Precedence: flags > args file > environment > defaults. A validation error is reported as a usage error.

The scoring spec (C4) is NOT a settings model: it is a plain pydantic model loaded from (composable) yaml, because it is an identity, not an invocation. The args file is read as plain yaml, without `extends:` composition.

## Commands

| Command | Model |
|---|---|
| `ponzi run` | `ponzi.core.runner.RunRequest` (C4a) |
| `ponzi replay SCORE --out PATH` | `ponzi.core.cli.ReplayArgs` (`score`, `out`, optional `alpha`, `delta`, `recovery_steps`, `nms_window`, `noise_floor`, `label`) |
| `ponzi forecasting-summary --stats FILE` | `ponzi.core.cli.ForecastingSummaryArgs` (`stats`, `window` `t_lo,t_hi` inclusive, `out`) |

## Invariants

- A field is defined once, in the model; the parser never carries its own defaults.
- `model_dump()` of the resolved model is what a stage stamps into its meta file (`run_meta.request`, C9, for `ponzi run`).
