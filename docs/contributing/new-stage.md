# Adding a stage

A stage is replaced or added without touching the worker or the server. Example: a second coherence backend.

1. **Write the change request.** What the stage reads and writes (Collections), its identity params (what changes the result), its request params, its resources, how it fans out.
2. **Choose or add the Collections.** Reuse an existing one when the output has the same meaning and format (a new coherence backend still writes `ponzi-coherence-pair`). A new Collection goes into `ponzi_spec.collections` with its asset roles, and into the change request.
3. **Write the spec.**

    ```python
    from pydantic import BaseModel, ConfigDict
    from ponzi_spec.stages import ResourceHint, StageSpec

    class SnapCoherenceParams(BaseModel):
        model_config = ConfigDict(extra="forbid")
        window: str = "17x3"
        polarisation: str = "VV"

    SPEC = StageSpec(
        name="coherence-snap",
        code=("ponzi-pipeline",),
        inputs={"scenes": "s1-slc", "orbits": "s1-orbit",
                "dem": "ponzi-dem", "pairs": "ponzi-pairs"},
        outputs={"coherence": "ponzi-coherence-pair"},
        identity_params=SnapCoherenceParams,
        resources=ResourceHint(cpus=8, memory_gb=48, walltime="04:00:00"),
        fan_out="per_pair",
    )
    ```

    `code` names the distributions whose code computes the outputs; their majors are part of the content id (CR-054).

4. **Implement `run`.** Read the input Items' assets, write the outputs under `workdir`, return the output Items, built with `make_item` and `PonziFields(content_id=SPEC.content_id(...), stage=SPEC.ref(), ...)`.
5. **Register the entry point** in the `pyproject.toml` of the distribution that holds the stage (today every stage is a thin adapter in ponzi-worker, `ponzi_worker.stages`):

    ```toml
    [project.entry-points."ponzi.stages"]
    coherence-snap = "ponzi_worker.stages.snap:SNAP_STAGE"
    ```

6. **Test.** Synthetic fixtures, no network. The outputs validate against the PONZI extension schema; the content id is stable; a second run with the same inputs and params gives the same content id.
7. **Backend-specific checks.** A coherence backend states its agreement with the primary backend on a reference burst (equal, or within a documented tolerance), and its assembled store passes `ponzi validate-store`.
8. **Document it** on this site (a page under the stage's area and a line in the [stages table](../method/stages.md)) and in the agent checklist if it changes how agents work.
9. **Use it.** `ponzi-models standard-workflow` (`ponzi_models.standards.workflow`) adds it to the steps it builds from a standard, and `STAGE_CODE` (`ponzi_models.standards.versions`) names its code's distributions for a standard's `requires`.
