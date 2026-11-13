# CR-099: one home on three tiers of storage: hot, warm and cold

- **Requested by / date:** owner, 2026-11-13 ("I may need to use multiple NAS stores which are faster for processing and another that is larger colder storage"; "what if I had a $PONZI_HOME_COLD $PONZI_HOME_WARM $PONZI_HOME_HOT?"; the stores are "mounted on login nodes and will have the same paths on other nodes"; "downloads should be on cold"; "leave $PONZI_HOME_HOT out and just use $PONZI_HOME"; "what if I want to do a partial promote (i.e some downloads?)")
- **Status:** signed off (2026-11-13: decisions 1 to 5 confirmed, partial promotion folded in; "approved to execute"), implemented (0.1.2)
- **Changes in part:** CR-088 (one home, no folder moved out of it): the home spans up to three roots, each folder in one of them by a fixed rule; CR-047 (a home's records name its files by relative paths): they are relative to the home, read through the tiers.

## Why
A worker keeps everything in one folder, `$PONZI_HOME` (CR-088): the cache, the downloaded inputs, scratch, logs, outputs. The cluster has storage of different kinds: a fast NAS for processing, and larger, slower stores. Today the only way to use them is symlinks inside the home, which PONZI does not know of: nothing moves between them, and the cache can only grow on the fast store until `evict` deletes from it.

## What changes

### Three roots
- **`$PONZI_HOME`** stays the home and is the **hot** tier: there is no `$PONZI_HOME_HOT`. Every command, script and document that names the home still means it. The docs say so wherever the tiers appear: "`$PONZI_HOME` is the home, and the hot tier".
- **`$PONZI_HOME_WARM`** and **`$PONZI_HOME_COLD`** name the other two. Unset, a tier falls back: cold to warm, warm to hot. A home with neither set is today's, unchanged.
- The three are the same on every machine that runs PONZI work: the login node and every compute node mount them at the same paths. A rendered SLURM script exports the tiers set, as it exports `PONZI_HOME` (CR-088).
- A layout made for a given root (`layout(root)`: the tests, a server made in its own process) has no other tier unless given (`layout(root, warm=..., cold=...)`).

### Each folder on one tier, by a fixed rule
| Tier | Folders | Why |
| --- | --- | --- |
| hot (`$PONZI_HOME`) | `cache/` (where entries are made: `cache/work/`, `cache/locks/`, `cache/jobs/`, `cache/slurm/`), `tmp/`, `work/` (ponzi-pipeline's), `logs/`, `cluster/`, `keys/`, `server/`, `specs/`, `catalog/`, `standards/` | written and read hard while work runs; the cache's locks and the rename that commits a task stay on one file system, and every sweep and node sees one set of locks and live batches |
| warm (`$PONZI_HOME_WARM`) | `outputs/`, `registry/`, `models/`, `calibrations/`, `panels/`, `training/` | large, written once, read often |
| cold (`$PONZI_HOME_COLD`) | `downloads/` (`slc/`, `orbits/`, `dem/`, `ghsl/`, `era5/`) | the largest and least read: inputs downloaded once, read by the tasks that ingest them |

`ponzi_spec.home.Layout` gives every folder at its tier's root; `Layout.make` makes each where it belongs. No setting moves one folder (CR-088 stands for that): the rule is the code's.

### Tiered folders: `cache/` and `downloads/`
Their files are written once, never changed, and named by what they are (a content id; a granule, orbit, tile or month), so a copy in any tier is the same file. For these two folders:

- **New files are written at the folder's tier:** cache entries on hot (a task writes in `hot/cache/work/<job>/` and renames into `hot/cache/<collection>/<content id>/`), downloads on cold.
- **A file is looked up hot, then warm, then cold:** the first copy found is used, read where it is. A cache entry found in any tier is cached; a download found in any tier is not downloaded again. A job's record (`cache/jobs/`) stays on hot, whatever tier its outputs are in.
- **`ponzi-worker promote`** copies files up a tier (default hot), whole or not at all (a `.partial` renamed, so a task reading at that moment sees the original or the whole copy); a copy already there with the same size is kept:
  - `promote CONTENT_ID ...`: cache entries;
  - `promote downloads/slc/<granule>.zip ...`, `promote 'downloads/slc/*_202609*'`, `promote downloads/dem`: given downloads, glob patterns (a granule's name carries its date), or whole folders.
- **`ponzi-worker evict`** gains:
  - `--to warm|cold`: the least recently used cache entries past an age or a size moved down a tier (copied whole, then removed from hot) instead of deleted; without `--to`, deleted, as today. Never an entry a running job holds, or one given to `--keep` and what it derives from, as today.
  - `--promoted FOLDER`: the copies in hotter tiers of `downloads/` files whose original is still at the folder's tier, removed (with `--older-than-days`); the originals stay.
- No sweep promotes or evicts by itself.

### Inputs found file by file
A stage is given the folder of its inputs (`slc_dir`, `orbit_dir`, `dem_dir`, `ghsl_dir`, `era5_dir`, CR-079), the home's `downloads/` on cold. ponzi-pipeline looks each file up through the tiers (`ponzi_spec.home.find_file`): the SLC zip (`acquire.slc`), the orbit file (`orbits.find_orbit`), the stitched DEM (`dem.cached`), the GHSL tile (`built.fetch_tile`) and the ERA5 month (`weather.area_path`); one in no tier is downloaded into the given folder, on cold. These folders are request params, never hashed, so no content id changes. A folder outside the home is used as it is.

### Records that name files
A record that names a file of the home (a built panel's stores, in `panels/` on warm, pointing into `cache/`) names it relative to the home, marked so: `home:cache/ponzi-coherence/<id>/coherence.zarr`. Read back, the first folder of the path says where to look: `cache/` and `downloads/` through the tiers, any other folder at its tier (`Layout.resolve`). A reference never names a mount or a tier, so it holds when an entry is evicted to cold or promoted, and when a home's tiers are copied elsewhere. A panel written before (`../../cache/...`, relative to the panel's folder) is read as before, through the tiers.

### The server
The server's own folders (`server/`, `keys/`, `standards/`, `catalog/`) are on its hot tier; `outputs/` on its warm tier. In `path` mode (CR-041) the server and its workers share the warm tier, at the same path.

### The cluster snapshot
`ponzi-worker profile` warns when a tier set is on no file system of the snapshot's `storage.txt` (as it does for the roots), and when two tiers set are one file system.

### Docs
Folders and environment variables (the three roots, "`$PONZI_HOME` is the home, and the hot tier", the rule, the fallbacks), Running on SLURM (the tiers on a cluster; `promote`, `evict --to`, `evict --promoted`), the worker (the tiered folders), the glossary (hot, warm, cold).

## Do results change?
No. Where a file is stored changes no content id and no number; every copy is the same file.

## Tests
- ponzi-spec: `Layout` with no tiers set (today's paths), with all three, with one set and the fallbacks; `make` makes each folder at its tier; `find_file`, `hotter`, `resolve` and `relative` through the tiers; a profile's warnings for the tiers against `storage.txt`.
- ponzi-worker: a task commits into hot with an input entry read from cold; an entry found in warm or cold is cached and read in place; `evict --to cold` moves entries whole, never a running job's or a kept one's, and deletes without `--to`; `promote` of entries, of a download glob and of a folder, keeping a copy already there; `evict --promoted downloads/slc`; job records stay on hot; a rendered script exports the tiers; a sweep (CR-096) sees entries in any tier as cached.
- ponzi-models: a panel built with its stores in the cache and itself on warm names them relative to the home and loads, also after its stores are evicted to cold; a panel from before (relative to its folder) loads.
- ponzi-pipeline: an SLC zip, an orbit file, a DEM, a GHSL tile and an ERA5 month promoted to hot are found there and not downloaded; one in no tier is downloaded into the given folder.

## Decided at sign-off
1. **`$PONZI_HOME` is the hot tier,** with no other name for it (owner: "leave $PONZI_HOME_HOT out and just use $PONZI_HOME"; the docs make it clear); `$PONZI_HOME_WARM` and `$PONZI_HOME_COLD` are added, falling back cold → warm → hot.
2. **The folder of each kind of file has one tier, fixed in code** (the table), so every machine agrees without settings; downloads on cold.
3. **`cache/` and `downloads/` are looked up through the tiers;** files move down only by `evict --to` (dropped copies by `evict --promoted`), and up by `promote`. No sweep moves anything by itself.
4. **Inputs are read in place,** in whichever tier they are found (the stores are mounted on every node); `promote` stages them to hot when the owner wants.
5. **Records name a home's files relative to the home,** read through the tiers; no reference names a mount or a tier.

## Version
- ponzi-spec: minor (`Layout`'s tiers, `find_file`, `hotter`, `resolve`, `relative`; the profile's warnings).
- ponzi-worker: minor (the tiered cache; `promote`, `evict --to`, `evict --promoted`; the scripts' exports).
- ponzi-models: minor (a panel's stores named relative to the home).
- ponzi-pipeline: minor (inputs found through the tiers).
- ponzi-server: patch (its folders through `Layout`).
- ponzi-suite: the docs above.
- Standard: no change.
