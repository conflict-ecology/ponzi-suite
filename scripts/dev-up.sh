#!/usr/bin/env bash
# The whole system on this machine, for development and testing (not for deploying): ponzi-server on the PONZI home,
# the client loop running each job here (--executor local) and ponzi-visual's dev server, until Ctrl+C stops all
# three. The checkouts are the ones beside this suite (pixi run dev-install).
#   pixi run dev-up
#   PONZI_HOME=DIR            the PONZI home (default ~/.ponzi); keys, logs and everything the server makes go there
#   PONZI_SERVER_PORT=8780    the server's port (it listens on 127.0.0.1 only; PONZI_SERVER_HOST changes that)
#   PONZI_VISUAL_PORT=5180    the front end's port
#   PONZI_SERVER_SETTINGS=F   a server settings file (its public_url is set to the server's address when it has none)
#   PONZI_WORKER_ID=NAME      the name the server records for the client loop (default dev-<host name>)
# The first start makes four keys in $PONZI_HOME/keys, never overwritten (ponzi-core CR-093): dev-visual.key (scope
# visual, the app's own, which its dev server adds to every call), dev-worker.key (worker, for the client loop),
# dev-admin.key (user-admin) and dev-user.key (user), the two printed to log in to the app with. A dev-browser.key of
# before is revoked and removed. The home gets the development standard s1-dev, whose jobs no worker claims (its one
# stage, dev-hold, is installed nowhere), as the server's default_standard unless the given settings name another;
# and the Gaza example, a watch request approved into an area (scripts/dev-seed.py, once the server's catalogs are
# ready). The logs are appended to $PONZI_HOME/logs/server/, logs/client/ and logs/visual/.
set -euo pipefail
# shellcheck source=scripts/linux-only.sh
. "$(dirname "$0")/linux-only.sh"
suite="$(cd "$(dirname "$0")/.." && pwd)"
parent="$(dirname "$suite")"
service="$parent/ponzi-service/pixi.toml"
visual="$parent/ponzi-visual"
home="${PONZI_HOME:-$HOME/.ponzi}"
host="${PONZI_SERVER_HOST:-127.0.0.1}"
port="${PONZI_SERVER_PORT:-8780}"
vport="${PONZI_VISUAL_PORT:-5180}"
worker_id="${PONZI_WORKER_ID:-dev-$(hostname -s)}"
url="http://127.0.0.1:$port"

for f in "$service" "$visual/pixi.toml"; do
  [ -f "$f" ] || { echo "$f is missing: run pixi run dev-install first" >&2; exit 1; }
done
[ -d "$visual/node_modules" ] || { echo "ponzi-visual's packages are missing: run pixi run dev-install first" >&2; exit 1; }
for p in "$port" "$vport"; do
  if curl -s -o /dev/null "http://127.0.0.1:$p/"; then
    echo "port $p is in use: stop what runs there, or set PONZI_SERVER_PORT / PONZI_VISUAL_PORT" >&2
    exit 1
  fi
done

home="$(mkdir -p "$home" && cd "$home" && pwd)"
export PONZI_HOME="$home"
keys="$home/keys"
logs="$home/logs"
mkdir -p "$keys" "$logs/server" "$logs/client" "$logs/visual"
chmod 700 "$keys"

# The settings: the given file, or none, with public_url (the address of the assets the server hands out) set to
# this server when the file has none. Written to a temporary file, removed once the server has started (or on exit).
mkdir -p "$home/tmp"
settings="$(mktemp "$home/tmp/ponzi-dev-up.XXXXXX.yaml")"     # in the home's tmp/ (ponzi-core CR-088)
pids=()
seed=""
# shellcheck disable=SC2329  # called by the EXIT trap
stop() {
  trap - INT TERM EXIT
  [ -n "$seed" ] && kill -TERM -- "-$seed" 2>/dev/null || true
  for pid in "${pids[@]}"; do kill -TERM -- "-$pid" 2>/dev/null || true; done
  for pid in "${pids[@]}"; do wait "$pid" 2>/dev/null || true; done
  rm -f "$settings"
}
trap stop EXIT
trap 'exit 130' INT
trap 'exit 143' TERM

# The development standard (CR-093), in the home's standards/ when it is not there: a server file written by hand,
# its version the first 8 characters of its workflow's hash, whose one step is of the stage dev-hold, which no worker
# installs: its jobs are made and wait in the queue, so nothing is downloaded or computed here.
pixi run --manifest-path "$service" python - "${PONZI_SERVER_SETTINGS:-}" "$url" "$settings" "$home/standards" <<'PY'
import sys
from pathlib import Path

import yaml
from ponzi_spec.identity import workflow_hash

src, url, out, standards = sys.argv[1:]
standards = Path(standards)
standards.mkdir(parents=True, exist_ok=True)
if not list(standards.glob("s1-dev@*.yaml")):
    workflow = {"workflow": "s1-dev", "steps": [{"id": "hold", "stage": "dev-hold"}]}
    version = workflow_hash(workflow)[:8]
    workflow["version"] = version
    doc = {"standard": f"s1-dev@{version}", "final": ["hold"], "workflow": workflow,
           "description": "Development only (pixi run dev-up): its jobs wait in the queue, since no worker has the "
                          "stage dev-hold, so nothing is downloaded or computed."}
    (standards / f"s1-dev@{version}.yaml").write_text(yaml.safe_dump(doc, sort_keys=False))
doc = {}
if src:
    raw = yaml.safe_load(Path(src).expanduser().read_text()) or {}
    doc = dict(raw.get("server", raw))
doc.setdefault("public_url", url)
doc.setdefault("default_standard", "s1-dev")
Path(out).write_text(yaml.safe_dump({"server": doc}))
PY

# The keys, the first time. A key's name is unique among the active keys: when a file was removed but its key is
# still active, the new one is named with the time (revoke the old with ponzi-server keys revoke NAME).
make_key() {
  local scope="$1" name="$2" file="$keys/$2.key"
  [ -f "$file" ] && return 0
  pixi run --manifest-path "$service" ponzi-server keys add --settings "$settings" --scope "$scope" --name "$name" \
    --out "$file" 2>/dev/null ||
    pixi run --manifest-path "$service" ponzi-server keys add --settings "$settings" --scope "$scope" \
      --name "$name-$(date +%Y%m%dT%H%M%S)" --out "$file"
}
make_key visual dev-visual
make_key worker dev-worker
make_key user-admin dev-admin
make_key user dev-user
# the one shared app key of before CR-093: revoked, its file removed
if [ -f "$keys/dev-browser.key" ]; then
  pixi run --manifest-path "$service" ponzi-server keys revoke --settings "$settings" dev-browser >/dev/null 2>&1 || true
  rm -f "$keys/dev-browser.key"
fi

# job control: each process runs in a process group of its own (its id is the pid), so stopping one group stops
# pixi and everything under it together
set -m
pixi run --manifest-path "$service" ponzi-server serve --settings "$settings" --host "$host" --port "$port" \
  >> "$logs/server/serve.log" 2>&1 &
server=$!
pids+=("$server")
set +m

echo "starting ponzi-server on $url (log: $logs/server/serve.log)"
for _ in $(seq 1 240); do
  # any answer means the server is up (/v1/health needs a key: 401 without one)
  curl -s -o /dev/null "$url/v1/health" && break
  kill -0 "$server" 2>/dev/null || { echo "ponzi-server stopped; see $logs/server/serve.log" >&2; exit 1; }
  sleep 0.5
done
curl -s -o /dev/null "$url/v1/health" || { echo "ponzi-server did not answer in 2 minutes" >&2; exit 1; }
rm -f "$settings"          # read by the server when it started

set -m
# PONZI_KEY is unset, as it would win over the key file
env -u PONZI_KEY PONZI_KEY_FILE="$keys/dev-worker.key" pixi run --manifest-path "$service" \
  ponzi-client --url "$url" serve --worker-id "$worker_id" -- --executor local >> "$logs/client/serve.log" 2>&1 &
pids+=("$!")
(cd "$visual" && PONZI_URL="$url" PONZI_VISUAL_KEY_FILE="$keys/dev-visual.key" exec pixi run --manifest-path "$visual/pixi.toml" npm run dev -- --host 127.0.0.1 --port "$vport" --strictPort) \
  >> "$logs/visual/dev.log" 2>&1 &
pids+=("$!")
# the Gaza example, once the server's catalogs are ready; not one of the three: its end stops nothing
pixi run --manifest-path "$service" python "$suite/scripts/dev-seed.py" "$url" "$keys/dev-admin.key" \
  "$keys/dev-user.key" >> "$logs/server/dev-seed.log" 2>&1 &
seed=$!
set +m

cat <<MSG

  PONZI is up (development; home: $home)

    server       $url
    client loop  worker $worker_id, --executor local
    app          http://localhost:$vport

  Log in to the app with:

    Admin user key   $(cat "$keys/dev-admin.key")
    User key         $(cat "$keys/dev-user.key")

  The Gaza example is added once the server's catalogs are ready ($logs/server/dev-seed.log).

  Logs: $logs/{server,client,visual}/     Stop: Ctrl+C

MSG

# until one of the three stops, or Ctrl+C
wait -n "${pids[@]}" || true
for pid in "${pids[@]}"; do
  kill -0 "$pid" 2>/dev/null || echo "a process stopped (pid $pid); stopping the others. See $logs" >&2
done
exit 1
