# CR-076: select tiles by an administrative boundary

- **Requested by / date:** owner, 2026-11-11 ("add an option in the left panel to be able to select by admin0, 1,2 or tile. if by admins just get the tiles that overlap the polygon"; then "remove admin0 as an option for selection")
- **Status:** signed off (2026-11-11), implemented (2026-11-11)

## Why
An area is made from Major TOM tiles only (CR-067), chosen one by one or by a box. A district, a province or a small country is what is often meant; its tiles are the tiles that meet its outline, which the server can find exactly and a box only roughly. The boundaries stay a way to choose tiles, never what an area is.

## What changes
- **ponzi-server.** `GET /v1/boundaries/{level}/{code}/cells[?limit=]` (`client:read`): the Major TOM tiles over land that meet the boundary's stored outline (simplified to about 100 m), in the grid's order, with their footprints (`MajorTomCell`). Each part of a boundary is walked over its own box. 422 past `limit` (at most and by default 5000), 404 for no such boundary, 503 until the boundaries are ready. It answers for any level; the map offers Admin 1 and 2 only. `openapi.json` is regenerated; `Client.boundary_cells`.
- **ponzi-visual.** **Select by** in the panel: **Tile**, **Admin 1** or **Admin 2** (not a whole country). With a level, its boundaries are drawn from their zoom whatever the legend's toggle, take the pointer, and a click adds the boundary's tiles to the selection (Shift-click removes them). The area made is its tiles, as before.
- **`ponzi-spec`.** Nothing: the route answers `MajorTomCell`s.

## Do results change?
No.

## Tests
ponzi-server: a triangle's tiles are those meeting it, not its box; a boundary of two far parts; the limit; 404. ponzi-visual: the level drawn and clickable whatever its toggle, a click adding and Shift-click removing, the refusal shown, the zoom gate, the panel's choice, without Admin 0.

## Version
ponzi-server and ponzi-client minor (a new route). ponzi-visual minor.
