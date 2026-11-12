# CR-074: an area may be more than 64 tiles, with a warning

- **Requested by / date:** owner, 2026-11-11 ("update the ui to remove the 64 major tom tile limit and just warn when user is attempting to submit more than 64 tiles." then "it shouldn't refuse. it should just warn.")
- **Status:** signed off (2026-11-11), implemented (2026-11-11)

## Why
CR-067 made an area 1 to 64 Major TOM tiles, and every layer refused more: the map added no more, `AreaCreate` failed validation and the server answered 422. Some areas to watch are larger than 64 tiles (about 6400 km²), and splitting them over several areas only to stay under the limit gains nothing.

## What changes
- **`ponzi-spec`.** `AreaCreate.cells` is 1 or more distinct cells, with no upper bound. `MAX_AREA_CELLS` (64) stays: past it a client warns, and it is still the most cells one `GET /v1/majortom/bursts`, `/tracks` or `/cells?cells=` request takes.
- **ponzi-server.** `POST /v1/areas` makes an area of any number of tiles over land; past `MAX_AREA_CELLS` it logs a warning. The area is still refused when its bursts pass the catalog's cap (5000), as before. The tile lookups keep their limit of 64 per request. `openapi.json` is regenerated.
- **ponzi-client.** The help texts and docstrings say 1 or more tiles.
- **ponzi-visual.** The map adds every tile chosen; past 64 the map's note and the form warn, and the form still sends them. The burst footprints and track counts of more than 64 tiles are asked for in groups of 64 and merged, each burst once.

## Do results change?
No. The bursts an area of 64 tiles or fewer watches are unchanged.

## Tests
`ponzi-spec`: `AreaCreate` takes 65 tiles. ponzi-server: `POST /v1/areas` with 65 tiles makes the area; `GET /v1/majortom/bursts` with 65 is still a 422. ponzi-visual: the map adds a 65th tile and warns, the bursts are drawn, and the form warns, merges the groups' bursts and sends all 65.

## Version
`ponzi-spec` minor (a constraint relaxed). ponzi-server, ponzi-client and ponzi-visual patch.
