# CR-087: no port reference kit, no port check

- **Requested by / date:** owner, 2026-11-05 (phase 0, the ISCE3 reference comparison, dropped: "no further steps"); written down 2026-11-12, after the change
- **Status:** implemented (2026-11-05, ponzi-core commit `1f8f7e8`, without a request at the time); recorded 2026-11-12

## Why
CR-036 added a kit to compare the ISCE3 port with repeat_ccd's chain on real SLCs, run once on the HPC (phase 0). The owner dropped phase 0 on 2026-11-05, and the old repositories stopped being referenced. The kit had no other use, and it carried a copy of repeat_ccd's code.

## What changed
- Deleted `packages/pipeline/reference/phase0/`: the kit's README, its sbatch files (`setup`, `pairs`, `check`), `pairs.csv`, `port_reference.py`, and the copy of repeat_ccd at `5250ac4` (`asf.py`, `auth.py`, `granules.py`, `isce3_coh.py`).
- Deleted `ponzi_pipeline.coherence.port_check` and the `ponzi-pipeline port-check` command, with `test_port_check.py`.
- Deleted ponzi-core's `test_retired.py` (the check that nothing imported the retired repositories) and `tests/data/statemachine_golden.py` (the script that made `statemachine_golden.npz` from the old repository's code). The `.npz` and its values stay.
- Kept from CR-036: `GeoGrid`, which `geocode` and `write_cog` still take.
- The same commit removed the other mentions of the old repositories from the code and the contracts.

## Do results change?
No. Nothing that computes was changed; the kit and the check only compared.

## Tests
The tests of the kit and of the port check went with them. The coherence chain keeps its own tests (`test_coherence_chain.py`).

## Version
Library: `ponzi-pipeline` major (a command removed). Standard: no change.
