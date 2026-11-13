# CR-094: admin users manage watched tiles as tracts

- **Requested by / date:** owner, 2026-11-12 (after CR-093: admin users should manage the areas they approve, "on a separate page", "by contiguous set of tiles that are touching", with "the same information as the approval page", and the approval page saying what each request "would add onto"; the term to be one "that is most appropriate and doesn't conflict with anything else")
- **Status:** signed off (2026-11-12; decision 2 changed by the owner: tiles touch by an edge only), implemented (unreleased)

## Why
CR-093 lets an admin user approve a watch request, which makes an area, but not manage it afterwards: `user-admin` holds no `client:write`, so pausing, resuming, looking now and deleting are refused (403), in the app and through the API. And an area is one approved request: tiles asked for in several requests side by side are several areas, while a person thinks of the place they cover as one piece of land. An admin approving a request cannot see which watched land it extends.

## What changes

### The term: tract
A **tract** is a set of watched tiles that touch: the tiles of every area that holds tiles, grouped so that two tiles sharing an edge are in the same tract; tiles meeting only at a corner are not joined by it. Tiles that touch nothing watched are a tract of their own. "Tract" is used nowhere else in PONZI; "region" (a panel spec's `regions`), "zone" (UTM zones), "site" (a cluster's site file), "patch" (a release, an HTTP method) and "area" (a watched area, one approved request) are.

A tract is computed from the areas whenever it is asked for, never stored: approving, changing or deleting an area changes the tracts at once. Its id is its first tile, south to north then west to east (`393U_467R`), and its name that tile and how many more (`393U_467R +11`), as an area's is. An id holds while the tract keeps that tile; when two tracts join or one splits, the ids follow the new tracts.

### Who may manage areas
`user-admin` may change and delete areas and look now: `PATCH` and `DELETE /v1/areas/{area_id}` and `POST /v1/areas/{area_id}/discover` need the new scope `areas`, which `user-admin`, `client:write` and `admin` hold. Making an area directly (`POST /v1/areas`) and run requests (`POST /v1/requests`) stay with `client:write` and `admin`: an admin user makes areas by approving requests.

### The API
- `GET /v1/tracts` (`client:read`): every tract, by its id: its tiles, bursts (the union of its areas'), tags (each once), span (the earliest first day, the latest last day or none), its areas, how many are active, and the watch requests behind them (who asked, when, who approved).
- `GET /v1/tracts/{tract_id}`: one tract, and for each of its areas what an area card shows today (tiles, tags, span, active, jobs by status, last looked at) with its request.
- `POST /v1/tracts/{tract_id}/pause`, `/resume`, `/discover` and `DELETE /v1/tracts/{tract_id}` (`areas`): the same change to every area of the tract, in one transaction. The per-area routes stay.
- A watch request gains `touches`: the tracts its tiles would join, each with its id, name, tiles and areas (`GET /v1/watch-requests`, for pending requests). Empty: it would be a new tract. Two or more: approving it joins them into one.

### ponzi-visual
The Admin page becomes three pages under **Admin** in the drawer, each its own address: **Requests** (`#/admin/requests`), **Tracts** (`#/admin/tracts`) and **Keys** (`#/admin/keys`). The design follows the Laws of UX (ponzi-suite's `ux` skill).

- **Requests:** each card as now (who asked and when, the tiles' drawing, bursts, tags, days, Approve and Deny), and a line saying what it adds onto: "A new tract", "Adds onto 393U_467R +11 (12 tiles, 2 areas)", or "Joins 393U_467R +11 and 401U_470R +3". The drawing shows the touched tracts' tiles in a muted colour and the request's tiles in the accent (Common Region, Von Restorff: what is new stands out against what exists).
- **Tracts:** one card per tract, the same information as a request card (Jakob's Law: one card shape across the admin pages): its tiles' drawing, bursts, tags, span, who asked for its areas and who approved them, and its state: active, paused, or some of each. Actions on the whole tract: **Pause**, **Resume**, **Look now**, **Delete** (Delete asks once more and names how many areas and tiles go). A card opens to list its areas, each with the area card of today and its own actions (progressive disclosure, Hick's Law). A search field filters by tag or tile. Tracts with a paused area or failed jobs come first (Serial Position Effect).
- **Keys:** as now.
- The map's area cards stop showing area actions to `user-admin` keys (they manage on the Tracts page); Open its outputs stays.

## Do results change?
No. No computed number, content id or store changes. What changes is who may change areas, and how the app groups them.

## Tests
- ponzi-server: tracts from areas whose tiles share an edge (joined), meet only at a corner (not joined), and do not touch; a tract's id and name; joining and splitting as areas come and go; the tract routes, their changes to every area in one transaction, and their scopes (`user` refused, `user-admin` allowed); a pending request's `touches` (none, one, two); `user-admin` may `PATCH`, `DELETE` and `discover` an area and may not `POST /v1/areas` or `/v1/requests`.
- ponzi-spec: the new models.
- ponzi-client: `tracts`, `tract`, and the tract actions.
- ponzi-visual: the three admin pages and their addresses; a request card's "adds onto" line and drawing; a tract card, its actions and its confirmation; the area list inside a tract.
- The OpenAPI document is regenerated.

## Decided at sign-off
Each is written above as recommended; the owner confirms or changes it.
1. **The term:** tract.
2. **Touching:** an edge only (owner: "include edge only"); tiles meeting only at a corner are in separate tracts.
3. **What an admin user may do with areas:** change, delete, look now; not make areas directly or submit runs.
4. **Tracts are computed, not stored;** an id is the tract's first tile, and changes when tracts join or split.
5. **Pages:** Requests, Tracts and Keys as three pages under Admin.

## Version
- ponzi-spec: minor (the `areas` scope, new models, `touches` on a watch request).
- ponzi-server: minor (tract routes; `user-admin` may manage areas).
- ponzi-client: minor.
- ponzi-visual: major (the admin pages and their addresses).
- ponzi-suite: the docs (Using the map, Watched areas, Running the server, Logins and keys, the Glossary).
- Standard: no change.
