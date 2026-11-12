# ponzi-models

Panels, training, calibration, the registry and standards: everything that makes the pieces a watched area runs.

- [Training panels](../method/panels.md): the pinned set of pixels models are trained and calibrated on (`ponzi_models.panels`).
- [Training and calibrating a model](new-model.md): from a training spec to a model in a standard (`ponzi_models.training`, `calibration`, `registry`).
- [Building a standard](standards.md): the lifecycle on the CPU (the rehearsal) and at scale, and how a standard reaches the server (`ponzi_models.standards`).
- [Standard versions](versions.md): a standard's and a spec's version and key, what a change means, and how the registry, the server and the outputs keep track of them.
- [Naming rules](naming.md): how specs, models and standards are named, and the spec folders.

`ponzi-models --help` lists its commands. Its [API reference](../reference/api/ponzi-models.md) is generated from its docstrings.
