# shellcheck shell=bash
# Sourced at the start of the dev scripts: PONZI runs on Linux on x86-64 only for now, the one platform its pixi
# workspaces are solved for (linux-64). Anything else stops here, before a clone or an install, saying why.
case "$(uname -s)/$(uname -m)" in
  Linux/x86_64) ;;
  *)
    echo "PONZI runs on Linux (x86-64) only for now: this machine is $(uname -s) $(uname -m)." >&2
    echo "The pixi workspaces of ponzi-core, ponzi-service and ponzi-visual are solved for linux-64 alone." >&2
    exit 1 ;;
esac
