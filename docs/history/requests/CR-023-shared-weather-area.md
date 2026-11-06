# CR-023: one CDS weather request per month for all the bursts of an AOI

- **Requested by / date:** owner, 2026-10-21
- **Status:** signed off and merged into main 2026-10-21 (owner), released in v0.2.3.

## Why

The onboarding's weather source `edh_cdsgrid` (monorepo decision 42) takes ERA5-Land from the DestinE EDH Zarr store up to its last stamp (currently 2026-05-31 23:00) and from the gridded ERA5-Land of the Copernicus CDS (`reanalysis-era5-land`) after it. The CDS part is ONE request per calendar month per BURST, over the burst's own cell patch, cached per burst (`era5grid_<burst>_<year>-<month>_<digest>.nc` under `<out>/era5`).

For the 36 Tehran bursts that queued 180 monthly requests (June to October 2026), which the CDS served about one at a time for our account; the onboarding was cancelled after 15 minutes and the Tehran onboarding went back to `edh` alone (ponzi-apps `aois/tehran/onboard.yaml`), so its weather, and with it its runs, end on 2026-05-31.

The bursts of an AOI overlap heavily (the Tehran campaign box is lon 50.8336..51.7675, lat 35.3207..35.9693, and every burst's footprint reaches beyond it). ERA5-Land is a fixed 0.1 degree grid, so a request over a box that contains every burst's patch returns the same cells with the same values as each burst's own request: one request per month for the AOI serves them all.

## What changes

**Config.** A new optional key of the onboarding section, `weather_area: [lon_min, lat_min, lon_max, lat_max]` (WGS84 degrees), default absent. Accepted with `weather_source: cdsgrid` or `edh_cdsgrid` only (the EDH route reads chunks, not requests, and is refused with an area); four numbers, min below max, in range.

**Requests.** With the key set, the CDS grid requests of the onboarding are over the AREA instead of the burst's patch:

- the area is snapped outward to whole ERA5-Land cells (`era5_cell_centres` of the area without a buffer) and requested half a cell beyond the outer cell centres, the rule of the per-burst requests (`weather.area_cells`, `area_box`);
- one request per calendar month, all 24 hours, the form of the per-burst request (variables with the gridded dataset's names, `netcdf`, `unarchived`). Its days: the whole month for every month of a burst but its last (so the other bursts find those months complete), from the 1st to the last day needed for the burst's last month (which the CDS may not have published to its end), and for the prefetch its `start..end` range; the range always includes the days the file already holds, so a month file only grows;
- each month is one file in the cache folder, `era5area_<key>_<YYYY>-<MM>.nc`, with no burst id; `<key>` is a digest of the dataset, the CDS box and the requested variables (`weather.area_key`), so two configs with the same cells and variables share files and anything else does not. A small `era5area_<key>.json` beside them states the area and the variables;
- a download is written to `.part`, joined into ONE plain NetCDF file (a zip of the instant and accumulated fields, as the CDS sometimes sends, is merged; the decoded values are written without packing, so they read back as they were) and renamed into place;
- a burst whose file holds every stamp it needs reads it and requests nothing.

**The burst's values.** The burst's cells (its footprint plus one cell, as before) are taken from the area files by `_extract_grids`, the same nearest-cell, nearest-hour and accumulation rules as from its own download; the cell patch rule (`_patch_layers`, the valid-cell mean and the fallback ring) is unchanged.

**Coverage, never a fallback.** Before any request, every cell of the burst's patch must be a cell of the area (`check_area_covers`); otherwise the step raises a `ValueError` naming the patch, the area and the cells outside, with the advice to widen `weather_area`. This also holds for the fallback ring of a burst whose patch is all sea (four cells beyond the footprint).

**Array tasks.** Many bursts onboarded at once (one SLURM array) must not all request the same month. The month is downloaded under `<file>.lock`, created exclusively (`O_CREAT | O_EXCL`, holding host, pid and time); a task that finds the lock waits (`LOCK_POLL_SECONDS`, 30 s) and then reads the file the other task wrote. A lock older than `LOCK_STALE_SECONDS` (6 hours) is a crashed task's: it is removed with a warning, the leftover `.part` with it, and the month is downloaded. The cache folder must therefore be one folder for the bursts of the area: the new `ponzi onboard --era5-cache DIR` (the `era5_cache` argument `onboard_store` already had; default `<out>/era5`, as before).

**Prefetch.** `ponzi weather-prefetch --config FILE --cache DIR --start YYYY-MM-DD --end YYYY-MM-DD [--dry-run]` (`weather.prefetch_area`) downloads the area's months for the days `start..end` once, before the array job, one request per month not yet held; `--dry-run` prints each month's file and request and downloads nothing. With `edh_cdsgrid` the start is the day of the EDH store's last stamp (the trailing 24 h of the first later acquisitions reach back into it), the end at most the last day the CDS publishes. After a prefetch the onboarding of the bursts requests nothing. Without a prefetch the complete months are still one request each (the first burst asks for the whole month); the LAST month is asked for up to the first burst's last day, and a burst with a later acquisition in it (another track) asks for that month again over the longer range (the file grows). For Tehran that is at most a few extra requests for October, one per later acquisition day; the prefetch avoids them.

**Record.** The weather step's stamp parameters gain `area` (the configured area) and `area_key` when the key is set; since they are part of the parameters the stamp compares, switching the area on, off or to another area re-runs the weather step and, through its recorded weather parameters, the pair differences (decision 42 logic, unchanged). The sidecar attrs gain `weather_area`, `cds_area` (the CDS box) and `cds_area_key`. The stamp's `onboarding` dump holds `weather_area` only when it is set.

Not changed: the per-burst route (no area): its requests, its cache names, its stamp and its attrs are those of before; the EDH route; the variables, aggregations and units; the sidecar format.

## Do results change?

No. Without `weather_area` nothing changes: no existing onboarding test was changed, the config dump and the stamp are the ones of before (the new key is left out when absent), and no golden file is involved. With the key, the series of every burst are equal, bit for bit, to those of its per-burst requests (tested on two fixture bursts for `cdsgrid` and `edh_cdsgrid`, also from a zipped download, and through `onboard_store` for the whole sidecar, pair differences included). An existing onboarding that turns the key on re-runs its weather and pairdiff steps once (the stamp parameters change) and writes the same values.

What differs is only what is downloaded: a month file may hold more days and cells than one burst needs. Stamps the CDS does not deliver (a month not yet published to its end) are NaN, as from a per-burst download, and logged as a warning; they are never filled from elsewhere.

## Tests

`tests/onboarding/test_weather_area.py`, offline, with a fake CDS that writes the requested month, days, hours and box of a synthetic ERA5-Land dataset as NetCDF (or as a zip of an instant and an accumulated file):

- the config: absent key, dump as before; an area with `edh`, a reversed, short or out-of-range area refused; read from yaml; the snapping, the box and the key (same cells same key, other variables other key);
- two bursts, `cdsgrid` and `edh_cdsgrid`: one request per month for both (fewer than the per-burst requests, which are one per month per burst), the files named by key and month, no lock or `.part` left, every series equal on the bytes to the per-burst result, the provenance that of the per-burst result plus the three area attrs; a rerun requests nothing;
- every month of a burst but its last is requested whole, the last to the burst's last day; a second burst finds the complete months held and grows only the last one; a later burst grows a month (days held and needed) and the earlier burst's values from the grown file equal its own request; a zipped download is joined into one NetCDF file with the same values;
- `onboard_store` of two bursts with a shared `era5_cache`: the sidecars equal those of the per-burst onboarding, the stamp holds `area` and `area_key` (also under pairdiff's weather), one request per month in all; a matching stamp reruns nothing, another area reruns the step;
- a burst whose patch is outside the area raises before any request;
- a stale lock with a leftover `.part` is taken over and the month downloaded once; a held lock is waited for and the other task's file read without a request;
- `ponzi weather-prefetch`: the dry run prints the six monthly requests of 2021-05-31..2021-10-05 (May with one day, October to the 5th) and downloads nothing; the run makes them; a second run finds every month held; the onboarding of both bursts afterwards requests nothing; a config without `weather_area` exits 2.

The fast tier (`pixi run test`) passes with the existing tests unchanged.

## Version

Library: minor (a new opt-in onboarding option and command; every existing onboarding config and every run stays bit-identical), released as `0.2.z+1` under CR-020's reading. Standard: no change (the onboarding's values are the same).

## For the owner

- **The area of an AOI.** It must contain every burst's footprint plus one 0.1 degree cell; a burst outside fails loudly before any request, so a generous area is safe and costs nothing (a month over a few hundred cells is a few MB). For Tehran the campaign box is not enough, because the bursts reach beyond it; a box about a degree wider in longitude and half a degree in latitude covers a full burst width on each side.
- **The lock timeout.** 6 hours, chosen for the CDS queue we saw (a request can wait for over an hour); a task waiting behind a crashed one waits that long before taking over. A prefetch before the array avoids the waiting altogether.
- **The ends of the range.** How far ERA5-Land on the CDS reaches cannot be checked offline; the prefetch requests what it is told and the stamps not delivered stay NaN as before.
