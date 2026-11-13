"""MkDocs hooks: content that comes from ponzi-spec, so the docs never restate it by hand.

- ``<!-- ponzi:collections -->`` in a page becomes the table of the profile's Collections.
- The PONZI extension's JSON Schema is published at ``schemas/ponzi/<version>/schema.json``, the URL Items name.
- ``<!-- ponzi:requests -->`` becomes the index table of the change requests (``docs/history/requests/CR-*.md``,
  kept in the suite since CR-071, as the store contracts are in ``docs/reference/contracts/``).
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
from ponzi_spec.stac import extension_schema, extension_versions

MARKER = "<!-- ponzi:collections -->"
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
    """Publish the extension schema, every version shipped (an Item made before names its own; CR-102)."""
    for version in extension_versions():
        out = Path(config["site_dir"]) / "schemas" / "ponzi" / version / "schema.json"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(extension_schema(version), indent=2) + "\n", encoding="utf-8")


def _repo(config, name: str) -> Path:
    """A checkout beside the suite (``ponzi-core``, ``ponzi-service``, ``ponzi-visual``), or where
    ``$PONZI_CORE``, ``$PONZI_SERVICE`` or ``$PONZI_VISUAL`` say."""
    here = Path(config["config_file_path"]).resolve().parent
    env = "PONZI_" + name.removeprefix("ponzi-").upper()
    return Path(os.environ.get(env) or here.parent / name)


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
             "([REST API](../../service/rest-api.md)).", ""]
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



def on_files(files, config):
    """Add the API reference pages, generated from the checkouts beside the suite."""
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
    return files


STALE = "- **Stale:**"
IN_PART = "- **Superseded in part:**"


def _line(text: str, mark: str) -> str:
    """The rest of a change request's line that starts with ``mark``, else empty."""
    for line in text.splitlines():
        if line.startswith(mark):
            return line[len(mark):].strip()
    return ""


def _index(paths: list[Path], folder: str, page_dir: str) -> str:
    """The index table of the change requests: each one's link, title, and what of it no longer applies."""
    rows = ["| Page | Title | No longer applies |", "| --- | --- | --- |"]
    for p in paths:
        text = p.read_text(encoding="utf-8")
        title = _title(text, p.stem).replace("|", "\\|")
        stale, part = _line(text, STALE), _line(text, IN_PART)
        note = f"**Stale:** {stale}" if stale else (f"In part: {part}" if part else "")
        rows.append(f"| [{p.stem}]({os.path.relpath(folder, page_dir)}/{p.name}) | {title} | {note.replace('|', chr(92) + '|')} |")
    return "\n".join(rows)



_on_page_markdown_collections = on_page_markdown


def on_page_markdown(markdown, page, config, files):  # noqa: F811  (extends the one above)
    """The collections table, the requests index and the REST table."""
    markdown = _on_page_markdown_collections(markdown, page, config, files)
    if REQUESTS in markdown:
        docs = Path(config["docs_dir"])
        requests = sorted((docs / "history" / "requests").glob("CR-*.md"))
        page_dir = os.path.dirname(page.file.src_uri)
        markdown = markdown.replace(REQUESTS, _index(requests, "history/requests", page_dir))
    if REST in markdown:
        doc = _repo(config, "ponzi-service") / "packages" / "server" / "openapi.json"
        markdown = markdown.replace(REST, rest_table(json.loads(doc.read_text(encoding="utf-8"))))
    return markdown
