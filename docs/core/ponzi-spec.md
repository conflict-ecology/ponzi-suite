# ponzi-spec

The shared schemas: the definitions every part of PONZI agrees on, with no computing code. The server, the clients, the worker and the other ponzi-core distributions all install it; it needs only pydantic and PyYAML.

| Module | Holds | Explained in |
| --- | --- | --- |
| `ponzi_spec.identity` | content ids, spec hashes, contract hashes, the workflow hash | [Content ids and reuse](../using/content-ids.md), [Versions](../reference/versions.md) |
| `ponzi_spec.stac`, `ponzi_spec.collections` | the STAC Collections, the PONZI extension, `make_item` | [STAC catalog profile](../using/stac-profile.md) |
| `ponzi_spec.manifest` | the readable provenance of an output | [Provenance (manifests)](../using/manifests.md) |
| `ponzi_spec.stages` | `StageSpec`, the interface of a stage | [Stages](../method/stages.md) |
| `ponzi_spec.home` | the PONZI home and its layout | [Folders and environment variables](../getting-started/paths.md) |
| `ponzi_spec.compose`, `ponzi_spec.specs`, `ponzi_spec.panel` | composing yaml with `extends:`, finding and recording specs, the panel spec | [Specs and the PONZI home](../service/configuration.md), [Naming rules](../models/naming.md#spec-folders) |
| `ponzi_spec.naming` | the words names are made of | [Naming rules](../models/naming.md) |
| `ponzi_spec.catalog`, `ponzi_spec.majortom` | the burst catalog, the Major TOM grid without numpy | [Data sources and catalogs](../method/data-sources.md) |
| `ponzi_spec.cluster` | cluster profiles from a snapshot and a site file | [Running on SLURM](../service/hpc.md#the-profile) |
| `ponzi_spec.api` | the REST API's request and response models | [REST API](../service/rest-api.md) |

It has no command. Its [API reference](../reference/ponzi-spec.md) is generated from its docstrings.
