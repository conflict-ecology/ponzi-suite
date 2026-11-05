# Gaza

The test location of the Gaza damage releases.

| File | What | State |
| --- | --- | --- |
| `recipe.yaml` | the release v4 detection recipe for one path (formerly the preset `gaza_release_v4`) | complete; the detection tests use it |
| `forecaster.yaml` | the TiDE forecaster `tide-weather-gaza-finetune` (formerly `tide_c30_gaza_f1p`) of the registered model `tide_c30_gaza_f1p_mt0.2`, composed on `forecasters/tide/weather.yaml` | complete; a record of history (see its header) |
| `area.yaml` | the outline, the bursts and the event date | complete: the outline is the World Bank Official Boundaries' Admin 1 unit PSE001 "Gaza" (CC BY 4.0), the bursts the 12 of the OPERA burst database that meet it, on tracks 87 and 160 (ascending) and 94 (descending), each track covering the whole Strip |

Not here yet, because they are not in this workspace:
- the run config of the registered model (`mon_b5h5_d38f1p_mean`), which is in the registry on the HPC;
- a standard for Gaza, which needs that model's reference, run config hash and calibrations.

The training samples and checkpoint the fit spec names (`${PONZI_DATA_ROOT}/gaza/...`) are on the HPC.

The outline comes from the World Bank Official Boundaries (dataset 0038272, CC BY 4.0, The World Bank). Credit the
World Bank when the outline is shown or shared.
