# CR-049: the docs' address, conflict-ecology.github.io/ponzi-suite

- **Requested by / date:** owner, 2026-11-04 ("my org is conflict-ecology"; "ponzi-suite will publish the docs and link to the other repos").
- **Status:** implemented on the owner's instruction (2026-11-04), awaiting review; uncommitted

## Why

Plan decision D15 left the docs host as the placeholder `ORG`, in `https://ORG.github.io/ponzi-docs`. The organisation is `conflict-ecology`, and the docs are published by ponzi-suite (formerly called ponzi-docs).

## What changes

- **`ponzi_spec.stac.DOCS_BASE`** is `https://conflict-ecology.github.io/ponzi-suite`. The PONZI extension's JSON Schema, its `$id`, and the URL every Item names in `stac_extensions` follow it: `https://conflict-ecology.github.io/ponzi-suite/schemas/ponzi/v0.1.0/schema.json`. The docs build publishes the schema there (`hooks/ponzi.py`).
- **ponzi-suite:**
  - `mkdocs.yml`: `site_url` is the address above, `repo_name` is `conflict-ecology/ponzi-suite`, and `repo_url` is its GitHub address.
  - The home page links each repository at `github.com/conflict-ecology/<repo>`, and the README is titled ponzi-suite.
  - The HPC guide's link to ponzi-core points at `conflict-ecology`.
- **The READMEs** of ponzi-core, its packages, ponzi-service and ponzi-visual link the Roadmap and the docs at the new address.
- **ponzi-visual's test fixtures** name the new extension URL, the same text replaced.

## Do results change?

No. Content ids are computed from stages, inputs and parameters, never from an Item's `stac_extensions`, so no id changes. Items written before this name the old placeholder URL, which never resolved. They are refreshed when their stage runs again.

## Tests

`test-spec` (Items validated against the schema with the new URL) 64 passed; the core STAC tests; ponzi-service 122; ponzi-visual 24.

## Version

ponzi-spec: patch. The extension version (v0.1.0) is unchanged; only its published address is set.
