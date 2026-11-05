# Standards

One file per standard version, `<id>-<version>.yaml`: everything a watched area runs (`ponzi_models.standards`, ponzi-core CR-028 and CR-055). A published standard never changes; a change is a new file with a new version.

| File | Status |
| --- | --- |
| `s1-general-1.0.0.yaml` | draft: waits for its model and calibrations on `majortom-global@0.4.0` |

- Check one with `ponzi-models check-standard standards/<file> [--registry DIR]`. A draft is checked for its form only. A published one is held against the registry, its panel, the installed versions it `requires`, and the version before it in this folder.
- Within a major, nothing that changes the runs may change (the workflow, the coherence and onboarding configs, the panel, the model, the run config). Within a minor, only the description and `requires`.
- `ponzi-models standard-workflow` turns a published standard into the server's file, in the PONZI home's `standards/`.
