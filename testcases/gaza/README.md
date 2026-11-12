# Gaza

The test location of the Gaza damage releases.

| File | What |
| --- | --- |
| `area.yaml` | the outline, the bursts and the event date: the outline is the World Bank Official Boundaries' Admin 1 unit PSE001 "Gaza" (CC BY 4.0), the bursts the 12 of the OPERA burst database that meet it, on tracks 87 and 160 (ascending) and 94 (descending), each track covering the whole Strip |
| `specs/detection_specs/single-path-gaza-release.yaml` | the releases' detection spec for one path; the detection tests use it |
| `specs/training_specs/tide/tide-weather-gaza-finetune.yaml` | the TiDE fine-tune of `tide-weather` on the Gaza outside-Strip samples |

Not here yet: the case's scoring spec and a standard for Gaza, which needs a registered model, its scoring spec
hash and calibrations. The training samples and checkpoint the fine-tune names (`${PONZI_HOME}/gaza/...`) are
on the cluster.

The outline comes from the World Bank Official Boundaries (dataset 0038272, CC BY 4.0, The World Bank). Credit the
World Bank when the outline is shown or shared.
