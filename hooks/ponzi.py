"""MkDocs hooks: content that comes from ponzi-spec, so the docs never restate it by hand.

- ``<!-- ponzi:collections -->`` in a page becomes the table of the profile's Collections.
- The PONZI extension's JSON Schema is published at ``schemas/ponzi/<version>/schema.json``, the URL Items name.
- ponzi-core's store contracts (``docs/contracts/*.md``) and change requests (``docs/requests/CR-*.md``) are
  published as pages from the ponzi-core checkout beside the suite (``$PONZI_CORE`` overrides it), never copied:
  ``reference/contracts/<name>/`` and ``history/requests/<CR>/``. ``<!-- ponzi:contracts -->`` and
  ``<!-- ponzi:requests -->`` become their index tables. A relative link in those files that names no page of the
  site (code, tests, a ponzi-core README) becomes its address on GitHub, so the strict build stays strict.
"""

from __future__ import annotations

import json
import os
import re
from pathlib import Path

from ponzi_spec.collections import COLLECTIONS
from ponzi_spec.stac import PONZI_EXTENSION_VERSION, extension_schema

MARKER = "<!-- ponzi:collections -->"
CONTRACTS = "<!-- ponzi:contracts -->"
REQUESTS = "<!-- ponzi:requests -->"
CORE_REPO = "https://github.com/conflict-ecology/ponzi-core/blob/main"
#: generated page src_uri -> its source folder inside ponzi-core (for the links)
_FROM_CORE: dict[str, str] = {}


def collections_table() -> str:
    """The Collections as a markdown table."""
    rows = ["| Collection | One Item is | Assets | Contract |", "| --- | --- | --- | --- |"]
    for c in COLLECTIONS.values():
        assets = ", ".join(f"`{k}`" + ("" if a.required else " (optional)") for k, a in c.assets.items())
        item = c.item + (" (external, by link)" if c.external else "")
        rows.append(f"| `{c.id}` | {item} | {assets or 'links only'} | {c.contract or ''} |")
    return "\n".join(rows)


def on_page_markdown(markdown, page, config, files):
    """Replace the markers."""
    return markdown.replace(MARKER, collections_table()) if MARKER in markdown else markdown


def on_post_build(config):
    """Publish the extension schema."""
    out = Path(config["site_dir"]) / "schemas" / "ponzi" / PONZI_EXTENSION_VERSION / "schema.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(extension_schema(), indent=2) + "\n", encoding="utf-8")


def _core(config) -> Path:
    """The ponzi-core checkout: ``$PONZI_CORE``, else ``ponzi-core`` beside the suite."""
    here = Path(config["config_file_path"]).resolve().parent
    return Path(os.environ.get("PONZI_CORE") or here.parent / "ponzi-core")


def _title(text: str, fallback: str) -> str:
    first = next((l for l in text.splitlines() if l.startswith("# ")), "")
    return first[2:].strip() or fallback


def _sources(config) -> tuple[list[Path], list[Path]]:
    core = _core(config)
    contracts = sorted(p for p in (core / "docs" / "contracts").glob("*.md") if p.name != "README.md")
    requests = sorted((core / "docs" / "requests").glob("CR-*.md"))
    if not contracts:
        raise FileNotFoundError(f"no ponzi-core contracts under {core} (check out ponzi-core beside the suite, or set "
                                "PONZI_CORE)")
    return contracts, requests


def on_files(files, config):
    """Add the contracts and requests of ponzi-core as generated pages."""
    from mkdocs.structure.files import File

    contracts, requests = _sources(config)
    for p in contracts:
        uri = f"reference/contracts/{p.name}"
        files.append(File.generated(config, uri, abs_src_path=str(p)))
        _FROM_CORE[uri] = "docs/contracts"
    for p in requests:
        uri = f"history/requests/{p.name}"
        files.append(File.generated(config, uri, abs_src_path=str(p)))
        _FROM_CORE[uri] = "docs/requests"
    return files


def _index(paths: list[Path], folder: str, page_dir: str) -> str:
    rows = ["| Page | Title |", "| --- | --- |"]
    for p in paths:
        title = _title(p.read_text(encoding="utf-8"), p.stem).replace("|", "\\|")
        rows.append(f"| [{p.stem}]({os.path.relpath(folder, page_dir)}/{p.name}) | {title} |")
    return "\n".join(rows)


LINK = re.compile(r"\]\((?!https?://|mailto:|#)([^)\s]+)\)")


def _repoint(markdown: str, page, files) -> str:
    """Relative links of a page from ponzi-core: kept when they name a page of the site, else sent to GitHub."""
    core_dir = _FROM_CORE[page.file.src_uri]
    page_dir = os.path.dirname(page.file.src_uri)
    known = {f.src_uri for f in files}

    def fix(m):
        target = m.group(1)
        path, _, anchor = target.partition("#")
        if not path:
            return m.group(0)
        if os.path.normpath(os.path.join(page_dir, path)) in known:
            return m.group(0)
        if path.endswith(".md") and os.path.normpath(os.path.join(core_dir, path)).startswith("docs/requests/"):
            here = os.path.relpath("history/requests", page_dir)
            return f"]({here}/{os.path.basename(path)}{'#' + anchor if anchor else ''})"
        if path.endswith(".md") and os.path.normpath(os.path.join(core_dir, path)).startswith("docs/contracts/"):
            here = os.path.relpath("reference/contracts", page_dir)
            return f"]({here}/{os.path.basename(path)}{'#' + anchor if anchor else ''})"
        url = f"{CORE_REPO}/{os.path.normpath(os.path.join(core_dir, path))}"
        return f"]({url}{'#' + anchor if anchor else ''})"

    return LINK.sub(fix, markdown)


_on_page_markdown_collections = on_page_markdown


def on_page_markdown(markdown, page, config, files):  # noqa: F811  (extends the one above)
    """The collections table, the contracts and requests indexes, and the links of pages from ponzi-core."""
    markdown = _on_page_markdown_collections(markdown, page, config, files)
    if CONTRACTS in markdown or REQUESTS in markdown:
        contracts, requests = _sources(config)
        page_dir = os.path.dirname(page.file.src_uri)
        markdown = markdown.replace(CONTRACTS, _index(contracts, "reference/contracts", page_dir))
        markdown = markdown.replace(REQUESTS, _index(requests, "history/requests", page_dir))
    if page.file.src_uri in _FROM_CORE:
        markdown = _repoint(markdown, page, files)
    return markdown
