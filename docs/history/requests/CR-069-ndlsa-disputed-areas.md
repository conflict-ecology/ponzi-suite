# CR-069: the disputed areas of the World Bank boundaries (NDLSA) are land, and the map has a base land layer

- **Requested by / date:** owner, 2026-11-05 ("readd a base country layer. it looks like admin 0 doesn't cover everything", then "The NDLSA covers it. add that in. describe it docs", then "the link with admin 0 all layers has all of them no need for NDSLA")
- **Status:** implemented (unreleased), owner sign-off pending

## Why
The World Bank's Admin 0 file holds the countries and territories but leaves out the areas whose legal status the World Bank has not determined (NDLSA): Jammu and Kashmir (the parts under India and under Pakistan), Aksai Chin and the smaller areas along the India and China border, Arunachal Pradesh, Western Sahara, the Golan Heights, the Shebaa Farms, the UN buffer zone in Cyprus, Abyei, the Ilemi Triangle, the Falklands, South Georgia and the British Indian Ocean Territory. 24 areas in all, about 600,000 km². The World Bank publishes them in two forms in the same dataset: a file of their own (NDLSA) and the "Admin 0_all_layers" file, which holds the countries and territories of the plain Admin 0 file and these areas together.

Without them those areas were holes in the map, and, since a Major TOM tile must meet land (CR-067) and the land was the Admin 0 outlines, no tile in them could be listed or watched. Several are places of conflict, which is what PONZI watches.

A base map from another source (Natural Earth, as the map had before CR-067) does not fit: its coasts are generalised differently and it draws the disputed areas its own way, so it never lines up with the Admin 0 outlines.

## What changes
- **The source.** Level 0 is read from `World Bank Official Boundaries - Admin 0_all_layers.parquet` (dataset 0038272 version 3, CC BY 4.0, 59 MB) instead of the plain Admin 0 file, pinned by its sha256 (`ponzi_server.boundaries.SOURCES[0]`). It has 275 rows: the 251 countries and territories of the plain file, with the same codes and names, and the 24 NDLSA areas (`WB_STATUS` "Non-determined legal status area"). No separate NDLSA file is downloaded.
- **Level 0.** Each NDLSA area is a level 0 boundary beside the countries, with `disputed` true. The file gives it no code: the code is `NDLSA-` and the name in capitals with dashes, with the sovereign's ISO code after it when two areas share a name (`NDLSA-JAMMU-AND-KASHMIR-IND`, `NDLSA-JAMMU-AND-KASHMIR-PAK`). Its country is its own name; it belongs to no country. The file's names are trimmed (it has `Kauirik\r\n`).
- **Land.** `on_land` tests the level 0 outlines, so the NDLSA areas are land: their tiles are listed and can be watched. Antarctica is in neither file and stays out.
- **The API.** `Boundary` gains `disputed` (`ponzi-spec`, default false). `boundaries.sqlite3` is format 2, with a `disputed` column; a format 1 file is built again on the next start (the level 0 file is downloaded, and the others again if they are not in `catalog/boundaries/`).
- **ponzi-visual.** The map draws the land under everything: the level 0 boundaries in view, filled in the skin's land colour, whatever overlays are on. It is the same query as the Admin 0 overlay, so the base and the outlines always match. The Admin 0 overlay is now outlines and names only; a disputed area's outline is dashed.

- **Checked** against the real file: 275 level 0 boundaries, 24 of them disputed, every code unique, the countries identical to those of the plain Admin 0 file.

## Do results change?
No. No store, model or calibration changes. Which tiles count as land changes: tiles in the NDLSA areas are now listed and can be watched.

## Tests
- ponzi-service: NDLSA rows without codes in the level 0 fixture; the areas are level 0 boundaries with `disputed`, codes told apart by sovereign, names trimmed, and a box in one is on land (`test_server_boundaries.py`).
- ponzi-visual: the land is drawn under the overlays with no names, stays when Admin 0 is off, and a disputed outline is dashed (`boundaries.test.tsx`).

## Version
`ponzi-spec` minor (a field with a default). The server's boundaries file changes format. No standard is affected.
