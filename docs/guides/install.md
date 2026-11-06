# Install

!!! note "Linux only, for now"
    PONZI runs on Linux on x86-64. Its pixi workspaces are solved for `linux-64` alone, and the development commands (`dev-install`, `dev-up`) check the machine when they start and stop on any other system. macOS and Windows are not supported yet; on Windows, WSL 2 with a Linux distribution is the closest.

Pick the line that matches what you want to do; each needs only what it says.

| You want to | Install | You get |
| --- | --- | --- |
| use a running PONZI server from Python or a shell | [the client](#the-client) (pip) | `ponzi-client` |
| run PONZI on this machine, without a server | [ponzi-core](#ponzi-core) (pixi) | `ponzi`, `ponzi-pipeline`, `ponzi-models` |
| run the service: a server, the client loop, the worker | [ponzi-service](#ponzi-service) (pixi) | `ponzi-server`, `ponzi-client`, `ponzi-worker`, and ponzi-core's commands |
| see it in the browser | [ponzi-visual](#ponzi-visual) (pixi) | the map front end, against a server |
| develop and test the whole system on one machine | [For development](#for-development): `pixi run dev-install` in ponzi-suite | all of the above, then `pixi run dev-up` starts the server, the client loop and the front end |

The repositories are under the GitHub organisation `conflict-ecology`. The pixi installs expect them checked out side by side, as ponzi-service and ponzi-visual use the code of the checkouts beside them:

```
workspace/
  ponzi-core/  ponzi-service/  ponzi-visual/  ponzi-suite/
```

Then set up the logins the work needs: [Authentication](authentication.md).

To set up a development workstation in one command instead, see [For development](#for-development).

## The client

One pip command, in any Python 3.11 or later. `ponzi-spec` is named in the same command because it is not on PyPI:

```
pip install "ponzi-spec @ git+https://github.com/conflict-ecology/ponzi-core@main#subdirectory=packages/spec" \
            "ponzi-client @ git+https://github.com/conflict-ecology/ponzi-service@main#subdirectory=packages/client"
```

It needs nothing else (pydantic, PyYAML, httpx). Then point it at a server: [The clients](../reference/clients.md).

## ponzi-core

```
cd ponzi-core
pixi install                 # the default environment: ponzi-spec, ponzi, ponzi-pipeline, ponzi-models
pixi run test                # optional: the fast tests
pixi run ponzi --help
```

The other environments are installed only when asked for (`pixi install -e NAME`, or the first `pixi run -e NAME ...`):

| Environment | Adds | For |
| --- | --- | --- |
| `default` | the geospatial stack; never torch | everything that needs no GPU and no ISCE3 |
| `ml` | torch on the CPU | the TiDE forecaster (the default) on the CPU, the rehearsal's tiny fit |
| `ml-gpu` | torch 2.14.1 from conda-forge, CUDA 12.9 build; wandb | training on a GPU |
| `isce3` | ISCE3 0.25.22, CUDA 12.9 build, with s1reader, COMPASS, dem_stitcher, GDAL, asf_search | the coherence chain from SLCs |

## ponzi-service

```
cd ponzi-service
pixi install                 # ponzi-server, ponzi-client, ponzi-worker, with ponzi-core's distributions from ../ponzi-core
pixi run test                # optional
```

It has the same four environments as ponzi-core; the worker's stages run in the one a stage declares, and a cluster's release installs all four. How the pieces run together: [Quickstart](quickstart.md) on one machine, [Running on the cluster](hpc.md).

## ponzi-visual

```
cd ponzi-visual
pixi run install             # Node and the front end's packages
pixi run dev                 # http://localhost:5173, against PONZI_URL (default the local demo server)
```

`pixi run server` makes and serves a demo installation from the ponzi-service checkout beside it ([Quickstart](quickstart.md)).

## For development

On a workstation for developing and testing PONZI, not for deploying it, one command from ponzi-suite clones what is missing and installs it all:

```
git clone https://github.com/conflict-ecology/ponzi-suite
cd ponzi-suite
pixi run dev-install         # ponzi-core, ponzi-service, ponzi-visual beside the suite, each installed
```

It clones each of ponzi-core, ponzi-service and ponzi-visual that is not yet beside the suite (over https, the default branch; `PONZI_REF=TAG` for another), then installs the default environments of ponzi-core and ponzi-service and ponzi-visual's packages. A checkout that exists is used as it is, never pulled, reset or overwritten, and the installs follow its lock file (`pixi install --locked`), so running it again only checks and finishes.

More environments are named in `PONZI_ENVS`, or as arguments:

```
PONZI_ENVS="ml isce3" pixi run dev-install
pixi run dev-install ml      # the same, as arguments
```

Both commands run on Linux (x86-64) only, and stop at once on any other system. `ml-gpu` and `isce3` need an NVIDIA driver for CUDA 12.9; set `CONDA_OVERRIDE_CUDA=12.9` to install them anyway ([GPUs and CUDA](#gpus-and-cuda)). Then start the whole system with `pixi run dev-up` ([Quickstart](quickstart.md#development-on-your-own-home)).

## GPUs and CUDA

The two environments are tied to a platform of their own, `linux-64-cuda`: Linux on x86-64 with a CUDA 12.9 driver (pixi's virtual package `__cuda`). The others are on plain `linux-64`, so each environment is solved once.

`ml-gpu` and `isce3` use CUDA 12.9 and need an NVIDIA driver for it (575 or later); pixi refuses to install them on a machine without one. On such a machine (a CI runner, a laptop), `CONDA_OVERRIDE_CUDA=12.9` installs them anyway.

- **Why 12.9.** CUDA 13 dropped GPUs below compute capability 7.5, so the cluster's GTX 1080 Ti (6.1) and V100 (7.0) nodes would be lost.
- **Why conda-forge torch.** PyTorch's own CUDA 12.8 and 12.9 wheels dropped Pascal; conda-forge's CUDA 12.9 build has kernels from SM 5.0 up, so it runs on every GPU of the cluster.
- **Why pixi for ISCE3.** ISCE3 and its companions are published on conda-forge only. Its version and build are pinned (`isce3 ==0.25.22`, build `py312cuda129*_cuda`), and the lock files of ponzi-core and ponzi-service hold the same exact build.

To check that the GPU is seen:

```
pixi run -e ml-gpu python -c "import torch; print(torch.cuda.is_available())"
pixi run -e isce3 python -c "import isce3.cuda.core as c; print(c.get_device_count())"
```

## Without pixi

Each distribution also installs with pip from its folder (`packages/<name>` of its repository), but pip cannot find the PONZI distributions it depends on, which are not on PyPI: name them all in one command, at one ref of each repository (a tag or `main`). The computing distributions need the conda-forge stack for ISCE3 and are not supported this way.

| Distribution | Folder | Depends on | Extras |
| --- | --- | --- | --- |
| `ponzi-spec` | ponzi-core `packages/spec` | | |
| `ponzi` | ponzi-core `packages/core` | `ponzi-spec` | `tide` (torch), `grid` (shapely, pyproj) |
| `ponzi-pipeline` | ponzi-core `packages/pipeline` | `ponzi` | `asf`, `dem` |
| `ponzi-models` | ponzi-core `packages/models` | `ponzi-spec`, `ponzi[grid]`, `ponzi-pipeline` | `train` (torch, wandb) |
| `ponzi-client` | ponzi-service `packages/client` | `ponzi-spec` | |
| `ponzi-server` | ponzi-service `packages/server` | `ponzi-spec` | |
| `ponzi-worker` | ponzi-service `packages/worker` | all of the above but the server | |

## Checking an install

```
python -c "import ponzi_spec; print(ponzi_spec.__version__)"
ponzi-client --help
```
