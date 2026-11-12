# CR-068: tile submission with a monitoring year; the server chooses the standard

- **Requested by / date:** owner, 2026-11-05 ("This UI is only for tile submission with a monitoring year. So runs should be removed. The back end should handle all the model logic. Add a collapsable tab to access settings, add another page with currently monitored.").
- **Status:** implemented on the owner's instruction (2026-11-05)
- **Superseded in part:** the Monitored page was removed (CR-075).

## Why

The front end is for one thing: choosing Major TOM tiles and watching them over a span of days. Which standard runs them, and how often new acquisitions are looked for, is the back end's business, not something a person choosing tiles should pick.

## What changes

- **`ponzi_spec.api`:** `AreaCreate.standard` is optional (`None` by default). `cadence_hours` stays optional with its default of 24 hours.
- **ponzi-server:**
  - A new setting, `default_standard`: the standard an area made without one takes. It must be one the server holds; a server whose `default_standard` names a standard it does not hold refuses to make such an area, saying so.
  - With no `default_standard`, a server holding exactly one standard takes that one.
  - Otherwise (none, or several) `POST /v1/areas` without a standard is refused with a 422 that says to give `standard` or set `default_standard` in the server's settings.
  - An area given a standard is made as before. Run requests (`POST /v1/requests`) are unchanged and still name their standard.
  - `openapi.json` is made again.
- **ponzi-visual:**
  - The Runs tab and its panel are removed; the server and the Python client keep their run requests.
  - The new area form takes the selected tiles, their tags and a first and last day (both empty by default: an empty first day leaves the start to the server, an empty last day leaves the end open), sent as `start_date` and `end_date`; no standard and no cadence are sent. (First made a monitoring year select; the owner asked for the date range back the same day.)
  - A collapsible navigation drawer at the side opens the pages: Map, Monitored, Settings and Disconnect.
  - A Monitored page (`#/monitored`) lists the watched areas with their tiles, tags, span, state, job counts and when they were last looked at, and pauses, resumes, looks now and deletes them.

## Do results change?

No. Which standard runs an area is chosen by the server; a given standard runs as before.

## Tests

- `ponzi-spec`: an `AreaCreate` with no standard validates and keeps the default cadence.
- ponzi-server: an area with no standard takes `default_standard`, else the one standard held; with several and no setting, or a setting naming no held standard, it is refused with a 422 naming `default_standard`.
- ponzi-visual: no Runs anywhere; the year maps to the dates and no standard or cadence is sent; the drawer opens, closes and is remembered; the Monitored page lists areas with their job counts and its actions call the API; Settings still switches the skin.

## Version

`ponzi-spec` minor (a required field becomes optional). The standards are unchanged.
