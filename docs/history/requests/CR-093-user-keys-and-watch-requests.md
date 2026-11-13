# CR-093: people log in with their own key, ask for areas to be watched, and find outputs by tag

- **Requested by / date:** owner, 2026-11-12 ("lets go with option 1 change with some adjustment", after comparing ways to log in without another service)
- **Status:** signed off (2026-11-12; decisions 3 and 5 changed by the owner, below), implemented (unreleased)

## Why
ponzi-visual is used by people who share one `client:write` key (`dev-browser.key` under `dev-up`). The key sits in the browser tab's `sessionStorage`, readable by any script on the page; the access log cannot tell people apart; and anyone holding it makes watched areas, which start downloads and cluster work at once, with nobody deciding whether they should. Finding outputs means knowing the STAC search; nothing shows what a tag covers (its tiles, bursts and places).

The owner chose PONZI's own keys over an outside sign-in service: one key per person, swapped at login for a session the page cannot read, and an admin who decides what is watched.

## What changes

### Who is who: scopes
Three scopes are added (`ponzi_server.auth.IMPLIES`); the four that exist stay as they are, for Python, the command line, agents and workers.

| Scope | Holds | Made by | For |
| --- | --- | --- | --- |
| `user` | `client:read`, and asking for areas to be watched | an admin user, in the app; `ponzi-server keys add` | a person using the app |
| `user-admin` | `user`, deciding watch requests, making and revoking `user` and `user-admin` keys | `ponzi-server keys add` (the first one); an admin user | a person who runs the lab's PONZI |
| `visual` | logging a person in, and passing that person's session on; nothing else | `ponzi-server keys add` | the app itself (its dev server, or the deployment's reverse proxy) |

`admin` holds the three new scopes too. An admin user cannot make `admin`, `worker`, `visual` or `client:*` keys: those stay on the server's machine (`ponzi-server keys add`).

### Logging in: sessions
- **The app's own key.** Whatever serves the app forwards `/v1` to the server and adds `Authorization: Bearer <visual key>` to every request: Vite's dev server under `dev-up` (`PONZI_VISUAL_KEY_FILE`), the reverse proxy in a deployment. The browser never sees it.
- **A person's key.** `POST /v1/sessions` with a `user` or `user-admin` key, through the app (its visual key present), answers with a session cookie: `HttpOnly`, `Secure` (but on `localhost`), `SameSite=Strict`, path `/v1`. The server keeps the hash of the session token, the key it was opened with and its expiry (14 days by default, `session_days`), in a new table of `server.db`. The key is never stored by the page.
- **Each request** through the app carries the visual key and the cookie; the server acts as the session's person, with that key's scope, and the access log names that person. A cookie without the visual key is refused, and so is the visual key without a cookie (but for logging in and `GET /v1/health`).
- **Logging out** (`DELETE /v1/sessions/current`) ends the session on the server. Revoking a key ends its sessions. `GET /v1/me` gives the person's key name and scope, which the app shows and uses to show the admin pages.
- **Python, the command line and agents** keep sending a key as a bearer token, any scope, as now; a `user` key works there too.

### Asking for an area: watch requests
The map's **Watch** becomes **Request**. A watch request is what an area was made from (tiles, tags, a first and a last day), from a person, waiting for an admin user. Its routes are `/v1/watch-requests` (`/v1/requests` stays the one-off run it is):

- `POST /v1/watch-requests` (`user`): tiles, tags, `start_date`, `end_date`; status `pending`, with the requester's key name and the time.
- `GET /v1/watch-requests` (`user`: their own; `user-admin`: all, `?status=`).
- `POST /v1/watch-requests/{id}/approve` (`user-admin`): makes the area as `POST /v1/areas` does (the server's standard, its cadence, its jobs at once), and records who approved it, when, and the area's id. A request the server cannot make an area of (no standard, CR-068) stays pending, with the reason.
- `POST /v1/watch-requests/{id}/deny` (`user-admin`): with an optional reason, which the requester sees.
- `client:write` and `admin` keys still make areas directly (`POST /v1/areas`), for scripts and agents.

### Tags: one word each
A tag is one word of letters, digits, `-` and `_` (`^[A-Za-z0-9_-]{1,40}$`), at most 20 per area, given comma separated; spaces around commas and a leading `#` are dropped, and a repeat (in any case) is kept once (`ponzi_spec.api`). A tag with any other character is refused with the rule. The rule holds for every tag: the owner starts fresh, so no area of before is carried over, and the docs' and the tests' examples of other tags (`flood 2024`) are replaced.

### Finding outputs by tag
- `GET /v1/tags?q=` (`client:read`): each tag that matches, with its counts: areas, tiles, bursts, analysis Items, and the latest output date.
- `GET /v1/tags/{tag}` (`client:read`): the tag's places, its admin 0, admin 1 and admin 2 boundaries (names and codes, from `boundaries.sqlite3`, each boundary once), and one row per tile: the tile, its admin 0, 1 and 2, its bursts, its analysis Items and their latest date, and its areas.
- Downloads are what they are: `GET /v1/stac/search?tags=` and `GET /v1/assets/...`, from the app, Python (`c.search(tags=[...])`, `c.download`) or the command line (`ponzi-client search --tags`, `download`). `ponzi-client` gains `tags` and `tag`.

### ponzi-visual
Pages, in the drawer: **Request** (the map, the first page), **Search**, **Admin** (shown to an admin user only), **Settings**, **Log out**. The design follows the Laws of UX (ponzi-suite's `ux` skill); the law behind each choice is named.

- **Log in.** One field, "Your key", and **Log in**; under it, one line: "Ask your PONZI admin for a key." (Paradox of the Active User: help where it is needed). A wrong or revoked key says so on the form. The drawer's foot names who is logged in.
- **Request** (the map). As the map is now, with the panel's **Watch** renamed **Request N tiles**.
    - Tags: one field, "Tags (comma separated)", checked as typed: each valid tag becomes a chip, and an invalid one stays in the field with "Letters, digits, - and _ only" under it (Postel's Law: accept spaces and `#`, say the rule once).
    - After sending: "Request sent. An admin will review it; you'll see the answer under My requests." (Peak-End Rule).
    - **My requests**, under the form: each request with its tiles, tags, days and a status (pending, approved with a link to its area, denied with the reason), newest first (Zeigarnik Effect: what is still open stays in sight).
- **Search.** A field for tags (the same rule), and a list with one row per matching tag: the tag, areas, tiles, bursts, outputs, latest output. A row opens the tag's page. With an empty field the list shows every tag, most recent output first (Hick's Law: start from something, not a blank).
- **A tag's page.**
    - At the top, one box (Common Region): the tag, its counts, and its places in three labelled lines, **Countries** (admin 0), **Admin 1**, **Admin 2**; a line longer than about eight names folds behind "and N more" (Chunking).
    - **Download**, beside the box: the tag's outputs, each Item's assets to download. (No copyable `ponzi-client` command or Python line: removed by the owner, 2026-11-12. Python and the command line are documented on [Clients](../../using/clients.md).)
    - Below, the table: one row per tile, sortable, columns tile, country, admin 1, admin 2, bursts, outputs, latest; a tile's row links its outputs (Jakob's Law: a plain table that sorts by its headers).
- **Admin**, two tabs:
    - **Requests**, pending first with their count on the tab (Von Restorff: what needs a decision stands out). A request: who asked and when, its tiles on a small map, its bursts, tags and days, and **Approve** and **Deny** side by side, Deny opening a field for the reason. Decided requests below, with who decided.
    - **Keys**: the keys an admin user can manage (name, scope, made, by whom, last used), **New key** (a name, and the scope `user` or `user-admin`, `user` by default), and **Revoke** with a confirmation. A new key is shown once, with **Copy** and "This is the only time it is shown." (Tesler's Law: the server keeps nothing it could show again, so the page says so).

### `dev-up` (ponzi-suite)
On its first start, in `$PONZI_HOME/keys/`, never overwritten:

| File | Scope | Shown |
| --- | --- | --- |
| `dev-visual.key` | `visual` | never: the app's dev server reads it (`PONZI_VISUAL_KEY_FILE`) |
| `dev-worker.key` | `worker` | never: the client loop reads it |
| `dev-admin.key` | `user-admin` | printed: "Admin user key" |
| `dev-user.key` | `user` | printed: "User key" |

`dev-browser.key` is no longer made; one left in a home is revoked by the next start. The printout gives both keys to log in with.

**The development standard.** `dev-up` writes a standard of its own into the home's `standards/`, `s1-dev`, if it is not there: a server file written by hand (no `workflow_hash`, CR-091), whose workflow is one step of the stage `dev-hold`, which no worker installs. Its jobs are made and wait in the queue, and no worker claims them, so nothing is downloaded or computed on a development machine. `dev-up` names it as the server's `default_standard` unless the settings given as `PONZI_SERVER_SETTINGS` name another. `dev` is added to the scope words of a standard's id (`ponzi_spec.naming`).

**The Gaza example.** The first start of a home adds a watch request: the Major TOM tiles over the Gaza Strip (the box 34.20 to 34.57 E, 31.21 to 31.60 N), tag `gaza`, from 2023-10-07, no last day, requested by `dev-user` and approved by `dev-admin`, which makes its area under `s1-dev`. It lives in the PONZI home, as any area does.

### The demo (ponzi-visual `pixi run server`)
Makes the same four keys, writes them into `keys.json` by scope, and prints the two to log in with. The end-to-end test logs in with the user key.

## Do results change?
No. No computed number, content id or store changes. What changes is who may make an area through the app (an admin user, by approving a request), and which tags are accepted.

## Tests
- ponzi-spec: the tag rule (letters, digits, `-`, `_`; `#` and spaces dropped; repeats; the limits; the refusal names the rule); the new API models.
- ponzi-server: each scope's routes and refusals; a session made only through a visual key, kept as a hash, ended by logging out, by its expiry and by revoking its key; a cookie without the visual key, and the visual key without a cookie, refused; a watch request's life (pending, approved into an area with the server's standard, pending with a reason when there is none, denied with a reason); a `user` sees only their own requests; an admin user makes only `user` and `user-admin` keys; `GET /v1/tags` and `/v1/tags/{tag}` on a fixture with tiles, bursts, Items and boundaries; the access log names the session's person; the OpenAPI document is regenerated and committed.
- ponzi-client: `tags`, `tag`, and logging in is not needed for a bearer key.
- ponzi-visual: log in and out; the tag field's chips and refusal; a request sent and shown under My requests; the Admin page shown only to an admin user; approving and denying; a new key shown once; Search and a tag's page from fixtures; the end-to-end test against the demo.
- ponzi-suite: `dev-up` makes the four keys once, prints two, revokes a leftover `dev-browser.key`, and adds the Gaza request once.

## Changed by the owner while it was built (2026-11-12)
- The tag page's Download has no copyable `ponzi-client` command or Python line.
- The Keys tab names the scopes formally: **User** ("May submit watch requests, search tags, and download outputs.") and **Administrator** ("May also approve or deny watch requests, and issue or revoke User and Administrator keys."); the API values stay `user` and `user-admin`.
- The map's tile states are shown and hidden by a checkbox each in the legend (kept in the browser), and "Outputs, not monitored" is called **Archived**. The API's state value stays `outputs`.

## Decided at sign-off
Each is written above as recommended; the owner confirms or changes it.
1. **Area creation without a request.** `client:write` and `admin` keys keep making areas directly (scripts, agents); only the app goes through requests.
2. **What an admin user can make:** `user` and `user-admin` keys only.
3. **The Gaza example:** in the PONZI home `dev-up` runs on, approved into an area under a development standard, `s1-dev`, whose jobs no worker claims (owner: "make a dummy standard used for dev purposes").
4. **Session length:** 14 days, a server setting.
5. **Old tags:** none kept. The rule holds for every tag, and the examples of other tags are removed (owner: "remove all old tags. I am starting fresh").

## Version
- ponzi-spec: major (the tag rule refuses tags it accepted; new models).
- ponzi-server: major (scopes, sessions, watch requests, tag routes; the app's areas go through requests). The REST API stays `v1`: the routes it had answer as before, but for the tag rule.
- ponzi-client: minor (`tags`, `tag`).
- ponzi-visual: major (log in with a key, the Request, Search and Admin pages).
- ponzi-suite: `dev-up` and the docs (Logins and keys, Watched areas, Using the map, Clients, Quickstart, Troubleshooting, REST API).
- Standard: no change.
