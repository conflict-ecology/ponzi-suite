# STAC catalog profile

PONZI catalogs its data with [STAC](https://stacspec.org) 1.1.0. Stores keep their formats (Zarr for the stores of the [contracts](../reference/contracts.md), Cloud Optimized GeoTIFF for pair coherence and display rasters); STAC is the catalog and the lineage around them.

## Collections

One Item of each Collection is:

<!-- ponzi:collections -->

Every burst-level Item carries the ESA Sentinel-1 burst id and footprint. A request is a list of burst ids; a watched area is made from Major TOM tiles and holds the ids of the bursts meeting them.

## Extensions

Standard extensions wherever they fit. In use: `sat` (a burst's orbit, below) and `proj` (its grid). Planned, not yet written by any code: `sar`, `file` (size and checksum per asset), `processing`, `version`, `datacube` (Zarr dimensions), `mlm` (models), `label` (labels).

### A burst's orbit (`sat`)

Every Item of a burst carries `sat:relative_orbit`, the track (`t028` of `t028_058198_iw3`; 1 to 175, also called the path). Where the pass is known, from ASF's flight direction at discovery, it also carries `sat:orbit_state`, `ascending` or `descending`.

A relative orbit has an ascending and a descending half, on opposite sides of the Earth, so a place is seen by a given track in one direction only. Two views of one place in different directions are always two tracks.

The stores hold the same as attrs (`relative_orbit`, `orbit_state`):

- `ponzi-pipeline assemble` writes them into the coherence store;
- a run copies them into its stores;
- the events stores record them.

A path (`ponzi detect-path`, `ponzi tile`) combines bursts of one track seen in one direction. Bursts of two tracks or two directions are refused unless `--allow-mixed-tracks` is given, and then the events store records every track it combined (`relative_orbits`, `orbit_states`, `mixed_tracks`).

## The PONZI extension

Schema: <a href="../../schemas/ponzi/v0.3.0/schema.json"><code>schemas/ponzi/v0.3.0/schema.json</code></a> (published by this site's build from `ponzi-spec`, with every earlier version: <a href="../../schemas/ponzi/v0.2.0/schema.json"><code>v0.2.0</code></a>), listed in every Item's `stac_extensions`.

| Field | Required | Meaning |
| --- | --- | --- |
| `ponzi:content_id` | yes | the Item's [content id](content-ids.md) |
| `ponzi:stage` | yes | `{name, code}` of the stage that made it: its name and the major of each distribution that computed it, `{}` for an ingest (ponzi-core CR-085) |
| `ponzi:spec_hash` | no | the hash of the spec the stage ran (scoring spec, coherence spec, ...) |
| `ponzi:request` | no | the request fields that do not change the result, for the record |
| `ponzi:standard` | no | the standard it was made under |
| `ponzi:tags` | no | assigned by the server as it serves an analysis Item (runs, p-values, events, events of a cell; a standard's jobs deliver only the events of a cell, the others are Items held from before CR-100): the tags of the watched areas of its burst or tile ([Watched areas](watched-areas.md#tags)). Never set by a stage, never stored in the Item and never part of its content id |
| `ponzi:layer` | no | the name of the input layer a `ponzi-input-layer` Item holds: `sar` or `onboard` (CR-102; extension `v0.3.0`). Items made before name `v0.2.0`, whose schema is still published |

Unknown `ponzi:` fields are refused.

## Lineage

An Item links to what it was made from:

| Link `rel` | Target |
| --- | --- |
| `derived_from` | each input Item, or an external input (a granule, an orbit file) |
| `ponzi:model` | the model Item a run used |
| `ponzi:calibration` | the calibration Item p-values were coded under |
| `ponzi:standard` | the standard Item |

Every lineage link carries the target's `ponzi:content_id`, so the graph can be walked without fetching the targets. Every Item also links its Collection (`rel: collection`, `./collection.json`); a static catalog keeps each Collection's Items in one folder.

Build Items with `ponzi_spec.make_item`; see the [ponzi-spec API reference](../reference/ponzi-spec.md#stac).
