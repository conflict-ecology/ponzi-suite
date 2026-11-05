# Install

Every distribution installs with pip from its repository. `<org>` is the GitHub owner of the repositories.

| Distribution | Install | Notes |
| --- | --- | --- |
| `ponzi-spec` | `pip install "ponzi-spec @ git+https://github.com/<org>/ponzi-core@<tag>#subdirectory=packages/spec"` | pydantic and PyYAML only |
| `ponzi` | `pip install "ponzi @ git+https://github.com/<org>/ponzi-core@<tag>#subdirectory=packages/core"` | add `[tide]` for the TiDE forecaster (torch), `[grid]` for geometry, `[stac]` for STAC Items of the stores (install `ponzi-spec` first: it is not on PyPI) |
| `ponzi-pipeline` | `pip install "ponzi-pipeline @ git+https://github.com/<org>/ponzi-core@<tag>#subdirectory=packages/pipeline"` | after `ponzi`; add `[asf]` for discovery and downloads, `[dem]` for DEMs; the coherence chain and the onboarding |
| `ponzi-models` | `pip install "ponzi-models @ git+https://github.com/<org>/ponzi-core@<tag>#subdirectory=packages/models"` | after `ponzi-spec`, `ponzi[grid]` and `ponzi-pipeline`; add `[train]` for the trainer (torch, wandb). Gives the command `ponzi-models` |

The other distributions follow the same form as they arrive (`packages/server`, `packages/worker`, `packages/client` in ponzi-service).

## Development environments

ponzi-core uses [pixi](https://pixi.sh) for its development environments:

| Environment | Holds | For |
| --- | --- | --- |
| `default` | the library, the tests, the geospatial stack; never torch | `pixi run test` |
| `ml` | default plus torch (CPU) | TiDE tests, CPU evaluation |
| `ml-gpu` | torch 2.6 with CUDA 12.4, wandb | GPU training |
| `isce3` | default plus ISCE3 0.25.22, CUDA 12.9 build, with s1reader, COMPASS, dem_stitcher, GDAL, asf_search from conda-forge | the ISCE3 coherence backend (`pixi run -e isce3 test-pipeline`) |

ISCE3 and its companions are published on conda-forge only, so the ISCE3 backend of `ponzi-pipeline` runs in the `isce3` environment; everything else installs with pip.

The `isce3` environment requires ISCE3's CUDA build at one version: `isce3 = { version = "==0.25.22", build = "py312cuda129*_cuda" }` with `cuda-version = "12.9.*"`, and the lock file holds the exact build (`py312cuda129h43e19af_0_cuda`), the same in ponzi-core and ponzi-service. CUDA 12.9, not 13: CUDA 13 dropped Pascal, and the cluster's `ayaya` nodes are GTX 1080 Ti, as for `ml-gpu`. The environment declares CUDA 12.9 as a system requirement, so it installs where an NVIDIA driver supports CUDA 12.9 (driver 575 or later). On a machine without one (a CI runner), set `CONDA_OVERRIDE_CUDA=12.9` to install it. To check that ISCE3 sees a GPU:

```
pixi run -e isce3 python -c "import isce3.cuda.core as c; print(c.get_device_count())"
```

## Checking an install

```
python -c "import ponzi_spec; print(ponzi_spec.__version__)"
```
