# CR-024: ponzi-spec, the shared schemas of the overhaul

- **Requested by / date:** owner, 2026-10-23 (phase 1 of the overhaul plan, `ponzi-service/docs/overhaul-plan.md`, decision D1)
- **Status:** implemented on the owner's instruction (2026-10-23, "start phase 1"), awaiting review; uncommitted (plan decision D10)

## Why

The overhaul makes PONZI four repositories that talk only through REST and STAC. The server, the clients and the front end must share the data spec and the API models without installing numpy, xarray or torch, and every computing distribution must stamp the same identity and lineage onto what it writes. One small distribution holds those definitions, so they change in one place and under this repository's change process.

## What changes

A new distribution `ponzi-spec` (import `ponzi_spec`) under `packages/spec/`, depending on pydantic and PyYAML only:

| Module | Holds |
| --- | --- |
| `identity` | canonical JSON, `content_id` (sha256 over stage, sorted input content ids and the identity config, 32 hex), `external_id` for inputs from outside (a granule, an orbit file), `item_id` |
| `stac` | minimal STAC 1.1.0 Item, Collection, Asset and Link models; `PonziFields`, the PONZI extension's fields; `make_item` with the lineage links (`derived_from`, `ponzi:model`, `ponzi:calibration`, `ponzi:standard`), each carrying the input's `ponzi:content_id` |
| `extension/ponzi/v0.1.0/schema.json` | the JSON Schema of the PONZI STAC extension |
| `collections` | the Collections of the profile (`ponzi-coherence`, `ponzi-run`, ...), their asset roles and media types, and the contract each one maps to |
| `manifest` | the provenance manifest: the lineage graph of an Item walked back to its external sources, as a model and as human-readable YAML |
| `stages` | `StageSpec` and `ResourceHint`, the `Stage` protocol, discovery through the entry point group `ponzi.stages` |
| `config` | the deployment config (`ponzi.yaml`: roots as URIs, server, credentials file, cluster profile), its lookup order and its environment overrides |
| `paths` | URI helpers: local or remote, join, and a local `Path` where one is needed |
| `api` | the `/v1` request and response models: watched areas, run submissions, jobs, leases, heartbeats, uploads, problems |

The extension's schema URL uses the placeholder host `ORG.github.io` (plan decision D15), set once in `ponzi_spec.stac.DOCS_BASE`.

The stage version in a content id is the stage's own identity version, declared by the stage and raised whenever its output bytes may change for the same inputs and config; it is not derived from a package version (below 1.0 this repository releases MINOR and PATCH changes alike as `0.y.z+1`, CR-020).

Nothing in `ponzi` changes. `ponzi` does not import `ponzi_spec` yet; that is phase 2.

## Do results change?

No. No existing module, store or config changes.

## Tests

`packages/spec/tests/`, run on their own (`pytest packages/spec/tests`; the root suite collects `tests/` only): content ids are stable, order-free in the inputs and sensitive to every identity field; Items validate against the extension schema and fail it where they should; the manifest walks a synthetic chain, deduplicates shared inputs, lists external sources and refuses a cycle; config lookup, precedence and the old environment aliases; path helpers; the API models' validators; importing `ponzi_spec` loads neither ponzi nor numpy. A CI job runs them.

## Version

`ponzi-spec` 0.1.0, a new distribution. Library `ponzi`: unchanged. Standard: not affected.
