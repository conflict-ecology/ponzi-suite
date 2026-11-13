# CR-098: the client runs anywhere; it starts its workers here or over its own ssh connection, and outputs go straight to the server

- **Requested by / date:** owner, 2026-11-13 ("I want the client to be run anywhere."; "the client to be able to run off cluster but can initiate short lived workers via ssh that takes the available work to be done and run them."; "ssh only: yes but maintain an option to not run via ssh as it is now"; "outputs can go directly to server"; on the client keeping one ssh connection rather than one per worker: "adjust CR-95-CR-98 to account for the long lived connection")
- **Status:** signed off (2026-11-13; the review's points 10 and 11 applied, decisions as recommended), implemented (unreleased), awaiting review; uncommitted
- **Builds on:** CR-096 (the sweep: one worker call per tick) and CR-097 (status reaches the server, so no one needs `squeue` beside the worker).
- **Changes in part:** CR-063 ("the worker talks to no server"): the worker may now send a job's final outputs to the server with a one-time upload ticket the client hands it; it holds no key and makes no other call.

## Why
The client already runs its worker through a command (`--worker`, default `ponzi-worker`), and the worker talks to no server, so `--worker "ssh hpc ponzi-worker"` nearly works: the sweep's input goes in on stdin, its answer comes back on stdout, and the worker plans, submits and checks its SLURM batches on the cluster. Two things still tie the client to the worker's machine:

- **Delivery.** A `done` answer gives each asset as a file on the worker's machine: a store zipped into `{cache}/work/deliver-<job>/`, or a plain file in its cache entry, `{cache}/<collection>/<content_id>/`. The client opens those files to upload them, or in path mode copies them under `outputs.root`, and deletes the `scratch` folder. From another machine those paths do not exist: every job runs to the end, then fails.
- **Arguments.** The worker args after `--` go on the command line as they are. Through ssh they become one remote shell string, so a value with a space or a shell character breaks.

And with the client off the cluster, outputs sent through it would cross the network twice (cluster → client → server), and through what may be a laptop. A connection per call would also cost: a handshake for every sweep, upload, fetch and clean, a login session each on the login node, and, on a cluster with two-factor login, a prompt each, which no unattended loop can answer.

## What changes

### The rule
The client never opens, stats, copies or deletes a path the worker gave it. Everything on the worker's side goes through the worker command, so a local worker and a remote one are one code path.

### Where the worker runs
- **Here (the default, as today):** without `--worker-host`, the worker command runs on the client's machine: on the cluster's login node, in a SLURM job, or on the server's machine.
- **Through ssh:** with `serve --worker-host HOST`, every worker command runs on HOST over the client's one ssh connection (below), the command line built with `shlex.join`, so the args after `--` reach the worker as given. The rest of ssh (user, key, a jump host) comes from `~/.ssh/config`.

The worker is the same either way: a short-lived process per call, the input on stdin, one answer on stdout. Only the transport lasts.

### The connection
With `--worker-host`, `serve` keeps one ssh connection to HOST open while it runs, and every worker call goes over it as a new session (OpenSSH connection sharing: the system `ssh`, no library):

- **Opened at start:** `ssh -M -S <socket> -o ControlPersist=yes -o ServerAliveInterval=60 -o ServerAliveCountMax=3 -N HOST`, with the socket in a private folder (mode 700) under the system's runtime or temporary folder, named by ssh's `%C` (a hash of the host, port and user), so its path stays under the 104-character limit of a socket's name whatever the `--worker-id`. By default the start is interactive (`--ssh-prompt start`): a password or two-factor prompt is answered once, at the terminal that started `serve`. `--ssh-prompt never` opens it with `BatchMode`, for unattended starts (a cron job, `scrontab`, a service), and `serve` exits at once if it cannot.
- **Each call:** `ssh -S <socket> -o BatchMode=yes HOST -- <command line>`: no handshake and no prompt, a new session on the open connection.
- **Kept open:** the keepalives hold an idle connection through the login node's idle timeout; before each sweep, `serve` checks it (`ssh -S <socket> -O check HOST`).
- **Reopened:** a connection found closed is reopened with `BatchMode` (a key, an agent, a Kerberos ticket), at most once per sweep. If it cannot be without a prompt, the sweep gets no answer (CR-096): the jobs are left as they were, after three such sweeps their leases expire, and the log says the connection needs `serve` restarted at a terminal.
- **Closed on stop:** `ssh -S <socket> -O exit HOST`, and the socket's folder removed.
- One connection serves every call of the loop: the sweep, `upload`, `fetch` and `clean`. Two loops have two connections.
- **`--worker`** stays the worker command on the worker's machine, for example `env PONZI_HOME=/path/to/home /path/to/env/bin/ponzi-worker` (a non-interactive ssh session reads no login profile).

### Delivery
A `done` answer gives each asset's `size_bytes` and `sha256` beside its href. Then, by the server's outputs mode:

- **`upload`, direct (the default):** the client asks the server for a ticket per asset (`POST /v1/uploads`, as today) and runs `<worker> upload -` with the tickets on stdin (`[{"path": ..., "ticket": UploadTicket}, ...]`); the worker sends each file to its ticket's `url` with the ticket's `headers`, and answers which were sent. The client then completes the job. The bytes go from the worker's machine to the server once.
- **`upload`, through the client:** when the worker's machine cannot reach the server (its answer says so for an asset: the connection refused or timed out), or with `serve --deliver through-client`, the client runs `<worker> fetch PATH` and streams its stdout into the upload itself, as before but without reading the worker's files. No copy is kept on the client's machine.
- **`path`:** the client copies nothing. The sweep's input carries the server's `outputs`, and the worker writes each final asset under `outputs.root` itself (as CR-041 first put it: "worker is also responsible for handling saving outputs to the right paths"); the answer's hrefs are those paths, and the client completes the job with them.
- **Scratch:** after completing or failing jobs, the client runs `<worker> clean JOB_ID ...` once for all of them.

Per tick, one worker call runs the sweep; delivery adds one `upload` call per finished job (or one `fetch` per asset) and one `clean`. Through ssh, each is a session on the loop's one connection.

### ponzi-server: a ticket carries its own permission
- `POST /v1/uploads` (worker scope, as today) returns the ticket with a one-time token in its `headers` (`X-Ponzi-Upload-Token`); the server keeps the token's hash with the upload.
- `PUT /v1/uploads/{upload_id}` accepts that token instead of a key: for that one upload, until it expires (`upload_seconds`) or is done. Size and sha256 are checked as today. A key with the worker scope still works.
- `UploadTicket` already has `headers`; no contract changes.

### ponzi-worker
- **`sweep -`** reads `outputs` beside `jobs` (absent: `upload`). In a `done` answer each asset carries `size_bytes` and `sha256`; in `path` mode its href is the file written under `outputs.root`, whole or not at all (a `.partial` renamed, as `serve.save` does today, moved here), a file already there with the same bytes kept.
- **`upload -`** (new): sends each listed file to its ticket and answers per asset `sent`, `unreachable` (no connection to the server: the client falls back to `fetch`), or `failed` with the server's reply. It sends only files under the cache root, to the ticket's URL only, and talks to the server for nothing else.
- **`fetch PATH`** (new): the bytes of one file on stdout, for delivery through the client. It takes a file under the cache root, after resolving links, and refuses anything else.
- **`clean JOB_ID ...`** (new): removes `{cache}/work/deliver-<job>/` of each; nothing else. One already gone is not an error.

### Unchanged
The worker still sends the server no status (CR-097) and makes no call but a ticket's upload; the compute nodes need no network (sweeps and uploads run where the client's worker command runs: the login node, or the client's own machine).

### Docs
- Running on the cluster (`service/hpc.md`): running the worker here or through ssh (`--worker-host`); the connection `serve` keeps, the prompt at start (`--ssh-prompt`), what a key or agent allows when it must be reopened unattended, and what the log says when it cannot; direct uploads, which need the worker's machine (the login node) to reach the server's URL (so they depend on where the server is deployed: a public address, or a VPN the cluster may not be on), and the fallback through the client, which covers a server the cluster cannot reach; that a client that sleeps or loses its network lets its leases expire (safe: the jobs return to the queue, and the next sweep finds their work in flight or in the cache); and that the login node, or a VM, remains the place for a loop that must not stop.
- The clients: `--worker-host`, `--deliver`. The worker: `upload`, `fetch`, `clean`, the sweep's `outputs`. The REST API: the ticket's token.

## Do results change?
No. The same Items, assets and manifests reach the server; only how the bytes travel changes.

## Tests
- ponzi-client: `serve` through a fake `ssh` (a script on `PATH` that runs its command through `sh -c`, as ssh does, and keeps a master's state in a file for `-M`, `-O check` and `-O exit`): a whole job, with worker args holding spaces and quotes; the master opened once at start and every call over its socket with `BatchMode=yes`; `--ssh-prompt never` exits when the master cannot open; a master found closed is reopened once per sweep, and a reopen that fails gives the sweep no answer; stop closes the master and removes its folder; the same job without `--worker-host`, run here. In the test, opening or stat-ing a path under the worker's home raises in the client's process (the worker, a subprocess, is unaffected), so a delivery that reads the worker's files fails the test. Direct upload by default; an asset answered `unreachable` delivered through `fetch`; `--deliver through-client`; path mode copies nothing; one `clean` for the jobs finished.
- ponzi-worker: the sweep with and without `outputs`; `size_bytes` and `sha256` in the answer; path mode writes whole files under `root` and keeps a same file already there; `upload` against a test server: sent, a refused connection answered `unreachable`, a wrong size answered `failed`, a file outside the cache refused; `fetch` of a zipped store in a deliver folder and of a plain file in a cache entry, refused outside the cache root (`..`, a symlink out); `clean` of the named jobs' folders only, and of one already gone.
- ponzi-client: the socket's path under 104 characters with a long `--worker-id`.
- ponzi-server: a ticket's token allows its own upload once, not another upload, not after it expires, not after it is done, and not any other route; a key with the worker scope still uploads.
- The loop tests pass unchanged in behaviour.

## Decided at sign-off
Each is written above as recommended; the owner confirms or changes it.
1. **The worker runs here by default, or through ssh** with `--worker-host` (owner: "maintain an option to not run via ssh as it is now"); nothing listens on the cluster, no daemon.
2. **The client keeps one ssh connection,** with OpenSSH's connection sharing; each worker is still a short-lived process, a new session on it. A prompt is answered once, at start (`--ssh-prompt start`, the default), or never (`--ssh-prompt never`); a connection that cannot be reopened without one ends in no answer (CR-096).
3. **One code path:** a local worker is also reached through the worker command (`upload`, `fetch`, `clean`), so local runs test what remote runs use.
4. **Outputs go straight to the server** (owner: "outputs can go directly to server") with a one-time ticket the client obtains; the worker holds no key. Through the client remains the fallback and an option.
5. **Path mode is the worker's:** it needs the worker's machine, not the client's, to share the server's home.

## Version
- ponzi-client: minor (`--worker-host`, `--ssh-prompt`, `--deliver`; the connection; delivery through the worker).
- ponzi-worker: minor (`upload`, `fetch`, `clean`, the sweep's `outputs`, the answer's size and sha256).
- ponzi-server: minor (an upload ticket's token).
- ponzi-spec: no change.
- ponzi-suite: the docs above.
- Standard: no change.
