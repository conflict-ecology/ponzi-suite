# Agent instructions

The instructions AI coding agents follow in every PONZI repository live here, so the rules are written once and every repository loads the same version. The pages under `docs/agents/` are different: they are published on the site and tell agents how to use and change PONZI. These files configure the agents themselves.

| File | Loaded by |
| --- | --- |
| `shared.md` | every repository (through its own file below) |
| `ponzi-core.md` | `ponzi-core/CLAUDE.md` |
| `ponzi-service.md` | `ponzi-service/CLAUDE.md` |
| `ponzi-visual.md` | `ponzi-visual/CLAUDE.md` |
| (`shared.md` only) | `ponzi-suite/CLAUDE.md`, for work in the suite itself |

## How a repository loads its file

Each repository keeps a one-line `CLAUDE.md` that imports its file from the suite, which is checked out beside it (the same layout the docs CI uses):

```markdown
@../ponzi-suite/agents/ponzi-core.md
```

Claude Code resolves the path relative to the `CLAUDE.md` that contains it. Without a suite checkout beside the repository the import loads nothing, so clone the suite first.

## Skills

Skills are packaged as the `ponzi-dev` plugin in `plugins/ponzi-dev/`, published through this repository's marketplace (`.claude-plugin/marketplace.json`). The shared `.claude/settings.json` in this repository registers the marketplace and enables the plugin, and each repository's `.claude` is a link to this one (`../ponzi-suite/.claude`), committed in that repository, so nothing has to be installed by hand. Claude Code registers the marketplace once you trust the folder.

| Skill | Use |
| --- | --- |
| `ux` | designing or reviewing any user interface, with the Laws of UX |

## Changing these files

A change to a repository's file changes that repository's rules, so it goes through that repository's change process (for ponzi-core, a signed request in `docs/requests/`).
