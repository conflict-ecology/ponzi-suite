# Install

Every distribution installs with pip from its repository, under the GitHub organisation `conflict-ecology`.

| Distribution | Install | Notes |
| --- | --- | --- |
| `ponzi-spec` | `pip install "ponzi-spec @ git+https://github.com/conflict-ecology/ponzi-core@<tag>#subdirectory=packages/spec"` | pydantic and PyYAML only |
| `ponzi` | `pip install "ponzi @ git+https://github.com/conflict-ecology/ponzi-core@<tag>#subdirectory=packages/core"` | after `ponzi-spec`, which it depends on (it is not on PyPI); add `[tide]` for the TiDE forecaster, the default (torch; not needed for other forecasters), `[grid]` for geometry |
| `ponzi-pipeline` | `pip install "ponzi-pipeline @ git+https://github.com/conflict-ecology/ponzi-core@<tag>#subdirectory=packages/pipeline"` | after `ponzi`; add `[asf]` for discovery and downloads, `[dem]` for DEMs; the coherence chain and the onboarding |
| `ponzi-models` | `pip install "ponzi-models @ git+https://github.com/conflict-ecology/ponzi-core@<tag>#subdirectory=packages/models"` | after `ponzi-spec`, `ponzi[grid]` and `ponzi-pipeline`; add `[train]` for the trainer (torch, wandb). Gives the command `ponzi-models` |

The service's distributions install the same way from ponzi-service (`packages/server`, `packages/worker`, `packages/client`). They are at 0.1.0 and not yet released.

## Development environments

ponzi-core uses [pixi](https://pixi.sh) for its development environments:

| Environment | Holds | For |
| --- | --- | --- |
| `default` | the library, the tests, the geospatial stack; never torch | `pixi run test` |
| `ml` | default plus torch (CPU) | TiDE tests, CPU evaluation |
| `ml-gpu` | default plus torch 2.14.1 from conda-forge in its CUDA 12.9 build, wandb | GPU training |
| `isce3` | default plus ISCE3 0.25.22, CUDA 12.9 build, with s1reader, COMPASS, dem_stitcher, GDAL, asf_search from conda-forge | the ISCE3 coherence backend (`pixi run -e isce3 test-pipeline`) |

Both GPU environments use CUDA 12.9 and need an NVIDIA driver for it (575 or later). `ml-gpu` takes torch from conda-forge, not PyPI: conda-forge's CUDA 12.9 build has kernels from SM 5.0 up, so it runs on every GPU of the cluster, the GTX 1080 Ti (SM 6.1) included, where PyTorch's own cu128 and cu129 wheels dropped Pascal. CUDA 13 would drop the 1080 Ti and the V100 (SM below 7.5).

ISCE3 and its companions are published on conda-forge only, so the ISCE3 backend of `ponzi-pipeline` runs in the `isce3` environment; everything else installs with pip.

The `isce3` environment requires ISCE3's CUDA build at one version: `isce3 = { version = "==0.25.22", build = "py312cuda129*_cuda" }` with `cuda-version = "12.9.*"`, and the lock file holds the exact build (`py312cuda129h43e19af_0_cuda`), the same in ponzi-core and ponzi-service. CUDA 12.9, not 13: CUDA 13 dropped Pascal, and the cluster's `ayaya` nodes are GTX 1080 Ti, as for `ml-gpu`. The environment declares CUDA 12.9 as a system requirement, so it installs where an NVIDIA driver supports CUDA 12.9 (driver 575 or later). On a machine without one (a CI runner), set `CONDA_OVERRIDE_CUDA=12.9` to install it. To check that ISCE3 sees a GPU:

```
pixi run -e isce3 python -c "import isce3.cuda.core as c; print(c.get_device_count())"
```

## Credentials

Downloads, weather and the server each need a login before anything runs: see [Authentication](authentication.md).

## Checking an install

```
python -c "import ponzi_spec; print(ponzi_spec.__version__)"
```
