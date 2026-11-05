"""MkDocs hooks: content that comes from ponzi-spec, so the docs never restate it by hand.

- ``<!-- ponzi:collections -->`` in a page becomes the table of the profile's Collections.
- The PONZI extension's JSON Schema is published at ``schemas/ponzi/<version>/schema.json``, the URL Items name.
- ponzi-core's store contracts (``docs/contracts/*.md``) and change requests (``docs/requests/CR-*.md``) are
  published as pages from the ponzi-core checkout beside the suite (``$PONZI_CORE`` overrides it), never copied:
  ``reference/contracts/<name>/`` and ``history/requests/<CR>/``. ``<!-- ponzi:contracts -->`` and
  ``<!-- ponzi:requests -->`` become their index tables. A relative link in those files that names no page of the
  site (code, tests, a ponzi-core README) becomes its address on GitHub, so the strict build stays strict.
- The API references are generated from the code of the checkouts beside the suite (``$PONZI_SERVICE`` and
  ``$PONZI_VISUAL`` override them, as ``$PONZI_CORE`` does): one page per Python distribution under
  ``reference/api/``, each module of its source a ``:::`` section that mkdocstrings reads from the source
  (``plugins.mkdocstrings.handlers.python.paths`` in mkdocs.yml); ponzi-visual's page from its TypeScript files,
  each file's header comment and its exported functions, components and types with their doc comments; and
  ``<!-- ponzi:rest-api -->`` becomes the table of the routes in ponzi-server's committed ``openapi.json``.
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
REST = "<!-- ponzi:rest-api -->"
#: Python distribution -> (repository, its source folder in the repository)
DISTRIBUTIONS = {
    "ponzi": ("ponzi-core", "packages/core/src"),
    "ponzi-pipeline": ("ponzi-core", "packages/pipeline/src"),
    "ponzi-models": ("ponzi-core", "packages/models/src"),
    "ponzi-server": ("ponzi-service", "packages/server/src"),
    "ponzi-worker": ("ponzi-service", "packages/worker/src"),
    "ponzi-client": ("ponzi-service", "packages/client/src"),
}
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


def _repo(config, name: str) -> Path:
    """A checkout beside the suite (``ponzi-core``, ``ponzi-service``, ``ponzi-visual``), or where
    ``$PONZI_CORE``, ``$PONZI_SERVICE`` or ``$PONZI_VISUAL`` say."""
    here = Path(config["config_file_path"]).resolve().parent
    env = "PONZI_" + name.removeprefix("ponzi-").upper()
    return Path(os.environ.get(env) or here.parent / name)


def _core(config) -> Path:
    """The ponzi-core checkout: ``$PONZI_CORE``, else ``ponzi-core`` beside the suite."""
    return _repo(config, "ponzi-core")


# --- the Python API references -------------------------------------------------------------------------------------

def _modules(src: Path) -> list[str]:
    """The public modules under a source folder, as dotted names, sorted (no tests, no ``_private`` parts)."""
    out = []
    for f in sorted(src.rglob("*.py")):
        parts = list(f.relative_to(src).with_suffix("").parts)
        if parts[-1] == "__init__":
            parts = parts[:-1]
        if not parts or any(p.startswith("_") or p in ("tests", "test", "__main__") for p in parts):
            continue
        out.append(".".join(parts))
    return out


def python_page(dist: str, src: Path) -> str:
    """The API reference page of one distribution: a section per module."""
    mods = _modules(src)
    lines = [f"# {dist}", "", f"Generated from the docstrings of `{dist}`'s source ({len(mods)} modules). "
             "A module's own docstring comes first, then its public members.", ""]
    for m in mods:
        lines += [f"## `{m}`", "", f"::: {m}", "    options:", "      show_root_heading: false",
                  "      show_submodules: false", "      heading_level: 3", ""]
    return "\n".join(lines)


# --- ponzi-visual --------------------------------------------------------------------------------------------------

_TS_EXPORT = re.compile(r"(?:/\*\*(?P<doc>(?:(?!\*/).)*?)\*/\s*)?export\s+(?:default\s+)?(?:async\s+)?"
                        r"(?P<kind>function|const|class|interface|type|enum)\s+(?P<name>\w+)", re.S)


def _header(text: str) -> str:
    """A TypeScript file's leading ``//`` comment, as prose."""
    lines = []
    for line in text.splitlines():
        if line.startswith("//"):
            lines.append(line[2:].strip())
        elif lines or line.strip():
            break
    return _plain(" ".join(lines))


def _plain(text: str) -> str:
    """Comment prose as Markdown text: brackets escaped, so ``[polygon][ring]`` is not read as a link."""
    return text.replace("[", "\\[").replace("]", "\\]")


def _jsdoc(doc: str | None) -> str:
    return _plain(" ".join(l.strip().lstrip("*").strip() for l in (doc or "").splitlines()).strip())


def visual_page(src: Path) -> str:
    """ponzi-visual's reference: per source file (not the tests, not the generated ``schema.d.ts``), its header
    comment and its exports with their doc comments."""
    files = sorted(f for f in src.rglob("*.ts*") if "test" not in f.relative_to(src).parts and
                   not f.name.endswith((".test.ts", ".test.tsx", ".d.ts")))
    lines = ["# ponzi-visual", "",
             "Generated from ponzi-visual's TypeScript source: each file's header comment and its exported functions, "
             "components and types with their doc comments. The API shapes (`Area`, `Boundary`, `Job` ...) are the "
             "server's, generated into `src/client/schema.d.ts` from its OpenAPI document "
             "([REST API](../rest-api.md)).", ""]
    for f in files:
        text = f.read_text(encoding="utf-8")
        rel = f.relative_to(src.parent).as_posix()
        lines += [f"## `{rel}`", ""]
        head = _header(text)
        if head:
            lines += [head, ""]
        rows = [(m["kind"], m["name"], _jsdoc(m["doc"])) for m in _TS_EXPORT.finditer(text)]
        if rows:
            lines += ["| Export | Kind | What |", "| --- | --- | --- |"]
            lines += [f"| `{n}` | {k} | {d.replace('|', '\\|')} |" for k, n, d in rows]
            lines.append("")
    return "\n".join(lines)


# --- the REST API ----------------------------------------------------------------------------------------------------

def _ref(schema: dict | None) -> str:
    if not schema:
        return ""
    if "$ref" in schema:
        return f"`{schema['$ref'].rsplit('/', 1)[-1]}`"
    if schema.get("type") == "array":
        inner = _ref(schema.get("items"))
        return f"list of {inner}" if inner else "list"
    for key in ("anyOf", "oneOf"):
        if key in schema:
            return " or ".join(x for x in (_ref(s) for s in schema[key]) if x)
    return ""


def rest_table(openapi: dict) -> str:
    """The routes of an OpenAPI document as a table: method, path, the key scope (``x-ponzi-scope``), the body,
    what it returns, and the route's description."""
    rows = ["| Method | Path | Scope | Body | Returns | What |", "| --- | --- | --- | --- | --- | --- |"]
    for path in sorted(openapi["paths"]):
        for method, op in sorted(openapi["paths"][path].items()):
            body = _ref(((op.get("requestBody") or {}).get("content") or {}).get("application/json", {}).get("schema"))
            ok = next((c for c in op.get("responses", {}) if c.startswith("2")), "")
            ret = _ref(((op["responses"].get(ok) or {}).get("content") or {}).get("application/json", {}).get("schema"))
            ret = ret or ("nothing" if ok == "204" else "")
            what = " ".join((op.get("description") or op.get("summary", "")).split()).replace("|", "\\|")
            scope = op.get("x-ponzi-scope", "")
            rows.append(f"| {method.upper()} | `{path}` | {scope} | {body} | {ret} | {what} |")
    return "\n".join(rows)


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

    for dist, (repo, folder) in DISTRIBUTIONS.items():
        src = _repo(config, repo) / folder
        if not src.is_dir():
            raise FileNotFoundError(f"no source of {dist} at {src} (check out {repo} beside the suite)")
        files.append(File.generated(config, f"reference/api/{dist}.md", content=python_page(dist, src)))
    visual = _repo(config, "ponzi-visual") / "src"
    if not visual.is_dir():
        raise FileNotFoundError(f"no ponzi-visual source at {visual} (check out ponzi-visual beside the suite)")
    files.append(File.generated(config, "reference/api/ponzi-visual.md", content=visual_page(visual)))
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
    if REST in markdown:
        doc = _repo(config, "ponzi-service") / "packages" / "server" / "openapi.json"
        markdown = markdown.replace(REST, rest_table(json.loads(doc.read_text(encoding="utf-8"))))
    if page.file.src_uri in _FROM_CORE:
        markdown = _repoint(markdown, page, files)
    return markdown
