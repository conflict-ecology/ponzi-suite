#!/usr/bin/env bash
# A development workstation in one command: ponzi-core, ponzi-service and ponzi-visual beside this suite, each
# installed. For development and testing on one machine, not for deploying.
#   pixi run dev-install                       the default environments of ponzi-core and ponzi-service, and
#                                              ponzi-visual's packages
#   PONZI_ENVS="ml isce3" pixi run dev-install also these environments (or: pixi run dev-install ml isce3)
#   PONZI_REF=TAG pixi run dev-install         clone this branch or tag instead of the default branch
# A checkout that exists is used as it is: never pulled, reset or overwritten. The installs follow each checkout's
# lock file (pixi install --locked), so they change nothing in it. ml-gpu and isce3 need an NVIDIA driver for CUDA
# 12.9; CONDA_OVERRIDE_CUDA=12.9 installs them anyway (pixi reads it from the environment).
set -euo pipefail
suite="$(cd "$(dirname "$0")/.." && pwd)"
parent="$(dirname "$suite")"
org="https://github.com/conflict-ecology"

envs=()
if [ "$#" -gt 0 ]; then
  envs=("$@")
elif [ -n "${PONZI_ENVS:-}" ]; then
  read -r -a envs <<< "$PONZI_ENVS"
fi
for env in "${envs[@]}"; do
  case "$env" in
    default | ml | ml-gpu | isce3) ;;
    *) echo "unknown environment '$env' (one of default, ml, ml-gpu, isce3)" >&2; exit 2 ;;
  esac
done

for repo in ponzi-core ponzi-service ponzi-visual; do
  dir="$parent/$repo"
  if [ -e "$dir" ]; then
    if [ -e "$dir/.git" ]; then      # a clone, or a worktree (.git is then a file)
      echo "$repo: using the checkout in $dir as it is"
    else
      echo "$dir exists and is not a git checkout: move it away, or clone $org/$repo there yourself" >&2
      exit 1
    fi
  else
    echo "$repo: cloning $org/$repo into $dir"
    branch=()
    [ -n "${PONZI_REF:-}" ] && branch=(--branch "$PONZI_REF")
    git clone "${branch[@]}" "$org/$repo.git" "$dir"
  fi
done

for repo in ponzi-core ponzi-service; do
  for env in default "${envs[@]}"; do
    echo "$repo: installing the $env environment"
    pixi install --locked --manifest-path "$parent/$repo/pixi.toml" -e "$env"
  done
done

visual="$parent/ponzi-visual"
# npm ci empties node_modules first, so it runs only when the packages are missing or older than the lock file
if [ -f "$visual/node_modules/.package-lock.json" ] && \
   [ ! "$visual/package-lock.json" -nt "$visual/node_modules/.package-lock.json" ]; then
  echo "ponzi-visual: the packages are installed"
  pixi install --locked --manifest-path "$visual/pixi.toml"
else
  echo "ponzi-visual: installing Node and the packages"
  pixi run --locked --manifest-path "$visual/pixi.toml" install
fi

echo
echo "PONZI is installed in $parent. Start it with: pixi run dev-up"
