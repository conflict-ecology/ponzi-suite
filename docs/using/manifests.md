# Provenance (manifests)

A manifest is the readable provenance of one output: every step from the Sentinel-1 scenes to the events, with the stages and the code releases, specs and models that made them.

It is built by walking the output's lineage links back to the external sources (`ponzi_spec.manifest.build_manifest`). Steps come sources first; an input shared by two steps appears once; a cycle is an error. The machine form is the Items themselves; the manifest is stored as the `manifest` asset of a final Item.

```yaml
# the hash of the manifest's declaration (CR-085)
manifest_version: b5e69bf8aca0dfcf87ae17458ca6d388
subject: ponzi-events-cell-393U_467R-9c1e4d2a7b10
content_id: 9c1e4d2a7b10...
standard: s1-general@3f9a12c4
created: '2026-11-04T10:12:03Z'
sources:
- content_id: 3fa1...
  rel: derived_from
  href: https://datapool.asf.alaska.edu/SLC/SA/S1A_IW_SLC__1SDV_20260901....zip
  title: S1A_IW_SLC__1SDV_20260901...
steps:
- item: ponzi-input-layer-t028_058198_iw3-51c0a9e2d4f7
  stage: {name: assemble, code: {ponzi: '0.0', ponzi-pipeline: '0.0'}}
  spec_hash: ...
  inputs: [3fa1..., ...]
- item: ponzi-run-t028_058198_iw3-7d2e...
  stage: {name: run, code: {ponzi: '0.0'}}
  spec_hash: ...
  request: {staged: true}
  inputs: [51c0a9e2..., ...]
- item: ponzi-events-cell-393U_467R-9c1e4d2a7b10
  stage: {name: tile, code: {ponzi: '0.0'}}
```

The server serves it at `/v1/manifests/{content_id}`, as JSON, or as this yaml with `?format=yaml`.
