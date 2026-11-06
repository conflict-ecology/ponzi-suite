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
# The first start makes two keys in $PONZI_HOME/keys, never overwritten: dev-worker.key (scope worker, for the client
# loop) and dev-browser.key (client:write, printed for the app). The logs are appended to $PONZI_HOME/logs/server/,
# logs/client/ and logs/visual/.
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
settings="$(mktemp "${TMPDIR:-/tmp}/ponzi-dev-up.XXXXXX.yaml")"
pids=()
# shellcheck disable=SC2329  # called by the EXIT trap
stop() {
  trap - INT TERM EXIT
  for pid in "${pids[@]}"; do kill -TERM -- "-$pid" 2>/dev/null || true; done
  for pid in "${pids[@]}"; do wait "$pid" 2>/dev/null || true; done
  rm -f "$settings"
}
trap stop EXIT
trap 'exit 130' INT
trap 'exit 143' TERM

pixi run --manifest-path "$service" python - "${PONZI_SERVER_SETTINGS:-}" "$url" "$settings" <<'PY'
import sys
from pathlib import Path

import yaml

src, url, out = sys.argv[1:]
doc = {}
if src:
    raw = yaml.safe_load(Path(src).expanduser().read_text()) or {}
    doc = dict(raw.get("server", raw))
doc.setdefault("public_url", url)
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
make_key worker dev-worker
make_key client:write dev-browser

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
(cd "$visual" && PONZI_URL="$url" exec pixi run --manifest-path "$visual/pixi.toml" npm run dev -- --host 127.0.0.1 --port "$vport" --strictPort) \
  >> "$logs/visual/dev.log" 2>&1 &
pids+=("$!")
set +m

cat <<MSG

  PONZI is up (development; home: $home)

    server       $url
    client loop  worker $worker_id, --executor local
    app          http://localhost:$vport

  Key to enter in the app (client:write):

      $(cat "$keys/dev-browser.key")

  Logs: $logs/{server,client,visual}/     Stop: Ctrl+C

MSG

# until one of the three stops, or Ctrl+C
wait -n "${pids[@]}" || true
for pid in "${pids[@]}"; do
  kill -0 "$pid" 2>/dev/null || echo "a process stopped (pid $pid); stopping the others. See $logs" >&2
done
exit 1
