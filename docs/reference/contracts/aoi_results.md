# C16: AOI results

> Note (2026-11-04): only the design table is in this repository, `ponzi.evaluation.events`. The AOI metric tables, the paired matrices and the AOI mosaics (`ponzi_pipeline.aggregate`, `ponzi.evaluation.aggregate`, `ponzi-pipeline aggregate`) are not in this repository.

Status: implemented 2026-09-07, extended 2026-09-16; here the design table, `ponzi.evaluation.events`.

## Purpose

The output of the evaluation primitive: every row of a design comparison, per event and summarised, in one long format. It consumes row sets (C20) built from runs (C7, C8) and label stores (C11) and never re-runs anything.

## Producer and consumers

Producer: `ponzi.evaluation.events` (`event_metric`, `pooled`, `across_events`), written by `write_design_table` (sorted parquet, zstd, byte reproducible) to a path the caller names, read back by `read_design_table`, which refuses a table missing a column. Consumers: the caller's analysis code; nothing in ponzi-core or ponzi-service reads one.

## Design table

Columns, in order, `ponzi.evaluation.events.DESIGN_COLUMNS`:

| Column | Meaning |
|---|---|
| `claim` | the caller's label |
| `strategy` | `event` (a per event row), `pooled_equal`, `pooled_pixel`, `median`, `paired`, `wins`, `worst` |
| `statistic` | `value` for event and pooled rows, `median`, `ratio_median`, `diff_median`, `wins`, `losses`, `n_paired`, `sign_test_p`, `worst` |
| `variant`, `baseline` | the design variant the row describes, and the variant it is paired against (empty unless paired) |
| `event` | the event name of a per event row, the worst event of a `worst` row, else empty |
| `cls`, `null_kind`, `metric`, `threshold_name`, `threshold_value`, `stratum`, `value`, `n`, `k`, `lo`, `hi` | the metric row of `ponzi.evaluation.metrics` (`threshold_value` of a median row is the median of the events' values) |
| `events` | the contributing events, semicolon joined |
| `excluded` | the events the pixel floor excluded for the class, semicolon joined |

`threshold_value`, `value`, `k`, `lo`, `hi` are float, `n` int, every other column str. Rows are sorted by every str column.

A per event row set is built by `event_rows` (bursts deduplicated on the ground, concatenated), its metrics by `event_metric`, which adds the rows `n_signal_pixels`, `n_null_pixels` and `below_floor`. `pool_rows` and `pooled` form the equal or pixel weight pool with the caller's threshold rule. `across_events` gives the summaries (`STRATEGIES`: `median`, `paired`, `wins`, `worst`; `paired` and `wins` need a `baseline` variant, wins counted in each metric's direction, `LOWER_IS_BETTER`). Events with fewer signal pixels than the floor (`FLOOR_PIXELS`, 20) are excluded from pools and summaries and named in `excluded`.
